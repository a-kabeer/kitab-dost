"""
Final Data Safety & Restoration Hardening Test Suite for Kitaab Bank.
Audits:
1. Empty database entering demo mode (creates full pre-demo backup snapshot).
2. Real database preservation in pre-demo snapshot.
3. Repeated demo activation does not overwrite the original real school backup point.
4. Exact backup selection during Exit Demo (never arbitrary latest).
5. Attempted deletion of active pre-demo backup is strictly rejected.
6. Interrupted demo operation / crash resilience across application restarts.
7. Concurrent requests during restore gated with HTTP 503.
8. Corrupted backup rejected before live database modification.
9. Failed restore triggers automatic rollback to pre-restore snapshot.
10. Successful restore passes post-restore PRAGMA integrity check and verification.
"""

import os
import shutil
import sqlite3
import tempfile
import unittest
from pathlib import Path

from app import create_app
from app.database import get_db, init_db
from app.services import backup_service, settings_service, maintenance_service
from scripts.seed_demo import reset_and_seed_demo_data

class FinalDataSafetyTestCase(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / 'test_kitaab_bank.db'
        self.backup_dir = Path(self.temp_dir) / 'backups'
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        self.app = create_app('testing')
        self.app.config.update({
            'TESTING': True,
            'DATABASE_PATH': self.db_path,
            'BACKUP_FOLDER': str(self.backup_dir),
            'WTF_CSRF_ENABLED': False,
            'SECRET_KEY': 'test-secret-key'
        })
        self.client = self.app.test_client()

        with self.app.app_context():
            init_db(self.app)

    def tearDown(self):
        maintenance_service.set_maintenance_mode(False)
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    # -------------------------------------------------------------------------
    # Test 1: Empty database entering demo mode
    # -------------------------------------------------------------------------
    def test_01_empty_database_entering_demo_mode_captures_backup(self):
        """Verify entering demo mode captures a verified backup even when books table is empty (0 books)."""
        with self.app.app_context():
            db = get_db()
            cur = db.cursor()
            cur.execute("SELECT COUNT(*) FROM books;")
            self.assertEqual(cur.fetchone()[0], 0, "Books table should start empty")

            # Seed demo data with create_safety_backup=True
            success = reset_and_seed_demo_data(
                target_db=self.db_path,
                create_safety_backup=True,
                target_backup_dir=self.backup_dir
            )
            self.assertTrue(success)

            # Pre-demo backup MUST exist on disk
            pre_demo_files = list(self.backup_dir.glob("*_pre_demo.db"))
            self.assertEqual(len(pre_demo_files), 1, "Pre-demo safety backup must be created even if 0 books!")

            # Verify demo_pre_backup_id was recorded in system_settings
            exact_id = settings_service.get_demo_pre_backup_id()
            self.assertIsNotNone(exact_id, "demo_pre_backup_id must be stored in system_settings")

            # Verify recorded backup exists in catalog
            bck = backup_service.get_backup_by_id(exact_id)
            self.assertIsNotNone(bck)
            self.assertEqual(bck['verification_status'], 'VALID')

    # -------------------------------------------------------------------------
    # Test 2: Real database preservation
    # -------------------------------------------------------------------------
    def test_02_real_database_preservation_in_pre_demo_backup(self):
        """Verify real school textbooks and activity are preserved in the pre-demo backup."""
        with self.app.app_context():
            db = get_db()
            db.execute(
                """
                INSERT INTO books (book_code, title, author, subject, class_grade, language, condition_state, status)
                VALUES ('KB-REAL-999', 'Real Govt Physics Class 8', 'Sir Ahmed', 'Physics', 'Class 8', 'Urdu', 'Good', 'available');
                """
            )
            db.commit()

            # Seed demo data
            reset_and_seed_demo_data(
                target_db=self.db_path,
                create_safety_backup=True,
                target_backup_dir=self.backup_dir
            )

            exact_id = settings_service.get_demo_pre_backup_id()
            bck = backup_service.get_backup_by_id(exact_id)
            self.assertIsNotNone(bck)

            # Check that pre-demo snapshot contains the real school textbook
            pre_demo_path = self.backup_dir / bck['filename']
            conn = sqlite3.connect(pre_demo_path)
            c = conn.cursor()
            c.execute("SELECT title FROM books WHERE book_code = 'KB-REAL-999';")
            row = c.fetchone()
            conn.close()
            self.assertIsNotNone(row)
            self.assertEqual(row[0], 'Real Govt Physics Class 8')

    # -------------------------------------------------------------------------
    # Test 3: Repeated demo activation does not overwrite recovery point
    # -------------------------------------------------------------------------
    def test_03_repeated_demo_activation_preserves_original_recovery_point(self):
        """Activating demo mode repeatedly must NOT overwrite the original pre-demo backup with demo data."""
        with self.app.app_context():
            db = get_db()
            db.execute("INSERT INTO books (book_code, title, author, subject, class_grade, language, condition_state, status) VALUES ('KB-ORIG-001', 'Original Real Book', 'Real Author', 'Math', 'Class 6', 'Urdu', 'Good', 'available');")
            db.commit()

            # First demo activation
            reset_and_seed_demo_data(target_db=self.db_path, create_safety_backup=True, target_backup_dir=self.backup_dir)
            first_pre_backup_id = settings_service.get_demo_pre_backup_id()
            self.assertIsNotNone(first_pre_backup_id)

            first_bck = backup_service.get_backup_by_id(first_pre_backup_id)
            first_filename = first_bck['filename']

            # Repeated demo activation while already in demo mode
            reset_and_seed_demo_data(target_db=self.db_path, create_safety_backup=True, target_backup_dir=self.backup_dir)
            second_pre_backup_id = settings_service.get_demo_pre_backup_id()

            # Must preserve the exact first pre-demo backup ID
            self.assertEqual(first_pre_backup_id, second_pre_backup_id, "Repeated demo activation replaced the original recovery point!")

            # Verify the snapshot still contains the original real book, not demo data
            conn = sqlite3.connect(self.backup_dir / first_filename)
            c = conn.cursor()
            c.execute("SELECT title FROM books WHERE book_code = 'KB-ORIG-001';")
            row = c.fetchone()
            conn.close()
            self.assertIsNotNone(row, "Original recovery point was overwritten with demo data!")

    # -------------------------------------------------------------------------
    # Test 4: Exact backup selection during Exit Demo
    # -------------------------------------------------------------------------
    def test_04_exact_backup_selection_during_exit_demo(self):
        """Exit Demo must restore the exact pre-demo backup, never an arbitrary latest backup."""
        with self.app.app_context():
            db = get_db()
            db.execute("INSERT INTO books (book_code, title, author, subject, class_grade, language, condition_state, status) VALUES ('KB-SCHOOL-TRUE', 'True School Archive', 'Staff', 'History', 'Class 7', 'English', 'Good', 'available');")
            db.commit()

            # Enter demo mode
            reset_and_seed_demo_data(target_db=self.db_path, create_safety_backup=True, target_backup_dir=self.backup_dir)
            target_pre_backup_id = settings_service.get_demo_pre_backup_id()

            # Simulate teacher creating a newer manual backup while in demo mode
            ok_man, man_bck, _ = backup_service.create_database_backup(teacher_name="Teacher In Demo")
            self.assertTrue(ok_man)
            self.assertGreater(man_bck['id'], target_pre_backup_id, "Manual backup must have higher ID")

            # Exit demo mode
            exit_ok, restored_file, err = settings_service.exit_demo_mode(teacher_name="Headmaster")
            self.assertTrue(exit_ok, f"Exit demo failed: {err}")

            # Verify that restored file was the PRE-DEMO backup, NOT the newer manual demo backup
            expected_filename = backup_service.get_backup_by_id(target_pre_backup_id)['filename']
            self.assertEqual(restored_file, expected_filename, "Exit demo restored arbitrary latest backup instead of pre-demo backup!")

            # Confirm real school book is back in live database
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM books WHERE book_code = 'KB-SCHOOL-TRUE';")
            self.assertEqual(c.fetchone()[0], 1)
            conn.close()

    # -------------------------------------------------------------------------
    # Test 5: Attempted deletion of protected pre-demo backup
    # -------------------------------------------------------------------------
    def test_05_attempted_deletion_of_active_pre_demo_backup_rejected(self):
        """System must strictly reject deleting the active pre-demo safety backup while demo mode is active."""
        with self.app.app_context():
            # Create a real book and enter demo mode
            db = get_db()
            db.execute("INSERT INTO books (book_code, title, author, subject, class_grade, language, condition_state, status) VALUES ('KB-REAL-SEC', 'Secure Real Data', 'Author', 'Islamiat', 'Class 6', 'Urdu', 'Good', 'available');")
            db.commit()

            reset_and_seed_demo_data(target_db=self.db_path, create_safety_backup=True, target_backup_dir=self.backup_dir)
            pre_id = settings_service.get_demo_pre_backup_id()

            # Create another backup so sole-backup check does not confound this test
            backup_service.create_database_backup()

            # Try deleting the active pre-demo backup
            del_ok, err = backup_service.delete_backup(pre_id, force=False)
            self.assertFalse(del_ok, "Allowed deletion of active pre-demo backup while in demo mode!")
            self.assertIn("active pre-demo safety backup", err)

            # Confirm file still exists
            bck = backup_service.get_backup_by_id(pre_id)
            self.assertTrue((self.backup_dir / bck['filename']).exists())

    # -------------------------------------------------------------------------
    # Test 6: Interrupted demo operation / crash resilience
    # -------------------------------------------------------------------------
    def test_06_crash_resilience_and_interrupted_demo_recovery(self):
        """If application crashes or restarts while in demo mode, state is preserved and Exit Demo recovers real data."""
        with self.app.app_context():
            db = get_db()
            db.execute("INSERT INTO books (book_code, title, author, subject, class_grade, language, condition_state, status) VALUES ('KB-CRASH-TEST', 'Pre-Crash Real Book', 'Author', 'Civics', 'Class 8', 'Urdu', 'Good', 'available');")
            db.commit()

            reset_and_seed_demo_data(target_db=self.db_path, create_safety_backup=True, target_backup_dir=self.backup_dir)
            orig_pre_id = settings_service.get_demo_pre_backup_id()

        # Simulate sudden application crash & fresh restart by spinning up a new Flask instance
        new_app = create_app('testing')
        new_app.config.update({
            'TESTING': True,
            'DATABASE_PATH': self.db_path,
            'BACKUP_FOLDER': str(self.backup_dir),
            'WTF_CSRF_ENABLED': False
        })

        with new_app.app_context():
            # Verify demo mode is still recognized as active
            self.assertTrue(settings_service.is_demo_mode_active())
            self.assertEqual(settings_service.get_demo_pre_backup_id(), orig_pre_id)

            # Successfully execute exit demo on restarted application
            exit_ok, restored_file, err = settings_service.exit_demo_mode()
            self.assertTrue(exit_ok, f"Exit demo failed after restart: {err}")

            # Verify real data is restored
            c = sqlite3.connect(self.db_path).cursor()
            c.execute("SELECT COUNT(*) FROM books WHERE book_code = 'KB-CRASH-TEST';")
            self.assertEqual(c.fetchone()[0], 1)
            c.close()

    # -------------------------------------------------------------------------
    # Test 7: Concurrent requests during restore
    # -------------------------------------------------------------------------
    def test_07_concurrent_requests_gated_with_503_during_restore(self):
        """When maintenance mode is active, incoming student and teacher requests receive HTTP 503."""
        with self.app.app_context():
            # Activate maintenance mode
            maintenance_service.set_maintenance_mode(True)
            try:
                # Student catalogue request must return 503
                res = self.client.get('/catalogue')
                self.assertEqual(res.status_code, 503)
                self.assertIn("Database Maintenance in Progress", res.get_data(as_text=True))

                # Student donation submission must return 503
                res_post = self.client.post('/donate', data={'student_name': 'Ali'})
                self.assertEqual(res_post.status_code, 503)
            finally:
                maintenance_service.set_maintenance_mode(False)

            # Once maintenance is released, normal requests return 200
            res_normal = self.client.get('/catalogue')
            self.assertEqual(res_normal.status_code, 200)

    # -------------------------------------------------------------------------
    # Test 8: Corrupted backup rejection
    # -------------------------------------------------------------------------
    def test_08_corrupted_backup_rejected_before_live_mutation(self):
        """Corrupted backup with invalid bytes or checksum mismatch must be rejected with zero mutation."""
        with self.app.app_context():
            # Create a live database with safety marker
            db = get_db()
            db.execute("INSERT INTO books (book_code, title, author, subject, class_grade, language, condition_state, status) VALUES ('KB-SAFE-CORRUPT', 'Untouched Real Book', 'Author', 'Math', 'Class 6', 'Urdu', 'Good', 'available');")
            db.commit()

            # Create a valid backup, then deliberately corrupt it
            ok, bck, _ = backup_service.create_database_backup()
            self.assertTrue(ok)
            corrupt_path = self.backup_dir / bck['filename']
            with open(corrupt_path, 'r+b') as f:
                f.seek(100)
                f.write(b'GARBAGE_CORRUPT_BYTES_XYZ_123')

            # Attempt restore of corrupted backup
            res_ok, _, err = backup_service.restore_database_from_backup(bck['id'])
            self.assertFalse(res_ok, "Restored a corrupted backup file!")
            self.assertIn("rejected", err.lower())

            # Confirm live database is completely untouched
            c = sqlite3.connect(self.db_path).cursor()
            c.execute("SELECT title FROM books WHERE book_code = 'KB-SAFE-CORRUPT';")
            row = c.fetchone()
            c.close()
            self.assertIsNotNone(row)
            self.assertEqual(row[0], 'Untouched Real Book')

    # -------------------------------------------------------------------------
    # Test 9: Failed restore rollback
    # -------------------------------------------------------------------------
    def test_09_failed_restore_triggers_automatic_rollback(self):
        """If restore verification fails after page streaming, automatic rollback restores pre-restore snapshot."""
        with self.app.app_context():
            db = get_db()
            db.execute("INSERT INTO books (book_code, title, author, subject, class_grade, language, condition_state, status) VALUES ('KB-LIVE-ORIG', 'Original State Before Failed Restore', 'Author', 'Urdu', 'Class 6', 'Urdu', 'Good', 'available');")
            db.commit()

            # Create a backup that lacks the required core tables (invalid schema)
            invalid_db_path = self.backup_dir / "kitab_bank_backup_invalid_schema.db"
            inv_conn = sqlite3.connect(invalid_db_path)
            inv_conn.execute("CREATE TABLE fake_table (id INTEGER PRIMARY KEY);")
            inv_conn.commit()
            inv_conn.close()

            # Catalog invalid backup in backup_records
            cur = db.cursor()
            cur.execute(
                "INSERT INTO backup_records (filename, file_size_bytes, checksum_sha256, verification_status) VALUES ('kitab_bank_backup_invalid_schema.db', 4096, 'fakechecksum', 'VALID');"
            )
            db.commit()
            inv_id = cur.lastrowid

            # Attempt restore
            res_ok, _, err = backup_service.restore_database_from_backup(inv_id)
            self.assertFalse(res_ok)

            # Confirm original live data is preserved
            c = sqlite3.connect(self.db_path).cursor()
            c.execute("SELECT title FROM books WHERE book_code = 'KB-LIVE-ORIG';")
            row = c.fetchone()
            c.close()
            self.assertIsNotNone(row)
            self.assertEqual(row[0], 'Original State Before Failed Restore')

    # -------------------------------------------------------------------------
    # Test 10: Successful restore and database integrity
    # -------------------------------------------------------------------------
    def test_10_successful_restore_and_database_integrity(self):
        """A valid backup restore succeeds, syncs WAL, and passes post-restore integrity check."""
        with self.app.app_context():
            db = get_db()
            cur = db.cursor()
            cur.execute("PRAGMA journal_mode = WAL;")
            cur.execute("INSERT INTO books (book_code, title, author, subject, class_grade, language, condition_state, status) VALUES ('KB-RESTORE-OK', 'Restored Success Book', 'Author', 'Science', 'Class 7', 'Urdu', 'Good', 'available');")
            db.commit()

            # Create backup of this state
            ok, bck, _ = backup_service.create_database_backup()
            self.assertTrue(ok)

            # Mutate live database
            db.execute("DELETE FROM books WHERE book_code = 'KB-RESTORE-OK';")
            db.commit()
            cur.execute("SELECT COUNT(*) FROM books WHERE book_code = 'KB-RESTORE-OK';")
            self.assertEqual(cur.fetchone()[0], 0)

            # Execute restore
            res_ok, pre_snap, err = backup_service.restore_database_from_backup(bck['id'])
            self.assertTrue(res_ok, f"Restore failed: {err}")

            # Verify live database integrity check is 'ok'
            verify_conn = sqlite3.connect(self.db_path)
            c = verify_conn.cursor()
            c.execute("PRAGMA integrity_check;")
            self.assertEqual(c.fetchone()[0], 'ok')

            # Verify book is restored
            c.execute("SELECT title FROM books WHERE book_code = 'KB-RESTORE-OK';")
            row = c.fetchone()
            self.assertIsNotNone(row)
            self.assertEqual(row[0], 'Restored Success Book')
            verify_conn.close()

if __name__ == '__main__':
    unittest.main()
