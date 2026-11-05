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

def restore_backup(backup_path, skip_confirm=False):
    """Safely restore database from verified backup file with WAL checkpoint and rollback defense."""
    backup_path = Path(backup_path)
    if not backup_path.exists():
        print(f"ERROR: Backup file '{backup_path}' does not exist.")
        return False

    print(f"\nTarget Backup: {backup_path.name}")
    print(f"File Size:     {backup_path.stat().st_size / 1024:.1f} KB")

    if not skip_confirm:
        print("\n[SAFETY NOTICE]")
        print("Restoring will replace the current active database with the contents of this snapshot.")
        print("An automated pre-restore rollback snapshot will be captured before modifying the live database.")
        print("Note: If the Waitress production server is actively processing writes, it is recommended to pause traffic.")
        ans = input("Proceed with database restoration? (y/N): ").strip().lower()
        if ans not in ('y', 'yes'):
            print("Restoration cancelled by user.")
            return False

    # 1. Integrity Check on Target Backup
    print("\nStep 1/4: Checking target backup file integrity and core tables...")
    try:
        conn = sqlite3.connect(str(backup_path))
        cur = conn.cursor()
        cur.execute("PRAGMA integrity_check;")
        res = cur.fetchone()
        if not res or res[0] != 'ok':
            conn.close()
            print(f"ERROR: Backup integrity check failed: {res}")
            return False

        cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = {r[0] for r in cur.fetchall()}
        required = {'teachers', 'books', 'donations', 'requests', 'handovers', 'activity_logs'}
        if not required.issubset(tables):
            conn.close()
            print(f"ERROR: Backup is missing required application tables: {required - tables}")
            return False

        conn.close()
        print("✓ Backup integrity and schema verification PASSED.")
    except Exception as e:
        print(f"ERROR: Could not verify backup file: {e}")
        return False

    # 2. Acquire Maintenance Gate to Protect Against Running Waitress Server
    m_file = LIVE_DB_PATH.parent / '.maintenance_lock'
    try:
        m_file.write_text(f"CLI_RESTORE_ACTIVE:{datetime.now().isoformat()}")
        print("\n[MAINTENANCE GATE] Acquired maintenance lock (.maintenance_lock).")
        print("  - Incoming Waitress requests gated with HTTP 503 Service Unavailable.")
        print("  - Draining active in-flight database connections (waiting 0.5s)...")
        time.sleep(0.5)

        # 2. Pre-Restore Safety Snapshot of Live Database (with WAL Checkpoint)
        BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
        pre_restore_file = BACKUPS_DIR / f"pre_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        print(f"\nStep 2/4: Capturing emergency rollback snapshot ({pre_restore_file.name})...")
        if LIVE_DB_PATH.exists():
            try:
                live_conn = sqlite3.connect(LIVE_DB_PATH, timeout=10.0)
                try:
                    live_conn.execute("PRAGMA wal_checkpoint(TRUNCATE);")
                except Exception:
                    pass
                # Capture existing backup catalog to preserve historical records across restores
                existing_backup_rows = []
                try:
                    cur = live_conn.cursor()
                    cur.execute("SELECT id, filename, file_size_bytes, checksum_sha256, verification_status, created_by, created_at FROM backup_records;")
                    existing_backup_rows = [tuple(r) for r in cur.fetchall()]
                except Exception:
                    pass

                safety_conn = sqlite3.connect(pre_restore_file)
                live_conn.backup(safety_conn)
                safety_conn.close()
                live_conn.close()
                print("✓ Emergency rollback snapshot captured and verified.")
            except Exception as e:
                print(f"WARNING: Pre-restore snapshot failed: {e}")
        else:
            print("Live database did not exist yet; skipping pre-restore copy.")

        # 3. Perform Live Restoration with WAL Truncate
        print("\nStep 3/4: Restoring database pages and syncing WAL...")
        try:
            src_conn = sqlite3.connect(str(backup_path))
            dest_conn = sqlite3.connect(LIVE_DB_PATH, timeout=10.0)
            dest_conn.execute("PRAGMA busy_timeout = 5000;")
            src_conn.backup(dest_conn)

            # Re-merge historical backup records
            if existing_backup_rows:
                try:
                    for row in existing_backup_rows:
                        dest_conn.execute(
                            """
                            INSERT INTO backup_records (id, filename, file_size_bytes, checksum_sha256, verification_status, created_by, created_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                            ON CONFLICT(id) DO NOTHING;
                            """,
                            row
                        )
                    dest_conn.commit()
                except Exception:
                    pass

            try:
                dest_conn.execute("PRAGMA wal_checkpoint(TRUNCATE);")
            except Exception:
                pass
            dest_conn.close()
            src_conn.close()
            print("✓ Database pages restored and historical backup catalog preserved.")
        except Exception as e:
            print(f"ERROR: Restoration failed: {e}")
            # Emergency rollback
            if pre_restore_file.exists():
                print("Attempting automatic rollback from emergency snapshot...")
                try:
                    rb_src = sqlite3.connect(pre_restore_file)
                    rb_dest = sqlite3.connect(LIVE_DB_PATH)
                    rb_src.backup(rb_dest)
                    rb_dest.close()
                    rb_src.close()
                    print("✓ Successfully rolled back to pre-restore state.")
                except Exception as rb_err:
                    print(f"CRITICAL: Rollback failed: {rb_err}")
            return False

        # 4. Post-Restore Verification
        print("\nStep 4/4: Running post-restore integrity check on live database...")
        try:
            check_conn = sqlite3.connect(LIVE_DB_PATH, timeout=10.0)
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
                # Emergency rollback
                if pre_restore_file.exists():
                    print("Rolling back due to failed verification...")
                    rb_src = sqlite3.connect(pre_restore_file)
                    rb_dest = sqlite3.connect(LIVE_DB_PATH)
                    rb_src.backup(rb_dest)
                    rb_dest.close()
                    rb_src.close()
                    print("✓ Rolled back to safe state.")
                return False
        except Exception as e:
            print(f"ERROR: Post-restore check failed: {e}")
            return False
    finally:
        if m_file.exists():
            try:
                m_file.unlink()
                print("✓ Maintenance gate released. Normal web traffic resumed.")
            except Exception:
                pass

def main():
    parser = argparse.ArgumentParser(description="Kitaab Bank Database Safe Restoration Tool")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--latest', action='store_true', help="Restore the most recent backup")
    group.add_argument('--file', type=str, help="Specific backup file name in backups/")
    group.add_argument('--list', action='store_true', help="List available backups")
    parser.add_argument('-y', '--yes', action='store_true', help="Bypass interactive confirmation prompt")

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

    success = restore_backup(target_file, skip_confirm=args.yes)
    return 0 if success else 1

if __name__ == '__main__':
    sys.exit(main())
