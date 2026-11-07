"""Regression coverage for high-impact audit findings fixed in the audit branch."""

import sqlite3
import tempfile
import threading
import unittest
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

from flask import Flask
from markupsafe import Markup

from app import create_app
from app.database import check_and_recover_interrupted_restore, db_transaction
from app.services import activity_service, maintenance_service, backup_service
from app.services.request_service import create_book_request
from app.services.translation_service import localize_activity_details


class SecurityAndIntegrityRegressionTests(unittest.TestCase):
    def test_activity_log_output_escapes_untrusted_text_in_every_language(self):
        payload = "<img src=x onerror=alert(1)>"
        details = f"Book '{payload}' (KB-BK-000001) added to inventory by Teacher."

        for language in ("en", "ur", "sd"):
            with self.subTest(language=language):
                rendered = localize_activity_details(details, lang=language)
                self.assertIsInstance(rendered, Markup)
                self.assertIn("&lt;img", str(rendered))
                self.assertNotIn("<img", str(rendered))
                if language in ("ur", "sd"):
                    self.assertIn("<bdi", str(rendered))

    def test_activity_logger_does_not_commit_callers_transaction(self):
        db = sqlite3.connect(":memory:")
        db.execute("""
            CREATE TABLE activity_logs (
                id INTEGER PRIMARY KEY,
                action TEXT,
                entity_type TEXT,
                entity_id INTEGER,
                actor_type TEXT,
                actor_name TEXT,
                details TEXT,
                created_at TEXT
            )
        """)
        db.commit()

        try:
            with patch("app.services.activity_service.get_db", return_value=db):
                with self.assertRaisesRegex(RuntimeError, "force rollback"):
                    with db_transaction(db):
                        activity_service.record_activity(
                            "test", "entity", 1, details="Must roll back"
                        )
                        self.assertTrue(db.in_transaction)
                        raise RuntimeError("force rollback")

            count = db.execute("SELECT COUNT(*) FROM activity_logs").fetchone()[0]
            self.assertEqual(count, 0)
        finally:
            db.close()

    def test_transaction_work_block_is_not_replayed_after_operational_error(self):
        db = sqlite3.connect(":memory:")
        executions = []
        try:
            with self.assertRaisesRegex(sqlite3.OperationalError, "database is locked"):
                with db_transaction(db, max_retries=3, initial_delay=0):
                    executions.append("ran")
                    raise sqlite3.OperationalError("database is locked")
            self.assertEqual(executions, ["ran"])
            self.assertFalse(db.in_transaction)
        finally:
            db.close()

    def test_request_rechecks_book_status_inside_write_transaction(self):
        db = sqlite3.connect(":memory:")
        db.row_factory = sqlite3.Row
        db.executescript("""
            CREATE TABLE books (
                id INTEGER PRIMARY KEY,
                book_code TEXT,
                title TEXT,
                status TEXT,
                is_approved INTEGER
            );
            CREATE TABLE requests (
                id INTEGER PRIMARY KEY,
                tracking_code TEXT UNIQUE,
                book_id INTEGER,
                requester_name TEXT,
                requester_class TEXT,
                requester_roll_no TEXT,
                requester_contact TEXT,
                notes TEXT,
                status TEXT
            );
            CREATE TABLE activity_logs (
                id INTEGER PRIMARY KEY,
                action TEXT,
                entity_type TEXT,
                entity_id INTEGER,
                actor_type TEXT,
                actor_name TEXT,
                details TEXT
            );
            INSERT INTO books (id, book_code, title, status, is_approved)
            VALUES (1, 'KB-BK-000001', 'Mathematics', 'available', 1);
        """)
        db.commit()

        @contextmanager
        def reserve_between_initial_read_and_request_write(database):
            # Simulate another teacher transaction winning the reservation
            # after the student's initial catalogue read.
            with db_transaction(database):
                database.execute(
                    "UPDATE books SET status='reserved' WHERE id=1"
                )
            with db_transaction(database):
                yield database

        form = {
            "book_code": "KB-BK-000001",
            "requester_name": "Student Example",
            "requester_class": "Class 6-A",
            "requester_roll_no": "12",
            "requester_contact": "03000000000",
            "notes": ""
        }
        try:
            with patch("app.services.request_service.get_db", return_value=db), patch(
                "app.services.request_service.db_transaction",
                side_effect=reserve_between_initial_read_and_request_write
            ):
                success, code, error = create_book_request(form)

            self.assertFalse(success)
            self.assertIsNone(code)
            self.assertIn("reserved", error)
            self.assertEqual(
                db.execute("SELECT COUNT(*) FROM requests").fetchone()[0],
                0
            )
        finally:
            db.close()

    def test_new_requests_can_register_and_see_maintenance_gate_during_restore(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            lock_file = Path(temp_dir) / ".maintenance_lock"
            entered_restore = threading.Event()
            release_restore = threading.Event()
            request_checked = threading.Event()
            observed = []

            def restore_worker():
                with patch(
                    "app.services.maintenance_service.get_maintenance_file",
                    return_value=lock_file
                ):
                    with maintenance_service.maintenance_context(timeout=1):
                        entered_restore.set()
                        release_restore.wait(2)

            restore_thread = threading.Thread(target=restore_worker)
            restore_thread.start()
            try:
                self.assertTrue(entered_restore.wait(1))

                def incoming_request():
                    with patch(
                        "app.services.maintenance_service.get_maintenance_file",
                        return_value=lock_file
                    ):
                        maintenance_service.register_request("new-request")
                        observed.append(maintenance_service.is_maintenance_active())
                        maintenance_service.unregister_request("new-request")
                        request_checked.set()

                request_thread = threading.Thread(target=incoming_request)
                request_thread.start()
                self.assertTrue(
                    request_checked.wait(1),
                    "New request was blocked by the maintenance state lock"
                )
                request_thread.join(1)
                self.assertEqual(observed, [True])
            finally:
                release_restore.set()
                restore_thread.join(2)
                self.assertFalse(restore_thread.is_alive())

    def test_login_rate_limit_blocks_after_five_failed_attempts(self):
        app = create_app("testing")
        client = app.test_client()

        for attempt in range(5):
            response = client.post(
                "/auth/login",
                data={"username": "teacher", "password": f"wrong-{attempt}"}
            )
            self.assertEqual(response.status_code, 200)

        blocked = client.post(
            "/auth/login",
            data={"username": "teacher", "password": "still-wrong"}
        )
        self.assertEqual(blocked.status_code, 429)

    def test_inventory_cover_rejects_non_image_content_even_with_allowed_extension(self):
        from io import BytesIO
        from werkzeug.datastructures import FileStorage
        from app.services.book_service import save_book_cover_image

        app = create_app("testing")
        with app.app_context():
            upload = FileStorage(
                stream=BytesIO(b"this is not an image"),
                filename="fake.jpg",
                content_type="image/jpeg"
            )
            with self.assertRaises(ValueError):
                save_book_cover_image(upload)

    def test_restore_rejects_path_traversal_filename(self):
        app = create_app("testing")
        with app.app_context():
            success, snapshot, error = backup_service.restore_database_from_backup("../outside.db")
            self.assertFalse(success)
            self.assertIsNone(snapshot)
            self.assertIn("Invalid backup filename", error)

    def test_existing_database_is_recovered_from_interrupted_restore_marker(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            live_db = root / "live.db"
            rollback_db = root / "rollback.db"

            with sqlite3.connect(rollback_db) as conn:
                conn.execute("CREATE TABLE sample (value TEXT)")
                conn.execute("INSERT INTO sample VALUES ('safe snapshot')")

            with sqlite3.connect(live_db) as conn:
                conn.execute("CREATE TABLE sample (value TEXT)")
                conn.execute("INSERT INTO sample VALUES ('partial restore')")

            app = Flask(__name__)
            app.config["DATABASE_PATH"] = live_db
            with app.app_context():
                maintenance_service.mark_restore_in_progress(rollback_db, "target.db")
                self.assertTrue(check_and_recover_interrupted_restore(app))

                with sqlite3.connect(live_db) as conn:
                    value = conn.execute("SELECT value FROM sample").fetchone()[0]
                self.assertEqual(value, "safe snapshot")
                self.assertIsNone(maintenance_service.get_interrupted_restore_info())

    def test_initial_teacher_password_is_confined_to_password_rotation(self):
        app = create_app("testing")
        client = app.test_client()
        response = client.post(
            "/auth/login",
            data={"username": "teacher", "password": app.config["INITIAL_TEACHER_PASSWORD"]}
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("/teacher/settings?tab=security", response.headers["Location"])

        blocked = client.get("/teacher/dashboard")
        self.assertEqual(blocked.status_code, 302)
        self.assertIn("/teacher/settings?tab=security", blocked.headers["Location"])

        rotated = client.post(
            "/teacher/settings/password",
            data={
                "current_password": app.config["INITIAL_TEACHER_PASSWORD"],
                "new_password": "A-Strong-New-Pass-2026!",
                "confirm_password": "A-Strong-New-Pass-2026!"
            }
        )
        self.assertEqual(rotated.status_code, 302)

        allowed = client.get("/teacher/dashboard")
        self.assertEqual(allowed.status_code, 200)


if __name__ == "__main__":
    unittest.main()
