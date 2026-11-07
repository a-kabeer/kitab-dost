"""
Backup Service: SQLite Hot Backup Engine (Consistent Live Snapshot) & Verification
Uses Python's native sqlite3.Connection.backup() API to produce consistent,
byte-for-byte snapshots without shutting down the server or disrupting readers.
Includes SHA-256 verification and automated PRAGMA integrity_check.
"""

import os
import sqlite3
import hashlib
from datetime import datetime
from pathlib import Path
from flask import current_app
from app.database import get_db
from app.services import activity_service

def get_backups_dir():
    """Retrieve absolute path to backups directory and ensure it exists."""
    try:
        if current_app and 'BACKUP_FOLDER' in current_app.config:
            bck_dir = Path(current_app.config['BACKUP_FOLDER'])
        else:
            project_root = Path(__file__).resolve().parent.parent.parent
            bck_dir = project_root / 'backups'
    except Exception:
        project_root = Path(__file__).resolve().parent.parent.parent
        bck_dir = project_root / 'backups'
    bck_dir.mkdir(parents=True, exist_ok=True)
    return bck_dir

def get_live_db_path():
    """Retrieve absolute path to active live SQLite database."""
    try:
        if current_app and 'DATABASE_PATH' in current_app.config:
            return str(current_app.config['DATABASE_PATH'])
        elif current_app and 'DATABASE' in current_app.config:
            return str(current_app.config['DATABASE'])
    except Exception:
        pass
    project_root = Path(__file__).resolve().parent.parent.parent
    return str(project_root / 'kitaab_bank.db')

def calculate_sha256(filepath):
    """Compute SHA-256 hex digest of a file on disk."""
    hasher = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()

# Required schema structure for strict backup validation
REQUIRED_SCHEMA = {
    'teachers': {'id', 'username', 'password_hash', 'full_name', 'email', 'role', 'is_active', 'created_at'},
    'books': {'id', 'book_code', 'title', 'subject', 'class_grade', 'language', 'condition_state', 'status'},
    'donations': {'id', 'donation_code', 'donor_name', 'title', 'subject', 'class_grade', 'status'},
    'requests': {'id', 'tracking_code', 'book_id', 'requester_name', 'status'},
    'handovers': {'id', 'handover_code', 'request_id', 'book_id', 'handed_over_by', 'status'},
    'activity_logs': {'id', 'action', 'entity_type', 'actor_name', 'created_at'},
    'system_settings': {'key', 'value'},
    'backup_records': {'id', 'filename', 'file_size_bytes', 'checksum_sha256', 'verification_status'}
}

def verify_backup_integrity(filepath, expected_checksum=None):
    """
    Validate backup file consistency using SHA-256 comparison,
    SQLite integrity_check, and strict schema & column verification.
    """
    filepath = Path(filepath)
    if not filepath.is_file():
        return False, f"File '{filepath}' not found on disk."

    if expected_checksum:
        try:
            actual_hash = calculate_sha256(filepath)
        except OSError as exc:
            return False, f"Unable to read backup checksum: {exc}"
        if actual_hash.lower() != expected_checksum.lower():
            return False, (
                f"SHA-256 hash mismatch! Catalog: {expected_checksum[:12]}..., "
                f"On-Disk: {actual_hash[:12]}... File corrupted or modified."
            )

    from contextlib import closing
    try:
        with closing(sqlite3.connect(str(filepath), timeout=10.0)) as conn:
            cur = conn.cursor()
            cur.execute("PRAGMA integrity_check;")
            integrity = cur.fetchone()
            if not integrity or integrity[0] != 'ok':
                return False, f"Integrity check failed: {integrity[0] if integrity else 'Unknown error'}"

            cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = {row[0] for row in cur.fetchall()}
            missing_tables = set(REQUIRED_SCHEMA) - tables
            if missing_tables:
                return False, f"Missing required backup tables: {sorted(missing_tables)}"

            for table_name, required_columns in REQUIRED_SCHEMA.items():
                cur.execute(f"PRAGMA table_info({table_name});")
                existing_columns = {row[1] for row in cur.fetchall()}
                missing_columns = required_columns - existing_columns
                if missing_columns:
                    return False, (
                        f"Table '{table_name}' is missing required columns: "
                        f"{sorted(missing_columns)}"
                    )

            cur.execute("SELECT COUNT(*) FROM system_settings;")
            if cur.fetchone()[0] == 0:
                return False, "Backup system_settings table is empty."

        return True, "VALID"
    except (sqlite3.Error, OSError, ValueError) as exc:
        return False, f"Corrupt or invalid SQLite database file: {exc}"

def create_database_backup(created_by_id=None, teacher_name=None):
    """
    Produce a live snapshot using SQLite's Online Backup API.
    Only a verified snapshot is catalogued as a successful backup.
    """
    from contextlib import closing

    dest_path = None
    catalogued = False
    try:
        bck_dir = get_backups_dir()
        now_dt = datetime.now()
        base_name = f"kitab_bank_backup_{now_dt.strftime('%Y%m%d_%H%M%S')}"
        filename = f"{base_name}.db"
        dest_path = bck_dir / filename
        counter = 1
        while dest_path.exists():
            filename = f"{base_name}_{counter}.db"
            dest_path = bck_dir / filename
            counter += 1

        live_db_path = get_live_db_path()

        # Open and close both SQLite handles deterministically, including errors.
        with closing(sqlite3.connect(live_db_path, timeout=10.0)) as src_conn:
            src_conn.execute("PRAGMA busy_timeout = 10000;")
            with closing(sqlite3.connect(str(dest_path), timeout=10.0)) as dest_conn:
                dest_conn.execute("PRAGMA busy_timeout = 10000;")
                src_conn.backup(dest_conn, pages=100, sleep=0.01)

        file_size_bytes = os.path.getsize(dest_path)
        checksum_sha256 = calculate_sha256(dest_path)

        is_valid, verify_msg = verify_backup_integrity(
            dest_path,
            expected_checksum=checksum_sha256
        )
        if not is_valid:
            dest_path.unlink(missing_ok=True)
            return False, None, f"Backup verification failed: {verify_msg}"

        db = get_db()
        cur = db.cursor()
        cur.execute(
            """
            INSERT INTO backup_records (
                filename, file_size_bytes, checksum_sha256, verification_status, created_by
            ) VALUES (?, ?, ?, 'VALID', ?);
            """,
            (filename, file_size_bytes, checksum_sha256, created_by_id)
        )
        db.commit()
        backup_id = cur.lastrowid
        catalogued = True

        try:
            activity_service.record_activity(
                action='backup_created',
                entity_type='backup',
                entity_id=backup_id,
                actor_type='teacher' if created_by_id else 'system',
                actor_name=teacher_name or 'System',
                details=(
                    f"Live snapshot '{filename}' created ({file_size_bytes} bytes, "
                    f"SHA-256: {checksum_sha256[:12]}...). Status: VALID."
                )
            )
        except Exception:
            # A valid snapshot must remain reported as successful even if the
            # secondary activity-log insert fails after cataloguing.
            import logging
            logging.getLogger(__name__).exception("Backup created but audit logging failed")

        record = {
            'id': backup_id,
            'filename': filename,
            'file_size_bytes': file_size_bytes,
            'checksum_sha256': checksum_sha256,
            'verification_status': 'VALID',
            'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        return True, record, None
    except Exception as exc:
        # Never leave an untracked or partial snapshot that looks restorable.
        if dest_path is not None and not catalogued:
            try:
                dest_path.unlink(missing_ok=True)
            except OSError:
                pass
        return False, None, f"Backup creation failed: {exc}"

def get_all_backups(limit=50):
    """Retrieve catalog of all backups with creator information."""
    db = get_db()
    cur = db.cursor()
    cur.execute(
        """
        SELECT b.*, t.full_name as creator_name
        FROM backup_records b
        LEFT JOIN teachers t ON b.created_by = t.id
        ORDER BY b.id DESC
        LIMIT ?;
        """,
        (limit,)
    )
    rows = cur.fetchall()
    return [dict(r) for r in rows]

def get_backup_by_id(backup_id):
    """Retrieve backup metadata by primary key ID."""
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT * FROM backup_records WHERE id = ? LIMIT 1;", (backup_id,))
    row = cur.fetchone()
    return dict(row) if row else None

def delete_backup(backup_id, teacher_id=None, teacher_name=None, force=False):
    """
    Delete a backup file and its catalog record.
    Safety Guard: Blocks deletion if this is the ONLY remaining verified backup snapshot,
    preventing the school from being left with zero recoverable backups.
    """
    record = get_backup_by_id(backup_id)
    if not record:
        return False, "Backup record not found."

    db = get_db()
    cur = db.cursor()

    # Safety Guard: Check if this backup is the active pre-demo safety backup while Demo Mode is active
    from app.services import settings_service
    if settings_service.is_demo_mode_active():
        active_pre_demo_id = settings_service.get_demo_pre_backup_id()
        if active_pre_demo_id and record['id'] == active_pre_demo_id:
            return False, "Data Safety Guard: Cannot delete the active pre-demo safety backup while Exhibition Demo Mode is active. Please exit demo mode first."

    cur.execute("SELECT COUNT(*) FROM backup_records WHERE verification_status = 'VALID';")
    valid_count = cur.fetchone()[0]

    if not force and record['verification_status'] == 'VALID' and valid_count <= 1:
        return False, "Data Safety Guard: Cannot delete the only remaining verified database backup. Please create a new backup before removing this snapshot."

    bck_dir = get_backups_dir()
    filepath = bck_dir / record['filename']

    try:
        if filepath.exists():
            filepath.unlink()

        cur.execute("DELETE FROM backup_records WHERE id = ?;", (backup_id,))
        db.commit()

        activity_service.record_activity(
            action='backup_deleted',
            entity_type='backup',
            entity_id=backup_id,
            actor_type='teacher' if teacher_id else 'system',
            actor_name=teacher_name or 'System',
            details=f"Backup snapshot '{record['filename']}' deleted by {teacher_name or 'System'}."
        )
        return True, None
    except Exception as e:
        return False, f"Failed to delete backup: {str(e)}"

def restore_database_from_backup(backup_id_or_filename, teacher_name=None, expected_checksum=None, drain_timeout=5.0):
    """
    Restore only a catalogued backup while the application is in maintenance mode.

    A verified pre-restore snapshot is retained until the target database has
    passed integrity and schema checks. Rollback occurs before maintenance is
    released. If rollback itself fails, a persistent maintenance marker is left
    behind and the restore marker remains for startup recovery.
    """
    from contextlib import closing
    from app.services import maintenance_service
    from app.services.maintenance_service import (
        maintenance_context,
        mark_restore_in_progress,
        clear_restore_in_progress
    )

    bck_dir = get_backups_dir().resolve()
    record = None

    # Resolve by catalog ID or exact catalogued filename. Never accept arbitrary
    # paths supplied by a caller, even when the caller is authenticated.
    if str(backup_id_or_filename).isdigit():
        record = get_backup_by_id(int(backup_id_or_filename))
    else:
        filename = str(backup_id_or_filename or '').strip()
        if not filename or Path(filename).name != filename or Path(filename).suffix.lower() != '.db':
            return False, None, "Invalid backup filename."
        db = get_db()
        cur = db.cursor()
        cur.execute("SELECT * FROM backup_records WHERE filename = ? LIMIT 1;", (filename,))
        row = cur.fetchone()
        record = dict(row) if row else None

    if not record:
        return False, None, "Backup record not found in catalog."

    filename = record.get('filename') or ''
    if not filename or Path(filename).name != filename or Path(filename).suffix.lower() != '.db':
        return False, None, "Catalog contains an invalid backup filename."

    backup_path = (bck_dir / filename).resolve()
    if backup_path.parent != bck_dir or not backup_path.is_file():
        return False, None, "Catalogued backup file is missing or resolves outside the backup directory."

    expected_hash = expected_checksum or record.get('checksum_sha256')
    if not expected_hash:
        return False, None, "Backup has no recorded SHA-256 checksum and cannot be restored safely."

    is_valid, msg = verify_backup_integrity(backup_path, expected_checksum=expected_hash)
    if not is_valid:
        return False, None, f"Target backup rejected: {msg}"

    live_db_path = Path(get_live_db_path()).resolve()
    if backup_path == live_db_path:
        return False, None, "The live database cannot be used as its own restore source."

    pre_restore_filename = f"pre_restore_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.db"
    pre_restore_path = bck_dir / pre_restore_filename
    recovery_required = False
    restore_error = None

    try:
        with maintenance_context(timeout=drain_timeout):
            # 1. Capture a consistent rollback snapshot while all live DB users
            # are drained and before any restore marker or target mutation.
            with closing(sqlite3.connect(str(live_db_path), timeout=10.0)) as live_conn:
                live_conn.execute("PRAGMA busy_timeout = 10000;")
                live_conn.execute("PRAGMA wal_checkpoint(TRUNCATE);")

                cur = live_conn.cursor()
                cur.execute(
                    """
                    SELECT id, filename, file_size_bytes, checksum_sha256,
                           verification_status, created_by, created_at
                    FROM backup_records;
                    """
                )
                existing_backup_rows = [tuple(row) for row in cur.fetchall()]

                with closing(sqlite3.connect(str(pre_restore_path), timeout=10.0)) as pre_conn:
                    live_conn.backup(pre_conn)

            pre_valid, pre_message = verify_backup_integrity(pre_restore_path)
            if not pre_valid:
                raise RuntimeError(f"Pre-restore rollback snapshot failed verification: {pre_message}")

            # 2. Persist recovery marker before replacing live database pages.
            mark_restore_in_progress(pre_restore_path, target_backup=filename)

            try:
                # 3. Restore target and merge the backup catalog from the current
                # live DB so newer restore points remain discoverable.
                with closing(sqlite3.connect(str(backup_path), timeout=10.0)) as target_conn:
                    with closing(sqlite3.connect(str(live_db_path), timeout=10.0)) as dest_conn:
                        dest_conn.execute("PRAGMA busy_timeout = 10000;")
                        target_conn.backup(dest_conn)

                        if existing_backup_rows:
                            for row in existing_backup_rows:
                                dest_conn.execute(
                                    """
                                    INSERT INTO backup_records (
                                        id, filename, file_size_bytes, checksum_sha256,
                                        verification_status, created_by, created_at
                                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                                    ON CONFLICT(id) DO NOTHING;
                                    """,
                                    row
                                )
                            dest_conn.commit()

                        dest_conn.execute("PRAGMA wal_checkpoint(TRUNCATE);")

                target_valid, target_message = verify_backup_integrity(live_db_path)
                if not target_valid:
                    raise RuntimeError(f"Restored database failed verification: {target_message}")

                clear_restore_in_progress()
                return True, pre_restore_filename, None

            except Exception as exc:
                restore_error = str(exc)
                # Roll back before maintenance_context releases the request gate.
                try:
                    with closing(sqlite3.connect(str(pre_restore_path), timeout=10.0)) as rb_src:
                        with closing(sqlite3.connect(str(live_db_path), timeout=10.0)) as rb_dest:
                            rb_src.backup(rb_dest)
                            rb_dest.execute("PRAGMA wal_checkpoint(TRUNCATE);")

                    rollback_valid, rollback_message = verify_backup_integrity(live_db_path)
                    if not rollback_valid:
                        raise RuntimeError(f"Rollback snapshot did not verify: {rollback_message}")

                    clear_restore_in_progress()
                    return False, pre_restore_filename, (
                        f"Restore failed and the original database was safely restored: {restore_error}"
                    )
                except Exception as rollback_exc:
                    recovery_required = True
                    raise RuntimeError(
                        f"Restore failed ({restore_error}); automatic rollback also failed "
                        f"({rollback_exc}). Keep the server stopped. The restore marker and "
                        f"rollback snapshot were retained for startup recovery."
                    ) from rollback_exc

    except TimeoutError as exc:
        return False, None, str(exc)
    except Exception as exc:
        if recovery_required:
            # maintenance_context releases its own gate on exit. Re-establish a
            # persistent gate so this process cannot serve against uncertain data.
            try:
                maintenance_service.set_maintenance_mode(True)
            except Exception:
                pass
            return False, pre_restore_filename, str(exc)
        return False, pre_restore_filename if pre_restore_path.exists() else None, (
            f"Restoration failed: {exc}. The previous database was retained or restored."
        )
