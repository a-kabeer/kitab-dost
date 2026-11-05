"""
Final Restore Safety Verification Test Suite for Kitaab Bank.
Audits:
1. In-flight database transaction lasting longer than 500ms (deterministic draining).
2. New requests during maintenance are gated with HTTP 503.
3. Restore controller does not deadlock while waiting (excludes controller thread).
4. CLI restore attempted while Waitress server is active is rejected.
5. Successful restore after all connections drain.
6. Drain timeout safely aborts restoration without modifying live database.
7. Interrupted restoration recovery across application startup.
8. Invalid schema backup rejection (strict table and column validation).
"""

import os
import json
import time
import socket
import shutil
import sqlite3
import tempfile
import threading
import unittest
from pathlib import Path

from app import create_app
from app.database import get_db, init_db
from app.services import backup_service, maintenance_service
from scripts.restore_backup import restore_backup, is_server_active

class RestoreSafetyHardeningTestCase(unittest.TestCase):
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
            'SECRET_KEY': 'safety-secret'
        })
        self.client = self.app.test_client()

        with self.app.app_context():
            init_db(self.app)

    def tearDown(self):
        maintenance_service.set_maintenance_mode(False)
        maintenance_service.clear_restore_in_progress()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    # -------------------------------------------------------------------------
    # 1. In-flight database transaction lasting > 500ms
    # -------------------------------------------------------------------------
    def test_01_inflight_transaction_longer_than_500ms_drains_deterministically(self):
        """Connection drainer waits deterministically for an in-flight transaction taking > 500ms."""
        query_finished = threading.Event()
        start_restore = threading.Event()

        def slow_writer():
            with self.app.app_context():
                db = get_db()
                start_restore.set() # signal restore thread to begin
                time.sleep(0.7)     # in-flight transaction lasts 700ms (> 500ms)
                db.execute("INSERT INTO books (book_code, title, author, subject, class_grade, language, condition_state, status) VALUES ('KB-SLOW-01', 'Slow Book', 'Author', 'Math', 'Class 6', 'Urdu', 'Good', 'available');")
                db.commit()
                query_finished.set()

        t = threading.Thread(target=slow_writer)
        t.start()
        start_restore.wait()

        # Call drain_connections with 3.0s timeout
        drain_start = time.time()
        drained = maintenance_service.drain_connections(timeout=3.0)
        drain_duration = time.time() - drain_start

        t.join()
        self.assertTrue(drained, "Deterministic drain should succeed after slow transaction completes")
        self.assertGreaterEqual(drain_duration, 0.65, f"Drain returned too early ({drain_duration}s), did not wait for 700ms query!")

    # -------------------------------------------------------------------------
    # 2. New requests during maintenance receive HTTP 503
    # -------------------------------------------------------------------------
    def test_02_new_requests_during_maintenance_gated_with_503(self):
        """New student/teacher requests during maintenance receive HTTP 503 Service Unavailable."""
        with self.app.app_context():
            maintenance_service.set_maintenance_mode(True)
            try:
                res_cat = self.client.get('/catalogue')
                self.assertEqual(res_cat.status_code, 503)
                self.assertIn("Database Maintenance in Progress", res_cat.get_data(as_text=True))

                res_home = self.client.get('/')
                self.assertEqual(res_home.status_code, 503)

                res_post = self.client.post('/donate', data={'title': 'Test'})
                self.assertEqual(res_post.status_code, 503)
            finally:
                maintenance_service.set_maintenance_mode(False)

            # Normal requests resume
            res_after = self.client.get('/catalogue')
            self.assertEqual(res_after.status_code, 200)

    # -------------------------------------------------------------------------
    # 3. Restore controller does not deadlock while waiting
    # -------------------------------------------------------------------------
    def test_03_restore_controller_does_not_deadlock_while_waiting(self):
        """Restore controller thread is excluded from drain check and executes without deadlock."""
        with self.app.app_context():
            # Current thread holds an open DB connection via get_db()
            db = get_db()
            db.execute("INSERT INTO books (book_code, title, author, subject, class_grade, language, condition_state, status) VALUES ('KB-CTRL-01', 'Controller Book', 'Author', 'Science', 'Class 7', 'Urdu', 'Good', 'available');")
            db.commit()

            ok, bck, _ = backup_service.create_database_backup()
            self.assertTrue(ok)

            # Initiate restore from the same thread holding the DB connection
            start_t = time.time()
            res_ok, pre_snap, err = backup_service.restore_database_from_backup(bck['id'], drain_timeout=2.0)
            duration = time.time() - start_t

            self.assertTrue(res_ok, f"Restore failed with error: {err}")
            self.assertLess(duration, 1.5, f"Restore took too long ({duration}s), possible deadlock!")

    # -------------------------------------------------------------------------
    # 4. CLI restore attempted while Waitress is active is rejected
    # -------------------------------------------------------------------------
    def test_04_cli_restore_attempted_while_server_active_is_rejected(self):
        """CLI restore detects an active server on the specified port and aborts immediately."""
        with self.app.app_context():
            ok, bck, _ = backup_service.create_database_backup()
            self.assertTrue(ok)
            backup_file = self.backup_dir / bck['filename']

            # Spin up a mock socket listener on an ephemeral test port
            srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            srv.bind(('127.0.0.1', 0))
            srv.listen(5)
            active_port = srv.getsockname()[1]

            stop_acceptor = False
            def acceptor():
                while not stop_acceptor:
                    try:
                        srv.settimeout(0.1)
                        conn, _ = srv.accept()
                        conn.close()
                    except Exception:
                        pass

            acc_t = threading.Thread(target=acceptor)
            acc_t.start()

            try:
                # Verify is_server_active detects the open socket
                self.assertTrue(is_server_active(port=active_port))

                # Attempt CLI restore with port check enabled
                success = restore_backup(
                    backup_path=backup_file,
                    skip_confirm=True,
                    port=active_port,
                    check_server=True
                )
                self.assertFalse(success, "CLI restore should abort when server is active on port!")
            finally:
                stop_acceptor = True
                acc_t.join()
                srv.close()

    # -------------------------------------------------------------------------
    # 5. Successful restore after all connections drain
    # -------------------------------------------------------------------------
    def test_05_successful_restore_after_all_connections_drain(self):
        """Database successfully restores after all concurrent connections finish and drain."""
        with self.app.app_context():
            db = get_db()
            db.execute("INSERT INTO books (book_code, title, author, subject, class_grade, language, condition_state, status) VALUES ('KB-DRAIN-OK', 'Drain Target Book', 'Author', 'Urdu', 'Class 6', 'Urdu', 'Good', 'available');")
            db.commit()

            ok, bck, _ = backup_service.create_database_backup()
            self.assertTrue(ok)

            # Mutate live DB
            db.execute("DELETE FROM books WHERE book_code = 'KB-DRAIN-OK';")
            db.commit()

            # Execute restore with deterministic draining
            res_ok, pre_snap, err = backup_service.restore_database_from_backup(bck['id'], drain_timeout=3.0)
            self.assertTrue(res_ok, f"Restore failed: {err}")

            # Verify restored book exists in live DB
            c = sqlite3.connect(self.db_path).cursor()
            c.execute("SELECT title FROM books WHERE book_code = 'KB-DRAIN-OK';")
            row = c.fetchone()
            c.close()
            self.assertIsNotNone(row)
            self.assertEqual(row[0], 'Drain Target Book')

    # -------------------------------------------------------------------------
    # 6. Drain timeout safely aborts restoration without modifying live DB
    # -------------------------------------------------------------------------
    def test_06_drain_timeout_safely_aborts_restoration_without_live_modification(self):
        """If connections cannot be drained within timeout, restoration aborts and live DB is untouched."""
        with self.app.app_context():
            # Create a backup to restore
            ok, bck, _ = backup_service.create_database_backup()
            self.assertTrue(ok)

            # Insert safety marker in live DB
            db = get_db()
            db.execute("INSERT INTO books (book_code, title, author, subject, class_grade, language, condition_state, status) VALUES ('KB-LIVE-GUARD', 'Live Guard Book', 'Author', 'Math', 'Class 6', 'Urdu', 'Good', 'available');")
            db.commit()

        stop_rogue = threading.Event()
        rogue_started = threading.Event()

        def rogue_connection():
            # Thread that simulates an unyielding database connection
            maintenance_service.register_db_connection()
            rogue_started.set()
            stop_rogue.wait() # hold connection open until test finishes
            maintenance_service.unregister_db_connection()

        t = threading.Thread(target=rogue_connection)
        t.start()
        rogue_started.wait()

        with self.app.app_context():
            # Attempt restore with short drain timeout (0.3s)
            res_ok, _, err = backup_service.restore_database_from_backup(bck['id'], drain_timeout=0.3)
            self.assertFalse(res_ok, "Restore should fail when connections cannot be drained!")
            self.assertIn("Connection drain timeout", str(err))

            # Stop rogue thread
            stop_rogue.set()
            t.join()

            # Verify live database remains completely untouched
            c = sqlite3.connect(self.db_path).cursor()
            c.execute("SELECT title FROM books WHERE book_code = 'KB-LIVE-GUARD';")
            row = c.fetchone()
            c.close()
            self.assertIsNotNone(row, "Live database was modified despite drain timeout!")
            self.assertEqual(row[0], 'Live Guard Book')

    # -------------------------------------------------------------------------
    # 7. Interrupted restoration recovery across application startup
    # -------------------------------------------------------------------------
    def test_07_interrupted_restoration_recovered_on_application_startup(self):
        """If application crashed during restore, startup detects .restore_in_progress and recovers rollback snapshot."""
        with self.app.app_context():
            # Initial healthy state with a real book
            db = get_db()
            db.execute("INSERT INTO books (book_code, title, author, subject, class_grade, language, condition_state, status) VALUES ('KB-RECOVER-01', 'Book Before Crash', 'Author', 'History', 'Class 8', 'English', 'Good', 'available');")
            db.commit()

            # Capture verified rollback snapshot
            rollback_file = self.backup_dir / "emergency_pre_restore_snapshot.db"
            live_c = sqlite3.connect(self.db_path)
            rb_c = sqlite3.connect(rollback_file)
            live_c.backup(rb_c)
            rb_c.close()
            live_c.close()

            # Corrupt the live database to simulate half-written pages before sudden power kill
            with open(self.db_path, 'r+b') as f:
                f.seek(50)
                f.write(b'CRASHED_INCOMPLETE_PAGES_ZERO_BYTES')

            # Create the .restore_in_progress marker pointing to the rollback snapshot
            maintenance_service.mark_restore_in_progress(rollback_file, target_backup="target.db")
            self.assertTrue(maintenance_service.get_restore_in_progress_file().exists())

        # Simulate fresh application startup after power cut
        fresh_app = create_app('testing')
        fresh_app.config.update({
            'TESTING': True,
            'DATABASE_PATH': self.db_path,
            'BACKUP_FOLDER': str(self.backup_dir)
        })

        with fresh_app.app_context():
            # init_db should detect .restore_in_progress, recover from rollback snapshot, and clear marker
            init_db(fresh_app)

            # Verify marker was removed
            self.assertFalse(maintenance_service.get_restore_in_progress_file().exists(), "Marker should be cleared after recovery")

            # Verify live database is fully operational and recovered
            c = sqlite3.connect(self.db_path).cursor()
            c.execute("PRAGMA integrity_check;")
            self.assertEqual(c.fetchone()[0], 'ok')

            c.execute("SELECT title FROM books WHERE book_code = 'KB-RECOVER-01';")
            row = c.fetchone()
            c.close()
            self.assertIsNotNone(row, "Live database was not recovered from pre-restore snapshot!")
            self.assertEqual(row[0], 'Book Before Crash')

    # -------------------------------------------------------------------------
    # 8. Invalid schema backup rejection (missing tables or columns)
    # -------------------------------------------------------------------------
    def test_08_invalid_schema_backup_rejected_with_exact_missing_columns(self):
        """Backup missing required tables or specific columns is rejected by verify_backup_integrity."""
        with self.app.app_context():
            # Create a backup with missing 'handover_code' in handovers table
            bad_backup_path = self.backup_dir / "kitab_bank_backup_missing_col.db"
            bad_conn = sqlite3.connect(bad_backup_path)
            bad_cur = bad_conn.cursor()

            # Copy all tables from live DB except corrupt handovers schema
            live_c = sqlite3.connect(self.db_path)
            live_c.backup(bad_conn)
            live_c.close()

            # Drop and recreate handovers missing handover_code column
            bad_cur.execute("DROP TABLE handovers;")
            bad_cur.execute(
                """
                CREATE TABLE handovers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    request_id INTEGER NOT NULL,
                    book_id INTEGER NOT NULL,
                    teacher_id INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    handed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """
            )
            bad_conn.commit()
            bad_conn.close()

            # Verify integrity check catches missing handover_code
            is_valid, msg = backup_service.verify_backup_integrity(bad_backup_path)
            self.assertFalse(is_valid, "verify_backup_integrity should reject backup missing handover_code!")
            self.assertIn("handovers", msg)
            self.assertIn("handover_code", msg)

if __name__ == '__main__':
    unittest.main()
