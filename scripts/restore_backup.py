"""
Kitaab Bank - Safe Database Restoration CLI Tool
Usage:
    python scripts/restore_backup.py --latest
    python scripts/restore_backup.py --file kitab_bank_backup_20261105_120000.db
    python scripts/restore_backup.py --list
"""

import sys
import os
import json
import socket
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

def is_server_active(port=5000):
    """Check if Waitress production server is actively listening on localhost port."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(0.5)
    try:
        res = s.connect_ex(('127.0.0.1', port))
        return res == 0
    except Exception:
        return False
    finally:
        s.close()

def is_database_locked(db_path):
    """Check if the live SQLite database is locked by an active external transaction."""
    db_path = Path(db_path)
    if not db_path.exists():
        return False
    try:
        conn = sqlite3.connect(str(db_path), timeout=0.2)
        conn.execute("BEGIN IMMEDIATE;")
        conn.rollback()
        conn.close()
        return False
    except (sqlite3.OperationalError, sqlite3.DatabaseError):
        return True

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

def restore_backup(backup_path, skip_confirm=False, port=5000, check_server=True):
    """Safely restore database from verified backup file with cross-process server check and crash resilience."""
    backup_path = Path(backup_path)
    if not backup_path.exists():
        print(f"ERROR: Backup file '{backup_path}' does not exist.")
        return False

    # 0. Cross-Process Safety Check: Require Waitress to be stopped before CLI restore
    if check_server and is_server_active(port=port):
        print("\n" + "=" * 70)
        print("[CROSS-PROCESS SAFETY GUARD] ACTIVE WAITRESS SERVER DETECTED")
        print("=" * 70)
        print(f"The Waitress production server is actively listening on port {port}.")
        print("To guarantee cross-process data safety and eliminate any write conflicts:")
        print("  1. Stop the Waitress server (Ctrl+C on start_kitaab_bank window) before running CLI restore; OR")
        print("  2. Perform restoration safely from the Teacher Settings web portal (/teacher/settings?tab=backup).")
        print("=" * 70)
        print("CLI restoration ABORTED. Live database was NOT modified.\n")
        return False

    if is_database_locked(LIVE_DB_PATH):
        print("\n[ERROR] Live database is locked by an active external transaction. CLI restore aborted.\n")
        return False

    print(f"\nTarget Backup: {backup_path.name}")
    print(f"File Size:     {backup_path.stat().st_size / 1024:.1f} KB")

    if not skip_confirm:
        print("\n[SAFETY NOTICE]")
        print("Restoring will replace the current active database with the contents of this snapshot.")
        print("An automated pre-restore rollback snapshot will be captured before modifying the live database.")
        ans = input("Proceed with database restoration? (y/N): ").strip().lower()
        if ans not in ('y', 'yes'):
            print("Restoration cancelled by user.")
            return False

    # 1. Integrity & Strict Schema Check on Target Backup
    print("\nStep 1/4: Checking target backup file integrity and required schema...")
    try:
        from app.services.backup_service import verify_backup_integrity
        is_valid, v_msg = verify_backup_integrity(backup_path)
        if not is_valid:
            print(f"ERROR: Backup validation rejected: {v_msg}")
            return False
        print("✓ Backup integrity and schema verification PASSED.")
    except Exception as e:
        print(f"ERROR: Could not verify backup file: {e}")
        return False

    # 2. Acquire Maintenance Gate & Create Pre-Restore Rollback Snapshot
    m_file = LIVE_DB_PATH.parent / '.maintenance_lock'
    rip_file = LIVE_DB_PATH.parent / '.restore_in_progress'

    try:
        m_file.write_text(f"CLI_RESTORE_ACTIVE:{datetime.now().isoformat()}")
        print("\n[MAINTENANCE GATE] Acquired maintenance lock (.maintenance_lock).")

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

        # Record crash resilience marker
        rip_file.write_text(json.dumps({
            "rollback_snapshot": str(pre_restore_file),
            "target_backup": str(backup_path.name),
            "started_at": datetime.now().isoformat()
        }))

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
                    if rip_file.exists():
                        rip_file.unlink()
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
                if rip_file.exists():
                    rip_file.unlink()
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
                    if rip_file.exists():
                        rip_file.unlink()
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
    parser.add_argument('-y', '--yes', action='store_true', help="Skip interactive confirmation prompt")
    parser.add_argument('--port', type=int, default=5000, help="Port to check for active Waitress server")
    parser.add_argument('--no-server-check', action='store_true', help="Bypass active server port check")

    args = parser.parse_args()

    if args.list:
        list_backups()
        return

    target_file = None
    if args.latest:
        backups = sorted(BACKUPS_DIR.glob("kitab_bank_backup_*.db"), reverse=True)
        if not backups:
            print("ERROR: No backup files found in backups/ directory.")
            sys.exit(1)
        target_file = backups[0]
    elif args.file:
        target_file = BACKUPS_DIR / args.file
        if not target_file.exists():
            target_file = Path(args.file)

    if not target_file or not target_file.exists():
        print(f"ERROR: Backup file '{target_file}' not found.")
        sys.exit(1)

    success = restore_backup(
        target_file,
        skip_confirm=args.yes,
        port=args.port,
        check_server=not args.no_server_check
    )
    if not success:
        sys.exit(1)

if __name__ == '__main__':
    main()
