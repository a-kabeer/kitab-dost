import os
import sqlite3
import time
from contextlib import closing
from pathlib import Path
from contextlib import contextmanager
from flask import g, current_app

def get_db():
    """Get or create SQLite connection for the current application context."""
    if 'db' not in g:
        db_path = current_app.config['DATABASE_PATH']
        timeout = current_app.config.get('SQLITE_TIMEOUT', 5.0)

        conn = sqlite3.connect(
            str(db_path),
            timeout=timeout
        )
        conn.row_factory = sqlite3.Row

        # Execute performance, concurrency and data safety pragmas
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON;")
        cursor.execute("PRAGMA journal_mode = WAL;")
        cursor.execute("PRAGMA busy_timeout = 5000;")
        cursor.execute("PRAGMA synchronous = NORMAL;")
        cursor.close()

        g.db = conn
        try:
            from app.services import maintenance_service
            maintenance_service.register_db_connection()
        except Exception:
            pass

    return g.db

def close_db(e=None):
    """Close the current request's SQLite connection if open."""
    db = g.pop('db', None)
    if db is not None:
        db.close()
    try:
        from app.services import maintenance_service
        maintenance_service.unregister_db_connection()
    except Exception:
        pass

def check_and_recover_interrupted_restore(app):
    """Recover an interrupted restore only after its owner has exited.

    A cross-process OS lock serializes recovery between simultaneous application
    startups. Unknown owner state always fails closed; the live database is never
    overwritten while a restore process may still be running.
    """
    try:
        from app.services import maintenance_service

        def owner_has_exited(pid, context):
            if not isinstance(pid, int) or isinstance(pid, bool) or pid <= 0:
                app.logger.critical("%s has no valid owner PID; startup is blocked.", context)
                return False
            try:
                if maintenance_service.is_process_running(pid):
                    app.logger.critical(
                        "%s is still owned by live process %s; startup recovery is blocked.",
                        context,
                        pid
                    )
                    return False
                return True
            except Exception:
                app.logger.exception(
                    "Could not establish whether %s owner PID %s is still alive; startup is blocked.",
                    context,
                    pid
                )
                return False

        info = maintenance_service.get_interrupted_restore_info()
        lock_info = maintenance_service.read_maintenance_lock_info()

        if not info and not lock_info:
            return True

        # A maintenance gate without a restore marker means the process crashed
        # before live-database mutation began (for example while draining or
        # creating the rollback snapshot). It may be cleared only after proving
        # its recorded owner has exited.
        if not info:
            with maintenance_service.restore_recovery_context():
                refreshed_lock = maintenance_service.read_maintenance_lock_info()
                if not refreshed_lock:
                    return True
                if not owner_has_exited(refreshed_lock.get("pid"), "Maintenance gate"):
                    return False
                if not maintenance_service.clear_stale_maintenance_lock(refreshed_lock["payload"]):
                    app.logger.critical(
                        "Maintenance gate changed during stale-lock cleanup; startup is blocked."
                    )
                    return False
                app.logger.warning("Removed stale maintenance gate left before restore mutation.")
                return True

        marker_pid = info.get("pid")
        if marker_pid is None and lock_info:
            # Older marker files did not persist a PID; the gate is the fallback
            # source of ownership metadata.
            marker_pid = lock_info.get("pid")

        if lock_info and marker_pid != lock_info.get("pid"):
            app.logger.critical(
                "Restore marker owner and maintenance gate owner disagree; startup is blocked."
            )
            return False

        if not owner_has_exited(marker_pid, "Interrupted restore"):
            return False

        # The kernel releases this lock automatically if a recovery process
        # crashes. A second startup cannot restore/verify/clear markers in
        # parallel and then accidentally serve while the other is still copying.
        with maintenance_service.restore_recovery_context():
            info = maintenance_service.get_interrupted_restore_info()
            lock_info = maintenance_service.read_maintenance_lock_info()

            # Another startup may have completed recovery while this process
            # waited for the recovery lock.
            if not info:
                if lock_info:
                    if not owner_has_exited(lock_info.get("pid"), "Maintenance gate"):
                        return False
                    if not maintenance_service.clear_stale_maintenance_lock(lock_info["payload"]):
                        app.logger.critical(
                            "Maintenance gate changed while another startup completed recovery."
                        )
                        return False
                return True

            marker_pid = info.get("pid")
            if marker_pid is None and lock_info:
                marker_pid = lock_info.get("pid")
            if lock_info and marker_pid != lock_info.get("pid"):
                app.logger.critical(
                    "Restore marker owner and maintenance gate owner changed during recovery; startup is blocked."
                )
                return False
            if not owner_has_exited(marker_pid, "Interrupted restore"):
                return False

            rollback_path = info.get("rollback_snapshot")
            if not rollback_path or not os.path.isfile(rollback_path):
                app.logger.critical(
                    "Interrupted database restore marker exists, but its rollback snapshot is missing: %s",
                    rollback_path
                )
                return False

            app.logger.warning(
                "Interrupted database restoration detected. Recovering live database from rollback snapshot: %s",
                rollback_path
            )

            db_path = app.config['DATABASE_PATH']
            with closing(sqlite3.connect(str(rollback_path), timeout=10.0)) as src_conn:
                integrity = src_conn.execute("PRAGMA integrity_check;").fetchone()
                if not integrity or integrity[0] != 'ok':
                    app.logger.critical("Rollback snapshot failed integrity_check: %s", integrity)
                    return False

                with closing(sqlite3.connect(str(db_path), timeout=10.0)) as dest_conn:
                    src_conn.backup(dest_conn)
                    dest_conn.execute("PRAGMA wal_checkpoint(TRUNCATE);")

            with closing(sqlite3.connect(str(db_path), timeout=10.0)) as check_conn:
                result = check_conn.execute("PRAGMA integrity_check;").fetchone()

            if not result or result[0] != 'ok':
                app.logger.critical("Rollback recovery integrity check failed: %s", result)
                return False

            # Remove markers only after the recovered database has been verified.
            maintenance_service.clear_restore_in_progress()
            if lock_info and not maintenance_service.clear_stale_maintenance_lock(lock_info["payload"]):
                app.logger.critical(
                    "Database was recovered, but the maintenance gate changed before cleanup; startup remains blocked."
                )
                return False

            app.logger.info("Interrupted restore recovery completed successfully.")
            return True
    except Exception:
        app.logger.exception("Failed to recover interrupted database restoration.")
        return False

def init_db(app):
    """Initialize the SQLite database schema, enforce WAL mode, and seed default teacher."""
    db_path = app.config['DATABASE_PATH']
    # Ensure parent directory exists
    db_path.parent.mkdir(parents=True, exist_ok=True)

    # 0. Crash Resilience: Check and recover using this app's configured database paths.
    # The app context is required because maintenance markers live beside DATABASE_PATH.
    with app.app_context():
        if not check_and_recover_interrupted_restore(app):
            raise RuntimeError('Interrupted database restore could not be recovered. Application startup aborted to protect school data.')

    with app.app_context():
        db = get_db()
        cur = db.cursor()

        # Check existing handovers table before schema execution to prevent index error on older schema
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='handovers';")
        if cur.fetchone():
            cur.execute("PRAGMA table_info(handovers);")
            handover_cols = [r[1] for r in cur.fetchall()]
            if 'handover_code' not in handover_cols:
                # Never destroy legacy circulation history during a schema upgrade.
                # Preserve the old table under a deterministic, collision-safe name;
                # the current schema.sql will then create the new handovers table.
                legacy_name = 'handovers_legacy'
                suffix = 1
                while True:
                    cur.execute(
                        "SELECT 1 FROM sqlite_master WHERE type='table' AND name = ?;",
                        (legacy_name,)
                    )
                    if not cur.fetchone():
                        break
                    legacy_name = f'handovers_legacy_{suffix}'
                    suffix += 1
                cur.execute(f'ALTER TABLE handovers RENAME TO "{legacy_name}";')
                db.commit()
                app.logger.warning(
                    "Archived legacy handovers table as %s to preserve historical records. "
                    "Review and migrate these rows before removing the archive.",
                    legacy_name
                )

        with current_app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

        # Ensure author column exists in donations table (schema migration)
        cur.execute("PRAGMA table_info(donations);")
        donation_cols = [r[1] for r in cur.fetchall()]
        if 'author' not in donation_cols:
            cur.execute("ALTER TABLE donations ADD COLUMN author TEXT;")
            db.commit()

        # Seed initial teacher account if none exists
        cur = db.cursor()
        cur.execute("SELECT COUNT(*) FROM teachers;")
        if cur.fetchone()[0] == 0:
            from werkzeug.security import generate_password_hash
            pwd_hash = generate_password_hash(current_app.config.get('INITIAL_TEACHER_PASSWORD', 'Teacher@123'))
            cur.execute(
                "INSERT INTO teachers (username, password_hash, full_name, email, role, is_active) "
                "VALUES (?, ?, ?, ?, ?, 1);",
                ('teacher', pwd_hash, 'School Teacher / Incharge', 'teacher@school.edu.pk', 'admin')
            )
            db.commit()

        # Verify WAL mode
        cur.execute("PRAGMA journal_mode;")
        mode = cur.fetchone()[0]
        cur.close()

        app.logger.info(f"Database initialized at {db_path} with journal_mode: {mode}")

@contextmanager
def db_transaction(db=None, max_retries=3, initial_delay=0.1):
    """
    Context manager for short, safe write transactions.
    Uses 'BEGIN IMMEDIATE' to acquire write lock up front, preventing deadlocks.
    Includes exponential backoff retry for transient SQLite lock contention.
    """
    if db is None:
        db = get_db()

    if max_retries < 1:
        raise ValueError("max_retries must be at least 1")

    delay = initial_delay
    # Retry only acquiring the write lock. Once the caller's block has run,
    # it must never be replayed: it may contain non-repeatable side effects.
    for attempt in range(1, max_retries + 1):
        try:
            db.execute("BEGIN IMMEDIATE")
            break
        except sqlite3.OperationalError as exc:
            if "database is locked" not in str(exc).lower() or attempt >= max_retries:
                raise
            time.sleep(delay)
            delay *= 2

    try:
        yield db
        db.commit()
    except Exception:
        if db.in_transaction:
            db.rollback()
        raise
