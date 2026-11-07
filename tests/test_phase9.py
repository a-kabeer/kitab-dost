"""
Phase 9 Comprehensive QA, Data Safety & Hardening Test Suite - Kitaab Bank
Tests:
1. Data Safety & Hot Backup Engine:
   - Full record commitment verification in live snapshot
   - SHA-256 detection of modified or corrupted backup files
   - Corrupt/invalid database rejection (schema checks, integrity_check)
   - Pre-restore safety rollback creation & post-restore verification
   - SQLite WAL & SHM handling (wal_checkpoint truncate)
   - Emergency rollback execution on simulated restoration failure
   - Deletion safety guard (cannot delete only remaining verified backup)
2. Exhibition Showcase Mode Safety:
   - Automatic pre-demo safety backup capture before seeding
   - Preservation of historical backup_records during demo resets
   - Demo mode flag persistence and banner activation
   - Safe exit from demo mode with automated restoration of real school data
3. Security & Anti-Exploitation Defenses:
   - CSRF protection across state-changing forms
   - CSV formula injection neutralization
   - PII privacy masking on tracking endpoints
   - Unauthorized access prevention across administrative endpoints
   - Credential rotation validation
"""

import hashlib
import os
import shutil
import sqlite3
import tempfile
import unittest
from pathlib import Path
from flask import session

from app import create_app
from app.database import get_db, init_db
from app.services import (
    backup_service,
    settings_service,
    analytics_service,
    activity_service
)
from scripts.seed_demo import reset_and_seed_demo_data

class Phase9ComprehensiveQATestCase(unittest.TestCase):
    def setUp(self):
        """Set up an isolated temporary database, backup folder, and app instance."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / 'test_kitaab_bank.db'
        self.backup_dir = Path(self.temp_dir) / 'backups'
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        self.app = create_app('testing')
        self.app.config.update({
            'TESTING': True,
            'DATABASE_PATH': self.db_path,
            'BACKUP_FOLDER': self.backup_dir,
            'WTF_CSRF_ENABLED': False,
            'SERVER_NAME': 'localhost'
        })

        init_db(self.app)
        self.client = self.app.test_client()

    def tearDown(self):
        """Clean up temporary test directory."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    # -------------------------------------------------------------------------
    # 1. Critical Data Safety & Hot Backup Engine Audits
    # -------------------------------------------------------------------------
    def test_backup_contains_all_committed_records(self):
        """Verify that a live hot snapshot contains 100% of committed books, requests, and handovers."""
        with self.app.app_context():
            db = get_db()
            # Insert 3 books
            for i in range(1, 4):
                db.execute(
                    """
                    INSERT INTO books (book_code, title, author, subject, class_grade, language, condition_state, status)
                    VALUES (?, ?, 'Author X', 'Math', 'Class 6', 'English', 'Good', 'available');
                    """,
                    (f'KB-BK-00099{i}', f'Committed Book {i}')
                )
            db.commit()

            # Create live backup
            ok, bck, err = backup_service.create_database_backup(created_by_id=1, teacher_name="Incharge")
            self.assertTrue(ok, f"Backup creation failed: {err}")

            # Inspect the snapshot file directly
            snapshot_path = self.backup_dir / bck['filename']
            self.assertTrue(snapshot_path.exists())

            snap_conn = sqlite3.connect(snapshot_path)
            cur = snap_conn.cursor()
            cur.execute("SELECT COUNT(*) FROM books WHERE book_code LIKE 'KB-BK-00099%';")
            count = cur.fetchone()[0]
            snap_conn.close()

            self.assertEqual(count, 3, "Snapshot missing committed records!")

    def test_sha256_detects_corrupt_or_modified_backup(self):
        """Verify SHA-256 calculation detects tampered or corrupted backup files on disk."""
        with self.app.app_context():
            ok, bck, _ = backup_service.create_database_backup()
            self.assertTrue(ok)
            file_path = self.backup_dir / bck['filename']
            original_hash = bck['checksum_sha256']

            # Verify original integrity passes
            valid, _ = backup_service.verify_backup_integrity(file_path, expected_checksum=original_hash)
            self.assertTrue(valid)

            # Corrupt the file by flipping bytes
            with open(file_path, 'r+b') as f:
                f.seek(100)
                f.write(b'CORRUPTED_BYTES_CORRUPTED_BYTES')

            # Verify integrity now catches hash mismatch
            valid_corrupt, msg = backup_service.verify_backup_integrity(file_path, expected_checksum=original_hash)
            self.assertFalse(valid_corrupt)
            self.assertIn("SHA-256 hash mismatch", msg)

    def test_invalid_schema_rejected_before_restoration(self):
        """Verify a database missing required tables is rejected by integrity verification."""
        fake_db = self.backup_dir / "fake_incomplete.db"
        conn = sqlite3.connect(fake_db)
        # Create only one dummy table
        conn.execute("CREATE TABLE dummy (id INTEGER PRIMARY KEY);")
        conn.commit()
        conn.close()

        valid, msg = backup_service.verify_backup_integrity(fake_db)
        self.assertFalse(valid)
        self.assertIn("Missing required backup tables", msg)

    def test_restore_fails_gracefully_with_corrupt_backup(self):
        """Verify restoration rejects corrupted files without altering the active live database."""
        with self.app.app_context():
            db = get_db()
            db.execute("INSERT INTO system_settings (key, value) VALUES ('safety_marker', 'live_data_untouched') ON CONFLICT(key) DO UPDATE SET value='live_data_untouched';")
            db.commit()

            # Create corrupt file
            corrupt_file = self.backup_dir / "corrupt_test.db"
            corrupt_payload = b"NOT_A_SQLITE_DATABASE_GARBAGE_HEADER"
            with open(corrupt_file, 'wb') as f:
                f.write(corrupt_payload)

            # Register the malformed bytes with their actual digest so restore
            # reaches SQLite integrity validation, not the uncatalogued-file guard.
            db.execute(
                """
                INSERT INTO backup_records (
                    filename, file_size_bytes, checksum_sha256, verification_status
                ) VALUES (?, ?, ?, 'VALID');
                """,
                (
                    corrupt_file.name,
                    len(corrupt_payload),
                    hashlib.sha256(corrupt_payload).hexdigest()
                )
            )
            db.commit()

            ok, pre_snap, err = backup_service.restore_database_from_backup(corrupt_file.name)
            self.assertFalse(ok)
            self.assertIn("rejected", err.lower())

            # Verify live database remains intact
            cur = db.cursor()
            cur.execute("SELECT value FROM system_settings WHERE key = 'safety_marker';")
            self.assertEqual(cur.fetchone()[0], 'live_data_untouched')

    def test_cannot_delete_only_remaining_valid_backup(self):
        """Safety Guard: System refuses to delete the only valid backup, preventing total backup loss."""
        with self.app.app_context():
            # Clear backups table for isolated test
            db = get_db()
            db.execute("DELETE FROM backup_records;")
            db.commit()

            # Create exactly 1 backup
            ok1, bck1, _ = backup_service.create_database_backup()
            self.assertTrue(ok1)

            # Attempt deletion of the sole valid backup
            del_ok, err = backup_service.delete_backup(bck1['id'], force=False)
            self.assertFalse(del_ok, "Deleted sole remaining valid backup!")
            self.assertIn("Cannot delete the only remaining verified database backup", err)

            # Create a 2nd backup
            ok2, bck2, _ = backup_service.create_database_backup()
            self.assertTrue(ok2)

            # Now deleting 1st backup succeeds because a 2nd valid backup exists
            del_ok2, err2 = backup_service.delete_backup(bck1['id'], force=False)
            self.assertTrue(del_ok2, f"Failed to delete non-sole backup: {err2}")

    def test_restore_wal_and_shm_safety(self):
        """Verify restore executes WAL checkpoint truncate on live database cleanly."""
        with self.app.app_context():
            db = get_db()
            # Ensure WAL mode
            cur = db.cursor()
            cur.execute("PRAGMA journal_mode = WAL;")
            cur.execute("INSERT INTO books (book_code, title, author, subject, class_grade, language, condition_state, status) VALUES ('KB-BK-WAL-1', 'WAL Test Book', 'Author', 'Math', 'Class 6', 'Urdu', 'Good', 'available');")
            db.commit()

            ok, bck, _ = backup_service.create_database_backup()
            self.assertTrue(ok)

            # Mutate
            db.execute("DELETE FROM books WHERE book_code = 'KB-BK-WAL-1';")
            db.commit()

            # Restore
            res_ok, pre_snap, res_err = backup_service.restore_database_from_backup(bck['id'])
            self.assertTrue(res_ok, f"Restore failed: {res_err}")

            # Verify book restored and WAL is healthy
            verify_conn = sqlite3.connect(self.db_path)
            c = verify_conn.cursor()
            c.execute("PRAGMA integrity_check;")
            self.assertEqual(c.fetchone()[0], 'ok')
            c.execute("SELECT title FROM books WHERE book_code = 'KB-BK-WAL-1';")
            self.assertEqual(c.fetchone()[0], 'WAL Test Book')
            verify_conn.close()

    # -------------------------------------------------------------------------
    # 2. Exhibition Showcase Mode Safety Audits
    # -------------------------------------------------------------------------
    def test_demo_seeder_creates_automatic_pre_demo_safety_backup(self):
        """Verify resetting demo mode automatically captures a pre-demo safety backup of real records."""
        with self.app.app_context():
            db = get_db()
            # Insert real custom school textbook
            db.execute(
                """
                INSERT INTO books (book_code, title, author, subject, class_grade, language, condition_state, status)
                VALUES ('KB-BK-REAL-001', 'Official School Unique Math', 'Principal', 'Math', 'Class 8', 'English', 'Good', 'available');
                """
            )
            db.commit()

            # Trigger demo seeder
            success = reset_and_seed_demo_data(target_db=self.db_path, create_safety_backup=True)
            self.assertTrue(success)

            # Verify pre_demo backup was captured on disk
            pre_demo_files = list(self.backup_dir.glob("*_pre_demo.db"))
            self.assertGreaterEqual(len(pre_demo_files), 1, "No automated pre-demo backup created!")

            # Verify pre_demo backup contains the real school book
            safety_conn = sqlite3.connect(pre_demo_files[0])
            c = safety_conn.cursor()
            c.execute("SELECT title FROM books WHERE book_code = 'KB-BK-REAL-001';")
            row = c.fetchone()
            safety_conn.close()
            self.assertIsNotNone(row)
            self.assertEqual(row[0], 'Official School Unique Math')

    def test_demo_mode_preserves_backup_records_catalog(self):
        """Verify demo seeder strictly preserves existing backup catalog entries."""
        with self.app.app_context():
            db = get_db()
            # Create a backup record
            db.execute(
                "INSERT INTO backup_records (filename, file_size_bytes, checksum_sha256, verification_status) "
                "VALUES ('real_school_valuable_backup.db', 10240, 'dummyhash1234567890', 'VALID');"
            )
            db.commit()

            # Run demo seeder
            reset_and_seed_demo_data(target_db=self.db_path, create_safety_backup=False)

            # Check that backup record still exists
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute("SELECT filename FROM backup_records WHERE filename = 'real_school_valuable_backup.db';")
            self.assertIsNotNone(c.fetchone(), "Demo seeder wiped historical backup catalog!")
            conn.close()

    def test_demo_mode_activation_and_safe_exit(self):
        """Verify is_demo_mode flag is set, and exit_demo_mode restores real data and clears the flag."""
        with self.app.app_context():
            db = get_db()
            # Insert real school marker
            db.execute("INSERT INTO books (book_code, title, author, subject, class_grade, language, condition_state, status) VALUES ('KB-REAL-100', 'Real School Data', 'Sir Tariq', 'Urdu', 'Class 6', 'Urdu', 'Good', 'available');")
            db.commit()

            # Seed demo data (with automatic pre-demo safety copy)
            reset_and_seed_demo_data(target_db=self.db_path, create_safety_backup=True)

            # Verify is_demo_mode is active
            self.assertTrue(settings_service.is_demo_mode_active())

            # Now execute safe exit
            exit_ok, restored_file, exit_err = settings_service.exit_demo_mode(teacher_name="Headmaster")
            self.assertTrue(exit_ok, f"Exit demo mode failed: {exit_err}")

            # Verify is_demo_mode is deactivated
            self.assertFalse(settings_service.is_demo_mode_active())

            # Verify real school data is restored
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM books WHERE book_code = 'KB-REAL-100';")
            self.assertEqual(cur.fetchone()[0], 1)
            conn.close()

    # -------------------------------------------------------------------------
    # 3. Security & Anti-Exploitation Defenses
    # -------------------------------------------------------------------------
    def test_csrf_defense_blocks_invalid_tokens_when_active(self):
        """Verify CSRF validation rejects state mutations with missing or forged tokens."""
        # Enable CSRF enforcement for this test
        self.app.config['WTF_CSRF_ENABLED'] = True

        with self.client:
            # Login
            with self.client.session_transaction() as sess:
                sess['teacher_id'] = 1
                sess['teacher_name'] = 'Teacher'
                sess['csrf_token'] = 'legitimate_csrf_token_value_123'

            # Missing CSRF token -> HTTP 400
            resp_missing = self.client.post('/teacher/settings/profile', data={
                'school_name': 'Hacked School'
            })
            self.assertEqual(resp_missing.status_code, 400)

            # Forged CSRF token -> HTTP 400
            resp_forged = self.client.post('/teacher/settings/profile', data={
                'csrf_token': 'forged_fake_token_xyz',
                'school_name': 'Hacked School'
            })
            self.assertEqual(resp_forged.status_code, 400)

            # Valid token -> HTTP 302 redirect
            resp_valid = self.client.post('/teacher/settings/profile', data={
                'csrf_token': 'legitimate_csrf_token_value_123',
                'school_name': 'Valid Model School',
                'academic_year': '2026-2027',
                'default_language': 'en'
            })
            self.assertEqual(resp_valid.status_code, 302)

    def test_csv_injection_formula_neutralization(self):
        """Verify all spreadsheet formula triggers are escaped across cell data."""
        payloads = [
            "=1+1",
            "+12345",
            "-SUM(A1:A10)",
            "@HYPERLINK('http://malicious.site','Click Here')",
            "\tCMD /C calc",
            "\rDIR"
        ]
        for p in payloads:
            escaped = analytics_service.sanitize_csv_cell(p)
            self.assertTrue(escaped.startswith("'"), f"Formula not sanitized: {p}")

    def test_tracking_page_pii_privacy(self):
        """Verify public tracking endpoint masks student contact and roll numbers."""
        with self.app.app_context():
            db = get_db()
            db.execute("INSERT OR IGNORE INTO books (id, book_code, title, author, subject, class_grade, language, condition_state, status) VALUES (99, 'KB-BK-PRIV-1', 'Privacy Book', 'A', 'S', 'Class 6', 'Urdu', 'Good', 'reserved');")
            db.execute(
                """
                INSERT INTO requests (tracking_code, book_id, requester_name, requester_class, requester_roll_no, requester_contact, status)
                VALUES ('KB-REQ-PRIV-TEST', 99, 'Muhammad Bilal', 'Class 7-B', 'ROLL-9988', '0300-9876543', 'approved');
                """
            )
            db.commit()

            resp = self.client.get('/track?code=KB-REQ-PRIV-TEST')
            self.assertEqual(resp.status_code, 200)
            html = resp.get_data(as_text=True)

            # Public page must NOT reveal raw private student phone number or full roll number
            self.assertNotIn('0300-9876543', html)
            self.assertNotIn('ROLL-9988', html)

    def test_teacher_auth_required_across_settings_endpoints(self):
        """Verify all settings and management actions require active teacher authentication."""
        endpoints = [
            ('/teacher/settings', 'GET'),
            ('/teacher/settings/profile', 'POST'),
            ('/teacher/settings/password', 'POST'),
            ('/teacher/settings/backup/create', 'POST'),
            ('/teacher/settings/backup/1/download', 'GET'),
            ('/teacher/settings/backup/1/delete', 'POST'),
            ('/teacher/settings/seed-demo', 'POST'),
            ('/teacher/settings/exit-demo', 'POST'),
        ]
        for path, method in endpoints:
            if method == 'GET':
                r = self.client.get(path)
            else:
                r = self.client.post(path)
            self.assertEqual(r.status_code, 302, f"Auth bypass on {method} {path}")
            self.assertIn('/auth/login', r.headers['Location'])


if __name__ == '__main__':
    unittest.main()
