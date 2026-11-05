"""
Settings Service: School Profile, System Settings & Teacher Account Security.
Handles updating school metadata, default system language, and secure teacher password rotations.
All mutations are recorded in the audit trail.
"""

from werkzeug.security import check_password_hash, generate_password_hash
from app.database import get_db, db_transaction
from app.services import activity_service

def get_system_settings():
    """
    Retrieve all system settings as a key-value dictionary.
    """
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT key, value, description, updated_at FROM system_settings;")
    rows = cur.fetchall()
    settings = {}
    for r in rows:
        settings[r['key']] = r['value']
    return settings

def update_school_profile(school_name, academic_year, default_language, updated_by_id=None, updated_by_name=None):
    """
    Update basic school administrative settings.
    Returns (success, error_message).
    """
    school_name = (school_name or '').strip()
    academic_year = (academic_year or '').strip()
    default_language = (default_language or '').strip()

    if not school_name:
        return False, "School name cannot be empty."
    if not academic_year:
        return False, "Academic year cannot be empty."
    if default_language not in ('en', 'ur', 'sd'):
        return False, "Invalid default language selected."

    db = get_db()
    try:
        with db_transaction(db):
            cur = db.cursor()
            cur.execute(
                "INSERT INTO system_settings (key, value, updated_at) VALUES ('school_name', ?, CURRENT_TIMESTAMP) "
                "ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = CURRENT_TIMESTAMP;",
                (school_name,)
            )
            cur.execute(
                "INSERT INTO system_settings (key, value, updated_at) VALUES ('academic_year', ?, CURRENT_TIMESTAMP) "
                "ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = CURRENT_TIMESTAMP;",
                (academic_year,)
            )
            cur.execute(
                "INSERT INTO system_settings (key, value, updated_at) VALUES ('default_language', ?, CURRENT_TIMESTAMP) "
                "ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = CURRENT_TIMESTAMP;",
                (default_language,)
            )

        activity_service.record_activity(
            action='settings_updated',
            entity_type='settings',
            entity_id=None,
            actor_type='teacher' if updated_by_id else 'system',
            actor_name=updated_by_name or 'Teacher',
            details=f"School profile updated: '{school_name}', Year: '{academic_year}', Default Lang: '{default_language}'."
        )
        return True, None
    except Exception as e:
        return False, f"Failed to update settings: {str(e)}"

def change_teacher_password(teacher_id, current_password, new_password, confirm_password, teacher_name=None):
    """
    Secure password rotation for teacher account.
    Returns (success, error_message).
    """
    if not current_password:
        return False, "Current password is required."
    if not new_password or not confirm_password:
        return False, "New password and confirmation are required."
    if new_password != confirm_password:
        return False, "New password and confirmation do not match."
    if len(new_password) < 8:
        return False, "New password must be at least 8 characters long."

    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT id, username, password_hash, full_name FROM teachers WHERE id = ?;", (teacher_id,))
    teacher = cur.fetchone()

    if not teacher:
        return False, "Teacher account not found."

    if not check_password_hash(teacher['password_hash'], current_password):
        return False, "Incorrect current password."

    new_hash = generate_password_hash(new_password)
    try:
        with db_transaction(db):
            db.execute(
                "UPDATE teachers SET password_hash = ? WHERE id = ?;",
                (new_hash, teacher_id)
            )

        activity_service.record_activity(
            action='password_changed',
            entity_type='teacher',
            entity_id=teacher_id,
            actor_type='teacher',
            actor_name=teacher_name or teacher['full_name'],
            details=f"Teacher '{teacher['username']}' updated their account password."
        )
        return True, None
    except Exception as e:
        return False, f"Password change error: {str(e)}"

def is_demo_mode_active():
    """Check if system is currently in exhibition demo mode."""
    try:
        settings = get_system_settings()
        return settings.get('is_demo_mode') == '1'
    except Exception:
        return False

def get_demo_pre_backup_id():
    """Retrieve the exact backup ID captured when demo mode was entered."""
    try:
        settings = get_system_settings()
        val = settings.get('demo_pre_backup_id')
        return int(val) if val and str(val).isdigit() else None
    except Exception:
        return None

def exit_demo_mode(teacher_id=None, teacher_name=None):
    """
    Safely exit demo mode and restore the EXACT pre-demo safety backup.
    Verifies checksum and integrity of restored database before declaring success.
    Returns (success, restored_filename, error_message).
    """
    from app.services import backup_service
    db = get_db()
    cur = db.cursor()

    # 1. Retrieve the exact recorded pre-demo backup ID (never an arbitrary latest backup)
    exact_id = get_demo_pre_backup_id()
    if exact_id:
        cur.execute(
            "SELECT * FROM backup_records WHERE id = ? AND verification_status = 'VALID';",
            (exact_id,)
        )
        bck = cur.fetchone()
    else:
        bck = None

    if not bck:
        return False, None, "No recorded pre-demo safety backup found with matching ID. Cannot safely restore real data."

    backup_id = bck['id']
    filename = bck['filename']
    expected_checksum = bck['checksum_sha256']

    # 2. Perform restoration with maintenance protection and rollback defense
    success, pre_restore, err = backup_service.restore_database_from_backup(
        backup_id,
        teacher_name=teacher_name,
        expected_checksum=expected_checksum
    )
    if not success:
        return False, None, f"Failed to restore pre-demo backup: {err}"

    # 3. Post-Restoration Hash & Integrity Verification
    live_db_path = backup_service.get_live_db_path()
    is_valid, verify_msg = backup_service.verify_backup_integrity(live_db_path)
    if not is_valid:
        return False, None, f"Restored database verification failed: {verify_msg}"

    # 4. Clear demo flags from system_settings
    db = get_db()
    with db_transaction(db):
        db.execute(
            "INSERT INTO system_settings (key, value, updated_at) VALUES ('is_demo_mode', '0', CURRENT_TIMESTAMP) "
            "ON CONFLICT(key) DO UPDATE SET value = '0', updated_at = CURRENT_TIMESTAMP;"
        )
        db.execute("DELETE FROM system_settings WHERE key = 'demo_pre_backup_id';")

    activity_service.record_activity(
        action='exhibition_demo_exited',
        entity_type='system',
        entity_id=backup_id,
        actor_type='teacher' if teacher_id else 'system',
        actor_name=teacher_name or 'Teacher',
        details=f"Exited Exhibition Demo Mode. Restored school database from exact pre-demo snapshot '{filename}' (ID: {backup_id})."
    )
    return True, filename, None
