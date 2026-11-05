"""
Kitaab Bank - Command-Line Backup Utility
Creates a live snapshot backup using SQLite Online Backup API with SHA-256 and integrity checks.
"""

import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app import create_app
from app.services import backup_service

def main():
    app = create_app()
    with app.app_context():
        print("Starting live database backup...")
        success, record, error = backup_service.create_database_backup(teacher_name='Desktop Backup Launcher')
        if success:
            print("=" * 65)
            print("[SUCCESS] LIVE DATABASE SNAPSHOT CREATED SUCCESSFULLY")
            print("=" * 65)
            print(f"  Filename:          {record['filename']}")
            print(f"  File Size:         {record['file_size_bytes']:,} bytes")
            print(f"  SHA-256 Digest:    {record['checksum_sha256']}")
            print(f"  Verification:      {record['verification_status']}")
            print(f"  Storage Location:  backups/{record['filename']}")
            print("=" * 65)
            sys.exit(0)
        else:
            print("=" * 65)
            print(f"[ERROR] Backup failed: {error}")
            print("=" * 65)
            sys.exit(1)

if __name__ == '__main__':
    main()
