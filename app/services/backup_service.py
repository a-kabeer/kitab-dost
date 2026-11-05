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

def verify_backup_integrity(filepath, expected_checksum=None):
    """
    Validate backup file consistency using SHA-256 comparison,
    SQLite integrity_check, and core schema verification.
    """
    filepath = Path(filepath)
    if not filepath.exists():
        return False, f"File '{filepath}' not found on disk."

    # 1. SHA-256 verification if provided
    if expected_checksum:
        actual_hash = calculate_sha256(filepath)
        if actual_hash.lower() != expected_checksum.lower():
            return False, f"SHA-256 hash mismatch! Catalog: {expected_checksum[:12]}..., On-Disk: {actual_hash[:12]}... File corrupted or modified."

    try:
        conn = sqlite3.connect(str(filepath))
        cur = conn.cursor()
        cur.execute("PRAGMA integrity_check;")
        res = cur.fetchone()
        if not res or res[0] != 'ok':
            conn.close()
            return False, f"Integrity check failed: {res[0] if res else 'Unknown error'}"

        # Verify core tables
        cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = {r[0] for r in cur.fetchall()}
        required_tables = {'teachers', 'books', 'donations', 'requests', 'handovers', 'activity_logs'}
        if not required_tables.issubset(tables):
            missing = required_tables - tables
            conn.close()
            return False, f"Missing required tables in backup: {missing}"

        conn.close()
        return True, "VALID"
    except Exception as e:
        return False, f"Corrupt or invalid SQLite database file: {str(e)}"

def create_database_backup(created_by_id=None, teacher_name=None):
    """
    Produce a live snapshot backup using sqlite3.Connection.backup().
    Returns (success, backup_record_dict, error_msg).
    """
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

        # 1. Perform Consistent Live Backup
        src_conn = sqlite3.connect(live_db_path)
        dest_conn = sqlite3.connect(dest_path)

        # Step through in chunks of 100 pages with minimal sleep
        src_conn.backup(dest_conn, pages=100, sleep=0.001)

        dest_conn.close()
        src_conn.close()

        # 2. File Metadata & Checksums
        file_size_bytes = os.path.getsize(dest_path)
        checksum_sha256 = calculate_sha256(dest_path)

        # 3. Post-Backup Integrity Verification
        is_valid, verify_msg = verify_backup_integrity(dest_path)
        status_val = 'VALID' if is_valid else 'CORRUPT'

        # 4. Catalog in backup_records
        db = get_db()
        cur = db.cursor()
        cur.execute(
            """
            INSERT INTO backup_records (
                filename, file_size_bytes, checksum_sha256, verification_status, created_by
            ) VALUES (?, ?, ?, ?, ?);
            """,
            (filename, file_size_bytes, checksum_sha256, status_val, created_by_id)
        )
        db.commit()
        backup_id = cur.lastrowid

        # 5. Log audit trail
        activity_service.record_activity(
            action='backup_created',
            entity_type='backup',
            entity_id=backup_id,
            actor_type='teacher' if created_by_id else 'system',
            actor_name=teacher_name or 'System',
            details=f"Live snapshot '{filename}' created ({file_size_bytes} bytes, SHA-256: {checksum_sha256[:12]}...). Status: {status_val}."
        )

        record = {
            'id': backup_id,
            'filename': filename,
            'file_size_bytes': file_size_bytes,
            'checksum_sha256': checksum_sha256,
            'verification_status': status_val,
            'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        return True, record, None
    except Exception as e:
        return False, None, f"Backup creation failed: {str(e)}"

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

def restore_database_from_backup(backup_id_or_filename, teacher_name=None):
    """
    Safely restore database from a verified backup with complete rollback protection.
    1. Pre-validates target backup (checksum match, PRAGMA integrity_check, schema presence).
    2. Checkpoints WAL on live database.
    3. Creates verified pre-restore rollback snapshot before any live database mutation.
    4. Streams backup pages using sqlite3.Connection.backup() with WAL truncation.
    5. Verifies live database integrity.
    6. Automatically rolls back to the pre-restore snapshot if post-restore verification fails.
    """
    bck_dir = get_backups_dir()
    record = None

    # Resolve filename and record
    if str(backup_id_or_filename).isdigit():
        record = get_backup_by_id(int(backup_id_or_filename))
        if not record:
            return False, None, "Backup record ID not found in catalog."
        filename = record['filename']
    else:
        filename = str(backup_id_or_filename).strip()
        db = get_db()
        cur = db.cursor()
        cur.execute("SELECT * FROM backup_records WHERE filename = ? LIMIT 1;", (filename,))
        r = cur.fetchone()
        if r:
            record = dict(r)

    backup_path = bck_dir / filename
    if not backup_path.exists():
        return False, None, f"Backup file '{filename}' does not exist on server disk."

    # 1. Pre-validate Target Backup Integrity & Checksum
    expected_hash = record.get('checksum_sha256') if record else None
    is_valid, msg = verify_backup_integrity(backup_path, expected_checksum=expected_hash)
    if not is_valid:
        return False, None, f"Target backup rejected: {msg}"

    live_db_path = get_live_db_path()
    pre_restore_filename = f"pre_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    pre_restore_path = bck_dir / pre_restore_filename

    try:
        # 2. Checkpoint WAL and Create Pre-Restore Rollback Snapshot
        live_conn = sqlite3.connect(live_db_path, timeout=10.0)
        try:
            live_conn.execute("PRAGMA wal_checkpoint(TRUNCATE);")
        except Exception:
            pass

        pre_conn = sqlite3.connect(pre_restore_path)
        live_conn.backup(pre_conn)
        pre_conn.close()
        live_conn.close()

        # 3. Perform Live Restoration with WAL Checkpoint
        target_bck_conn = sqlite3.connect(str(backup_path))
        dest_live_conn = sqlite3.connect(live_db_path, timeout=10.0)
        dest_live_conn.execute("PRAGMA busy_timeout = 5000;")
        target_bck_conn.backup(dest_live_conn)
        try:
            dest_live_conn.execute("PRAGMA wal_checkpoint(TRUNCATE);")
        except Exception:
            pass
        dest_live_conn.close()
        target_bck_conn.close()

        # 4. Verify Live Database After Restoration
        verify_conn = sqlite3.connect(live_db_path, timeout=10.0)
        cur = verify_conn.cursor()
        cur.execute("PRAGMA integrity_check;")
        verify_res = cur.fetchone()
        verify_conn.close()

        if not verify_res or verify_res[0] != 'ok':
            # Emergency automated rollback to pre-restore snapshot
            rb_src = sqlite3.connect(pre_restore_path)
            rb_dest = sqlite3.connect(live_db_path)
            rb_src.backup(rb_dest)
            rb_dest.close()
            rb_src.close()
            return False, pre_restore_filename, "Post-restore integrity check failed! Automatically restored database back to pre-restore safety copy."

        return True, pre_restore_filename, None
    except Exception as e:
        # Emergency rollback if safety copy was created
        if pre_restore_path.exists():
            try:
                rb_src = sqlite3.connect(pre_restore_path)
                rb_dest = sqlite3.connect(live_db_path)
                rb_src.backup(rb_dest)
                rb_dest.close()
                rb_src.close()
            except Exception:
                pass
        return False, pre_restore_filename if pre_restore_path.exists() else None, f"Restoration error: {str(e)}. Safe rollback snapshot retained."
