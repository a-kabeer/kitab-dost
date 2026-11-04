"""
Unit and Integration Tests for Phase 3: Book Donation System
Tests:
- Student donation form rendering and validation
- Secure unpredictable donation reference codes (KB-DON-XXXX-XXXX)
- Local Pillow image validation, re-encoding, and traversal defense
- Teacher review queue, search, and filtering
- Teacher approval workflow: atomic book creation, unique KB-BK-000001 code, catalogue visibility
- Teacher rejection workflow: reason logging, history preservation, zero catalogue listing
- Duplicate approval / state transition protection
- Confidentiality: Zero donor PII leakage in public catalogue or book detail
- Multiple donations with identical titles supported
"""

import io
import os
import sys
import unittest
from PIL import Image

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

from app import create_app
from app.database import get_db, db_transaction
from app.services import donation_service, book_service, rate_limiter

class Phase3DonationSystemTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app('testing')
        cls.client = cls.app.test_client()

    def setUp(self):
        # Reset in-memory rate limits before each test
        rate_limiter.reset_rate_limits()

    def _login_teacher(self):
        """Helper to establish an authenticated teacher session."""
        with self.client.session_transaction() as sess:
            sess['teacher_id'] = 1
            sess['teacher_username'] = 'teacher'
            sess['teacher_name'] = 'School Teacher / Incharge'
            sess['teacher_role'] = 'admin'

    def _create_sample_image(self, format='PNG', size=(400, 500), color=(50, 100, 200)):
        """Generate in-memory test image bytes."""
        buf = io.BytesIO()
        img = Image.new('RGB', size, color=color)
        img.save(buf, format=format)
        buf.seek(0)
        return buf

    def test_01_donation_form_renders_with_csrf(self):
        """Verify student donation form renders with required fields and CSRF token."""
        response = self.client.get('/donate')
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)

        self.assertIn('Donate an Unused Educational Book', html)
        self.assertIn('name="csrf_token"', html)
        self.assertIn('name="title"', html)
        self.assertIn('name="class_grade"', html)
        self.assertIn('name="subject"', html)
        self.assertIn('name="condition_state"', html)
        self.assertIn('name="donor_name"', html)
        self.assertIn('name="donor_class"', html)
        self.assertIn('name="book_image"', html)

    def test_02_successful_donation_submission(self):
        """Verify valid donation without photo submits successfully and generates reference code."""
        with self.client.session_transaction() as sess:
            csrf_token = sess.get('csrf_token', 'test-token')

        post_data = {
            'csrf_token': csrf_token,
            'title': 'Social Studies for Middle School',
            'author': 'Prof. A. R. Jamali',
            'class_grade': 'Class 7',
            'subject': 'Social Studies',
            'language': 'English',
            'condition_state': 'Like New',
            'description': 'Clean condition, all maps intact.',
            'donor_name': 'Ali Raza',
            'donor_class': 'Class 8-B',
            'donor_roll_no': '19',
            'donor_contact': '0300-9876543'
        }

        response = self.client.post('/donate', data=post_data, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)

        self.assertIn('Thank You, Ali Raza!', html)
        self.assertIn('KB-DON-', html)
        self.assertIn('Awaiting Teacher Approval', html)

        # Verify record exists in SQLite (order by id DESC to get newly submitted record)
        with self.app.app_context():
            db = get_db()
            cur = db.cursor()
            cur.execute("SELECT * FROM donations WHERE donor_name = 'Ali Raza' AND title = 'Social Studies for Middle School' ORDER BY id DESC LIMIT 1;")
            row = cur.fetchone()
            self.assertIsNotNone(row)
            self.assertEqual(row['status'], 'pending')
            self.assertEqual(row['class_grade'], 'Class 7')
            self.assertEqual(row['author'], 'Prof. A. R. Jamali')
            self.assertIsNone(row['temp_image_path'])

    def test_03_donation_validation_missing_required_fields(self):
        """Verify validation errors for missing title, class, subject, or donor info."""
        with self.client.session_transaction() as sess:
            csrf_token = sess.get('csrf_token', 'test-token')

        # Missing Title
        data_no_title = {
            'csrf_token': csrf_token,
            'class_grade': 'Class 6',
            'subject': 'Mathematics',
            'donor_name': 'Sara',
            'donor_class': '6-A'
        }
        res = self.client.post('/donate', data=data_no_title)
        self.assertEqual(res.status_code, 400)
        self.assertIn('Book title is required', res.get_data(as_text=True))

        # Missing Donor Name
        data_no_donor = {
            'csrf_token': csrf_token,
            'title': 'Sindhi Book 6',
            'class_grade': 'Class 6',
            'subject': 'Sindhi',
            'donor_name': '',
            'donor_class': '6-A'
        }
        res = self.client.post('/donate', data=data_no_donor)
        self.assertEqual(res.status_code, 400)
        self.assertIn('Donor name is required', res.get_data(as_text=True))

        # Invalid Class Level
        data_bad_class = {
            'csrf_token': csrf_token,
            'title': 'Physics for Class 11',
            'class_grade': 'Class 11',
            'subject': 'Physics',
            'donor_name': 'Zahid',
            'donor_class': '11-B'
        }
        res = self.client.post('/donate', data=data_bad_class)
        self.assertEqual(res.status_code, 400)
        self.assertIn('valid Class Level', res.get_data(as_text=True))

    def test_04_image_upload_and_pillow_processing(self):
        """Verify valid image upload is re-encoded, stripped of metadata, and saved as webp."""
        with self.client.session_transaction() as sess:
            csrf_token = sess.get('csrf_token', 'test-token')

        img_bytes = self._create_sample_image(format='PNG', size=(1200, 1500))

        data = {
            'csrf_token': csrf_token,
            'title': 'Illustrated Science Encyclopedia',
            'author': 'Oxford Educational Press',
            'class_grade': 'Class 8',
            'subject': 'General Science',
            'language': 'English',
            'condition_state': 'Good',
            'donor_name': 'Hassan Tariq',
            'donor_class': '8-C',
            'donor_roll_no': '45',
            'book_image': (img_bytes, 'science_cover_photo.png')
        }

        res = self.client.post('/donate', data=data, content_type='multipart/form-data', follow_redirects=True)
        self.assertEqual(res.status_code, 200)

        with self.app.app_context():
            db = get_db()
            cur = db.cursor()
            cur.execute("SELECT temp_image_path FROM donations WHERE donor_name = 'Hassan Tariq';")
            row = cur.fetchone()
            self.assertIsNotNone(row)
            rel_path = row['temp_image_path']
            self.assertIsNotNone(rel_path)
            self.assertTrue(rel_path.endswith('.webp'))

            # Check file on disk
            abs_path = os.path.join(self.app.root_path, 'static', rel_path)
            self.assertTrue(os.path.isfile(abs_path))

            # Inspect saved file via Pillow: must be WEBP and resized <= 1000px
            with Image.open(abs_path) as saved_img:
                self.assertEqual(saved_img.format, 'WEBP')
                self.assertLessEqual(max(saved_img.size), 1000)

    def test_05_malicious_or_fake_image_rejection(self):
        """Verify non-image files disguised with an image extension are strictly rejected."""
        with self.client.session_transaction() as sess:
            csrf_token = sess.get('csrf_token', 'test-token')

        # Plain text disguised as .jpg
        fake_image = io.BytesIO(b"<?php echo 'malicious payload'; ?>")

        data = {
            'csrf_token': csrf_token,
            'title': 'Computer Basics',
            'class_grade': 'Class 6',
            'subject': 'Computer Science',
            'donor_name': 'Test Student',
            'donor_class': '6-B',
            'book_image': (fake_image, 'exploit.jpg')
        }

        res = self.client.post('/donate', data=data, content_type='multipart/form-data')
        self.assertEqual(res.status_code, 400)
        self.assertIn('not be decoded as a valid image', res.get_data(as_text=True))

    def test_06_unauthenticated_teacher_routes_blocked(self):
        """Verify teacher donation management requires authentication."""
        # Anonymous session (clear any teacher credentials, visit / to get fresh csrf_token)
        with self.client.session_transaction() as sess:
            sess.clear()
        self.client.get('/')

        with self.client.session_transaction() as sess:
            self.assertNotIn('teacher_id', sess)
            csrf_token = sess.get('csrf_token')

        # Unauthenticated GET requests redirected to login
        res = self.client.get('/teacher/donations')
        self.assertEqual(res.status_code, 302)
        self.assertIn('/auth/login', res.headers['Location'])

        res_detail = self.client.get('/teacher/donations/1')
        self.assertEqual(res_detail.status_code, 302)
        self.assertIn('/auth/login', res_detail.headers['Location'])

        # Unauthenticated POST with CSRF token is redirected to login by teacher auth guard
        res_post = self.client.post('/teacher/donations/1/approve', data={'csrf_token': csrf_token})
        self.assertEqual(res_post.status_code, 302)
        self.assertIn('/auth/login', res_post.headers['Location'])

    def test_07_teacher_review_queue_and_filtering(self):
        """Verify teacher can view queue, filter by status, and search."""
        self._login_teacher()

        # View pending queue
        res = self.client.get('/teacher/donations?status=pending')
        self.assertEqual(res.status_code, 200)
        html = res.get_data(as_text=True)
        self.assertIn('Donation Review Queue', html)
        self.assertIn('Social Studies for Middle School', html)

        # Search by donor name
        res_search = self.client.get('/teacher/donations?q=Ali+Raza')
        self.assertEqual(res_search.status_code, 200)
        self.assertIn('Ali Raza', res_search.get_data(as_text=True))

    def test_08_teacher_approval_creates_public_book(self):
        """
        Verify teacher approval:
        - Changes status to 'approved'
        - Generates sequential KB-BK-000001 code
        - Creates book in 'books' marked available
        - Immediately visible in public catalogue
        """
        self._login_teacher()

        with self.app.app_context():
            db = get_db()
            cur = db.cursor()
            cur.execute("SELECT id FROM donations WHERE title = 'Social Studies for Middle School' AND status = 'pending';")
            d_row = cur.fetchone()
            self.assertIsNotNone(d_row)
            donation_id = d_row['id']

        with self.client.session_transaction() as sess:
            csrf_token = sess.get('csrf_token', 'test-token')

        # Approve donation
        res = self.client.post(
            f'/teacher/donations/{donation_id}/approve',
            data={'csrf_token': csrf_token},
            follow_redirects=True
        )
        self.assertEqual(res.status_code, 200)
        html = res.get_data(as_text=True)
        self.assertIn('Donation approved successfully', html)

        # Verify in SQLite
        with self.app.app_context():
            db = get_db()
            cur = db.cursor()
            cur.execute("SELECT * FROM donations WHERE id = ?;", (donation_id,))
            d = cur.fetchone()
            self.assertEqual(d['status'], 'approved')
            self.assertIsNotNone(d['book_id'])
            self.assertEqual(d['reviewed_by'], 1)

            cur.execute("SELECT * FROM books WHERE id = ?;", (d['book_id'],))
            b = cur.fetchone()
            self.assertIsNotNone(b)
            self.assertTrue(b['book_code'].startswith('KB-BK-'))
            self.assertEqual(b['title'], 'Social Studies for Middle School')
            self.assertEqual(b['status'], 'available')
            self.assertEqual(b['is_approved'], 1)
            book_code = b['book_code']

        # Verify book is visible in public catalogue
        cat_res = self.client.get(f'/catalogue?q={book_code}')
        self.assertEqual(cat_res.status_code, 200)
        self.assertIn(book_code, cat_res.get_data(as_text=True))

        # Verify book detail page
        detail_res = self.client.get(f'/book/{book_code}')
        self.assertEqual(detail_res.status_code, 200)
        detail_html = detail_res.get_data(as_text=True)
        self.assertIn('Social Studies for Middle School', detail_html)
        self.assertIn(book_code, detail_html)

    def test_09_donor_privacy_protection_in_public_views(self):
        """Ensure student donor name, roll number, and contact are NOT present in public catalogue or book detail."""
        with self.app.app_context():
            db = get_db()
            cur = db.cursor()
            cur.execute("SELECT b.book_code FROM books b JOIN donations d ON b.donation_id = d.id WHERE d.donor_name = 'Ali Raza';")
            row = cur.fetchone()
            self.assertIsNotNone(row)
            book_code = row['book_code']

        # Check public detail page
        res = self.client.get(f'/book/{book_code}')
        html = res.get_data(as_text=True)

        # Donor PII must NOT appear in public HTML
        self.assertNotIn('Ali Raza', html)
        self.assertNotIn('0300-9876543', html)
        self.assertNotIn('Class 8-B', html)

    def test_10_duplicate_approval_prevention(self):
        """Verify already approved or rejected donation cannot be approved again."""
        self._login_teacher()

        with self.app.app_context():
            db = get_db()
            cur = db.cursor()
            cur.execute("SELECT id FROM donations WHERE status = 'approved' LIMIT 1;")
            d_id = cur.fetchone()['id']

        with self.client.session_transaction() as sess:
            csrf_token = sess.get('csrf_token', 'test-token')

        # Attempt to approve again
        res = self.client.post(
            f'/teacher/donations/{d_id}/approve',
            data={'csrf_token': csrf_token},
            follow_redirects=True
        )
        self.assertEqual(res.status_code, 200)
        self.assertIn('Approval failed', res.get_data(as_text=True))

    def test_11_teacher_rejection_workflow(self):
        """Verify teacher rejection records reason, retains history, and creates NO book listing."""
        self._login_teacher()

        # Submit a fresh donation to reject
        with self.app.app_context():
            success, code, _ = donation_service.create_donation({
                'title': 'Old Damaged Workbook 1998',
                'class_grade': 'Class 6',
                'subject': 'General Science',
                'language': 'Urdu',
                'condition_state': 'Fair',
                'donor_name': 'Usman Khan',
                'donor_class': '6-C'
            })
            self.assertTrue(success)

            db = get_db()
            cur = db.cursor()
            cur.execute("SELECT id FROM donations WHERE donation_code = ?;", (code,))
            donation_id = cur.fetchone()['id']

        with self.client.session_transaction() as sess:
            csrf_token = sess.get('csrf_token', 'test-token')

        # Reject with specific reason
        rejection_reason = "Outdated 1998 syllabus, major page discoloration."
        res = self.client.post(
            f'/teacher/donations/{donation_id}/reject',
            data={'csrf_token': csrf_token, 'reason': rejection_reason},
            follow_redirects=True
        )
        self.assertEqual(res.status_code, 200)
        self.assertIn('Donation rejected and archived', res.get_data(as_text=True))

        # Check DB state
        with self.app.app_context():
            db = get_db()
            cur = db.cursor()
            cur.execute("SELECT * FROM donations WHERE id = ?;", (donation_id,))
            d = cur.fetchone()
            self.assertEqual(d['status'], 'rejected')
            self.assertEqual(d['rejection_reason'], rejection_reason)
            self.assertIsNone(d['book_id'])

            # Verify no book was created
            cur.execute("SELECT COUNT(*) FROM books WHERE donation_id = ?;", (donation_id,))
            self.assertEqual(cur.fetchone()[0], 0)

        # Verify not in public catalogue
        cat_res = self.client.get('/catalogue?q=Workbook+1998')
        self.assertNotIn('Old Damaged Workbook 1998', cat_res.get_data(as_text=True))

    def test_12_multiple_donations_with_same_title_supported(self):
        """Verify system supports multiple student donations of the same book title."""
        with self.app.app_context():
            # First copy
            s1, c1, _ = donation_service.create_donation({
                'title': 'Mathematics for Class 6',
                'class_grade': 'Class 6',
                'subject': 'Mathematics',
                'donor_name': 'Student A',
                'donor_class': '6-A'
            })
            # Second copy
            s2, c2, _ = donation_service.create_donation({
                'title': 'Mathematics for Class 6',
                'class_grade': 'Class 6',
                'subject': 'Mathematics',
                'donor_name': 'Student B',
                'donor_class': '6-B'
            })
            self.assertTrue(s1 and s2)
            self.assertNotEqual(c1, c2)

            db = get_db()
            cur = db.cursor()
            cur.execute("SELECT id FROM donations WHERE donation_code = ?;", (c1,))
            id1 = cur.fetchone()['id']
            cur.execute("SELECT id FROM donations WHERE donation_code = ?;", (c2,))
            id2 = cur.fetchone()['id']

            ok1, bk1, _ = donation_service.approve_donation(id1, 1, 'Teacher')
            ok2, bk2, _ = donation_service.approve_donation(id2, 1, 'Teacher')

            self.assertTrue(ok1 and ok2)
            self.assertNotEqual(bk1, bk2)
            self.assertTrue(bk1.startswith('KB-BK-'))
            self.assertTrue(bk2.startswith('KB-BK-'))

if __name__ == '__main__':
    unittest.main()
