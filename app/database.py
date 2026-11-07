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
    """Recover an interrupted restore before the application serves requests.

    Returns False on any recovery uncertainty so startup can fail closed rather
    than serving a potentially half-restored SQLite database.
    """
    try:
        from app.services import maintenance_service
        info = maintenance_service.get_interrupted_restore_info()
        if not info:
            return True

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

        # Marker removal is part of successful recovery; failure must stop startup.
        maintenance_service.clear_restore_in_progress()
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

    # 0. Crash Resilience: Check and recover from any previously interrupted restore
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
                cur.execute("DROP TABLE IF EXISTS handovers;")
                db.commit()

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
            pwd_hash = generate_password_hash("Teacher@123")
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
