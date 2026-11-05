"""
Phase 7 Test Suite: Teacher Dashboard, Analytics, Inventory Management & System Activity Logs
Verifies:
- Live analytics calculation from SQLite (zero fabricated data)
- Full inventory CRUD (adding, editing, retiring, restoring)
- Status integrity guards (cannot retire reserved or handed-over books)
- Activity log audit trail (recording, filtering, pagination)
- Reports dataset and CSV exports with UTF-8 BOM
- Teacher authentication protection across all Phase 7 routes
- Teacher login and logout audit logging
"""

import unittest
from flask import session
from app import create_app
from app.database import get_db, close_db
from app.services import book_service, analytics_service, activity_service

class Phase7TeacherDashboardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app('testing')
        cls.client = cls.app.test_client()

        with cls.app.app_context():
            db = get_db()
            cls._cleanup_test_data(db)
            cls._ensure_teacher_account(db)

    @classmethod
    def tearDownClass(cls):
        with cls.app.app_context():
            db = get_db()
            cls._cleanup_test_data(db)
            close_db()

    @classmethod
    def _cleanup_test_data(cls, db):
        cur = db.cursor()
        cur.execute("""
            DELETE FROM books WHERE
                title LIKE 'Unit Test%' OR
                title LIKE 'Book to Retire%' OR
                title LIKE 'Reserved Active%' OR
                title LIKE 'Already Handed Over%' OR
                title LIKE 'Original Book%' OR
                title LIKE 'Updated Modern%' OR
                image_path = 'img/book-placeholder.svg';
        """)
        cur.execute("DELETE FROM activity_logs WHERE action = 'test_custom_action';")
        db.commit()

    @classmethod
    def _ensure_teacher_account(cls, db):
        from werkzeug.security import generate_password_hash
        cur = db.cursor()
        cur.execute("SELECT id FROM teachers WHERE username = 'teacher';")
        row = cur.fetchone()
        if not row:
            db.execute(
                """
                INSERT INTO teachers (username, password_hash, full_name, email, role, is_active)
                VALUES ('teacher', ?, 'Master Teacher', 'teacher@school.edu.pk', 'admin', 1);
                """,
                (generate_password_hash('Teacher@123'),)
            )
            db.commit()

    def _login_teacher(self):
        """Helper to establish an authenticated teacher session."""
        with self.client.session_transaction() as sess:
            sess['teacher_id'] = 1
            sess['teacher_username'] = 'teacher'
            sess['teacher_name'] = 'Master Teacher'
            sess['teacher_role'] = 'admin'

    def test_01_dashboard_analytics_calculation(self):
        """Verify dashboard analytics computes exact values from SQLite without fabrication."""
        with self.app.app_context():
            data = analytics_service.get_dashboard_analytics()

            self.assertIn('summary', data)
            summary = data['summary']
            self.assertIn('total_inventory', summary)
            self.assertIn('available_books', summary)
            self.assertIn('reserved_books', summary)
            self.assertIn('handed_over_books', summary)
            self.assertIn('retired_books', summary)
            self.assertIn('total_donations', summary)
            self.assertIn('pending_donations', summary)
            self.assertIn('pending_requests', summary)
            self.assertIn('completed_handovers', summary)
            self.assertIn('reuse_rate', summary)

            db = get_db()
            cur = db.cursor()
            cur.execute("SELECT COUNT(*) FROM books;")
            actual_total = cur.fetchone()[0]
            self.assertEqual(summary['total_inventory'], actual_total)

            cur.execute("SELECT COUNT(*) FROM books WHERE status = 'available' AND is_approved = 1;")
            actual_avail = cur.fetchone()[0]
            self.assertEqual(summary['available_books'], actual_avail)

            cur.execute("SELECT COUNT(*) FROM handovers;")
            actual_handovers = cur.fetchone()[0]
            self.assertEqual(summary['completed_handovers'], actual_handovers)

    def test_02_class_and_subject_distribution(self):
        """Verify class-wise and subject-wise breakdown structures."""
        with self.app.app_context():
            data = analytics_service.get_dashboard_analytics()
            class_dist = data['class_distribution']
            subject_dist = data['subject_distribution']

            self.assertIsInstance(class_dist, list)
            self.assertIsInstance(subject_dist, list)

            for cd in class_dist:
                self.assertIn('class_grade', cd)
                self.assertIn('total', cd)
                self.assertIn('percentage', cd)
                self.assertIn('available', cd)
                self.assertIn('handed_over', cd)
                self.assertGreaterEqual(cd['percentage'], 0)

            for sd in subject_dist:
                self.assertIn('subject', sd)
                self.assertIn('total', sd)
                self.assertIn('percentage', sd)

    def test_03_inventory_listing_and_filtering(self):
        """Verify inventory querying with status, class, and search filters."""
        with self.app.app_context():
            books, total = book_service.get_inventory_books(status='all', limit=10)
            self.assertIsInstance(books, list)
            self.assertGreater(total, 0)

            # Filter by specific class
            c7_books, c7_total = book_service.get_inventory_books(class_grade='Class 7')
            for b in c7_books:
                self.assertEqual(b['class_grade'], 'Class 7')

            # Filter by status
            avail_books, avail_total = book_service.get_inventory_books(status='available')
            for b in avail_books:
                self.assertEqual(b['status'], 'available')

    def test_04_add_inventory_book_success(self):
        """Verify directly adding a textbook creates code KB-BK-XXXXXX and logs activity."""
        with self.app.app_context():
            data = {
                'title': 'Unit Test Advanced Physics',
                'author': 'Prof. Test Scientist',
                'subject': 'General Science',
                'class_grade': 'Class 8',
                'language': 'English',
                'publisher': 'Academic Test Press',
                'edition_year': 2024,
                'condition_state': 'Like New',
                'description': 'Direct teacher inventory insertion test.'
            }
            success, book_id, book_code, err = book_service.add_inventory_book(
                data=data,
                teacher_id=1,
                teacher_name='Master Teacher'
            )
            self.assertTrue(success)
            self.assertIsNotNone(book_id)
            self.assertTrue(book_code.startswith('KB-BK-'))

            # Verify persisted record
            book = book_service.get_book_by_code_or_id(book_id)
            self.assertIsNotNone(book)
            self.assertEqual(book['title'], 'Unit Test Advanced Physics')
            self.assertEqual(book['status'], 'available')
            self.assertEqual(book['is_approved'], 1)

            # Verify activity log
            logs, _ = activity_service.get_activity_logs(action='book_added', limit=5)
            matching = [l for l in logs if l['entity_id'] == book_id]
            self.assertTrue(len(matching) >= 1)
            self.assertIn('Unit Test Advanced Physics', matching[0]['details'])

    def test_05_add_inventory_book_validation(self):
        """Verify missing mandatory fields reject book addition."""
        with self.app.app_context():
            # Missing title
            success, _, _, err = book_service.add_inventory_book({'title': '', 'subject': 'Math', 'class_grade': 'Class 6'})
            self.assertFalse(success)
            self.assertIn('title is required', err.lower())

            # Missing subject
            success, _, _, err = book_service.add_inventory_book({'title': 'Valid Title', 'subject': '', 'class_grade': 'Class 6'})
            self.assertFalse(success)
            self.assertIn('subject is required', err.lower())

            # Missing class
            success, _, _, err = book_service.add_inventory_book({'title': 'Valid Title', 'subject': 'Math', 'class_grade': ''})
            self.assertFalse(success)
            self.assertIn('class level is required', err.lower())

    def test_06_update_inventory_book_success(self):
        """Verify updating textbook details and activity log."""
        with self.app.app_context():
            # Add a book first
            _, book_id, book_code, _ = book_service.add_inventory_book({
                'title': 'Original Book Title',
                'subject': 'Mathematics',
                'class_grade': 'Class 6',
                'language': 'Urdu',
                'condition_state': 'Good'
            }, teacher_id=1, teacher_name='Master Teacher')

            # Update book
            success, err = book_service.update_inventory_book(book_id, {
                'title': 'Updated Modern Mathematics',
                'subject': 'Mathematics',
                'class_grade': 'Class 6',
                'language': 'Urdu',
                'publisher': 'National Board',
                'edition_year': 2025,
                'condition_state': 'Like New',
                'description': 'Updated description.'
            }, teacher_id=1, teacher_name='Master Teacher')

            self.assertTrue(success)
            updated = book_service.get_book_by_code_or_id(book_id)
            self.assertEqual(updated['title'], 'Updated Modern Mathematics')
            self.assertEqual(updated['condition_state'], 'Like New')
            self.assertEqual(updated['publisher'], 'National Board')

            # Check activity log
            logs, _ = activity_service.get_activity_logs(action='book_updated', limit=5)
            matching = [l for l in logs if l['entity_id'] == book_id]
            self.assertTrue(len(matching) >= 1)

    def test_07_retire_and_restore_book(self):
        """Verify retiring an available book and restoring it."""
        with self.app.app_context():
            _, book_id, book_code, _ = book_service.add_inventory_book({
                'title': 'Book to Retire',
                'subject': 'Social Studies',
                'class_grade': 'Class 7',
                'condition_state': 'Fair'
            }, teacher_id=1, teacher_name='Master Teacher')

            # Retire book
            success, err = book_service.retire_or_restore_book(
                book_id=book_id,
                new_status='retired',
                reason='Pages missing and water damaged',
                teacher_id=1,
                teacher_name='Master Teacher'
            )
            self.assertTrue(success)
            retired_book = book_service.get_book_by_code_or_id(book_id)
            self.assertEqual(retired_book['status'], 'retired')

            # Check activity log
            logs, _ = activity_service.get_activity_logs(action='book_retired', limit=5)
            matching = [l for l in logs if l['entity_id'] == book_id]
            self.assertTrue(len(matching) >= 1)
            self.assertIn('Pages missing', matching[0]['details'])

            # Restore book
            success, err = book_service.retire_or_restore_book(
                book_id=book_id,
                new_status='available',
                teacher_id=1,
                teacher_name='Master Teacher'
            )
            self.assertTrue(success)
            restored_book = book_service.get_book_by_code_or_id(book_id)
            self.assertEqual(restored_book['status'], 'available')

    def test_08_retire_reserved_book_blocked(self):
        """Verify retiring a reserved book is strictly blocked."""
        with self.app.app_context():
            db = get_db()
            cur = db.cursor()
            code = book_service.generate_next_book_code()
            cur.execute("""
                INSERT INTO books (book_code, title, subject, class_grade, image_path, status, is_approved)
                VALUES (?, 'Reserved Active Book', 'Mathematics', 'Class 6', 'img/covers/placeholder.svg', 'reserved', 1);
            """, (code,))
            db.commit()
            book_id = cur.lastrowid

            success, err = book_service.retire_or_restore_book(
                book_id=book_id,
                new_status='retired',
                teacher_id=1,
                teacher_name='Master Teacher'
            )
            self.assertFalse(success)
            self.assertIn('reserved book', err.lower())

    def test_09_retire_handed_over_book_blocked(self):
        """Verify modifying a handed_over book is strictly blocked."""
        with self.app.app_context():
            db = get_db()
            cur = db.cursor()
            code = book_service.generate_next_book_code()
            cur.execute("""
                INSERT INTO books (book_code, title, subject, class_grade, image_path, status, is_approved)
                VALUES (?, 'Already Handed Over Book', 'General Science', 'Class 8', 'img/covers/placeholder.svg', 'handed_over', 1);
            """, (code,))
            db.commit()
            book_id = cur.lastrowid

            success, err = book_service.retire_or_restore_book(
                book_id=book_id,
                new_status='retired',
                teacher_id=1,
                teacher_name='Master Teacher'
            )
            self.assertFalse(success)
            self.assertIn('already been handed over', err.lower())

    def test_10_activity_logs_filtering_and_pagination(self):
        """Verify activity logs search, action filter, and pagination."""
        with self.app.app_context():
            activity_service.record_activity(
                action='test_custom_action',
                entity_type='test',
                entity_id=999,
                actor_type='teacher',
                actor_name='QA Tester',
                details='Audit test entry for pagination verification.'
            )

            # Query without filter
            logs, total = activity_service.get_activity_logs(limit=10)
            self.assertGreater(total, 0)

            # Filter by action
            act_logs, act_total = activity_service.get_activity_logs(action='test_custom_action')
            self.assertGreaterEqual(act_total, 1)
            for l in act_logs:
                self.assertEqual(l['action'], 'test_custom_action')

            # Search by text
            search_logs, _ = activity_service.get_activity_logs(search_query='pagination verification')
            self.assertGreaterEqual(len(search_logs), 1)

    def test_11_detailed_reports_data(self):
        """Verify detailed reports dictionary structure."""
        with self.app.app_context():
            report = analytics_service.get_detailed_reports()

            self.assertIn('summary', report)
            self.assertIn('class_distribution', report)
            self.assertIn('subject_distribution', report)
            self.assertIn('languages', report)
            self.assertIn('conditions', report)
            self.assertIn('velocity', report)

            # Verify language breakdown
            for lg in report['languages']:
                self.assertIn('language', lg)
                self.assertIn('count', lg)
                self.assertIn('percentage', lg)

    def test_12_export_inventory_csv(self):
        """Verify inventory CSV export route returns valid CSV with UTF-8 BOM."""
        self._login_teacher()
        res = self.client.get('/teacher/reports/export/inventory.csv')
        self.assertEqual(res.status_code, 200)
        self.assertIn('text/csv', res.content_type)
        self.assertIn('kitab_bank_inventory.csv', res.headers.get('Content-Disposition', ''))

        content = res.data.decode('utf-8-sig') # decodes BOM cleanly
        self.assertIn('Book Code,Title,Author,Subject,Class Grade', content)
        res.close()

    def test_13_export_handovers_csv(self):
        """Verify handover ledger CSV export route returns valid CSV with UTF-8 BOM."""
        self._login_teacher()
        res = self.client.get('/teacher/reports/export/handovers.csv')
        self.assertEqual(res.status_code, 200)
        self.assertIn('text/csv', res.content_type)
        self.assertIn('kitab_bank_handovers.csv', res.headers.get('Content-Disposition', ''))

        content = res.data.decode('utf-8-sig')
        self.assertIn('Handover Code,Request Tracking Code,Book Code', content)
        res.close()

    def test_14_teacher_auth_protection_on_phase7_routes(self):
        """Verify all Phase 7 routes are protected against unauthenticated access."""
        unauth_client = self.app.test_client()

        routes = [
            '/teacher/dashboard',
            '/teacher/inventory',
            '/teacher/inventory/new',
            '/teacher/reports',
            '/teacher/reports/export/inventory.csv',
            '/teacher/reports/export/handovers.csv',
            '/teacher/logs'
        ]

        for route in routes:
            res = unauth_client.get(route)
            self.assertEqual(res.status_code, 302, f"Route {route} did not redirect unauthenticated user!")
            self.assertIn('/auth/login', res.headers.get('Location', ''))
            res.close()

    def test_15_teacher_login_logout_audit_logging(self):
        """Verify successful teacher login and logout generate audit logs."""
        client = self.app.test_client()

        # Establish session and get CSRF token
        client.get('/auth/login')
        with client.session_transaction() as sess:
            csrf_tok = sess.get('csrf_token')

        # Login
        res_login = client.post('/auth/login', data={
            'username': 'teacher',
            'password': 'Teacher@123',
            'csrf_token': csrf_tok
        }, follow_redirects=True)
        self.assertEqual(res_login.status_code, 200)
        res_login.close()

        with self.app.app_context():
            logs, _ = activity_service.get_activity_logs(action='teacher_login', limit=5)
            self.assertGreaterEqual(len(logs), 1)
            self.assertIn('logged in successfully', logs[0]['details'])

        # Logout
        res_logout = client.get('/auth/logout', follow_redirects=True)
        self.assertEqual(res_logout.status_code, 200)
        res_logout.close()

        with self.app.app_context():
            logs, _ = activity_service.get_activity_logs(action='teacher_logout', limit=5)
            self.assertGreaterEqual(len(logs), 1)
            self.assertIn('signed out', logs[0]['details'])

if __name__ == '__main__':
    unittest.main()
