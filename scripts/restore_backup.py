"""
Kitaab Bank - Safe Database Restoration CLI Tool
Usage:
    python scripts/restore_backup.py --latest
    python scripts/restore_backup.py --file kitab_bank_backup_20261105_120000.db
    python scripts/restore_backup.py --list
"""

import sys
import os
import argparse
import sqlite3
from pathlib import Path
from datetime import datetime

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BACKUPS_DIR = PROJECT_ROOT / 'backups'
LIVE_DB_PATH = PROJECT_ROOT / 'kitaab_bank.db'

def list_backups():
    """Display available backups in backups/ directory."""
    if not BACKUPS_DIR.exists():
        print("No backups directory found.")
        return []

    backups = sorted(BACKUPS_DIR.glob("kitab_bank_backup_*.db"), reverse=True)
    if not backups:
        print("No backup files found in backups/")
        return []

    print("\n" + "=" * 70)
    print("AVAILABLE KITAAB BANK BACKUPS")
    print("=" * 70)
    for i, b in enumerate(backups, 1):
        size_kb = b.stat().st_size / 1024
        mod_time = datetime.fromtimestamp(b.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{i}] {b.name}  ({size_kb:.1f} KB) - {mod_time}")
    print("=" * 70 + "\n")
    return backups

def restore_backup(backup_path):
    """Safely restore database from verified backup file."""
    backup_path = Path(backup_path)
    if not backup_path.exists():
        print(f"ERROR: Backup file '{backup_path}' does not exist.")
        return False

    print(f"Restoring from: {backup_path.name}")

    # 1. Integrity Check on Target Backup
    print("Step 1/4: Checking backup file integrity...")
    try:
        conn = sqlite3.connect(backup_path)
        cur = conn.cursor()
        cur.execute("PRAGMA integrity_check;")
        res = cur.fetchone()
        conn.close()
        if not res or res[0] != 'ok':
            print(f"ERROR: Backup integrity check failed: {res}")
            return False
        print("✓ Backup integrity check PASSED (ok).")
    except Exception as e:
        print(f"ERROR: Could not verify backup file: {e}")
        return False

    # 2. Pre-Restore Safety Snapshot of Live Database
    BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
    pre_restore_file = BACKUPS_DIR / f"pre_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    print(f"Step 2/4: Creating pre-restore rollback snapshot ({pre_restore_file.name})...")
    if LIVE_DB_PATH.exists():
        try:
            live_conn = sqlite3.connect(LIVE_DB_PATH)
            safety_conn = sqlite3.connect(pre_restore_file)
            live_conn.backup(safety_conn)
            safety_conn.close()
            live_conn.close()
            print("✓ Pre-restore rollback safety snapshot created.")
        except Exception as e:
            print(f"WARNING: Pre-restore snapshot failed: {e}")
    else:
        print("Live database did not exist yet; skipping pre-restore copy.")

    # 3. Perform Live Restoration
    print("Step 3/4: Restoring database content...")
    try:
        src_conn = sqlite3.connect(backup_path)
        dest_conn = sqlite3.connect(LIVE_DB_PATH)
        src_conn.backup(dest_conn)
        dest_conn.close()
        src_conn.close()
        print("✓ Database restoration completed.")
    except Exception as e:
        print(f"ERROR: Restoration failed: {e}")
        return False

    # 4. Post-Restore Verification
    print("Step 4/4: Verifying restored live database...")
    try:
        check_conn = sqlite3.connect(LIVE_DB_PATH)
        cur = check_conn.cursor()
        cur.execute("PRAGMA integrity_check;")
        res = cur.fetchone()
        cur.execute("SELECT COUNT(*) FROM books;")
        books_count = cur.fetchone()[0]
        check_conn.close()

        if res and res[0] == 'ok':
            print(f"✓ Restored database verified! (Integrity: ok, Books cataloged: {books_count})")
            print("\n🎉 RESTORATION COMPLETED SUCCESSFULLY!\n")
            return True
        else:
            print(f"ERROR: Post-restore verification failed: {res}")
            return False
    except Exception as e:
        print(f"ERROR: Post-restore check failed: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Kitaab Bank Database Safe Restoration Tool")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--latest', action='store_true', help="Restore the most recent backup")
    group.add_argument('--file', type=str, help="Specific backup file name in backups/")
    group.add_argument('--list', action='store_true', help="List available backups")

    args = parser.parse_args()

    if args.list:
        list_backups()
        return 0

    if args.latest:
        backups = sorted(BACKUPS_DIR.glob("kitab_bank_backup_*.db"), reverse=True)
        if not backups:
            print("ERROR: No backups found in backups/ to restore.")
            return 1
        target_file = backups[0]
    else:
        target_file = BACKUPS_DIR / args.file
        if not target_file.exists():
            # Try direct path
            target_file = Path(args.file)

    success = restore_backup(target_file)
    return 0 if success else 1

if __name__ == '__main__':
    sys.exit(main())
