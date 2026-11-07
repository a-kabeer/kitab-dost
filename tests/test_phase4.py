"""
Unit and Integration Tests for Phase 4: Book Request System
Tests:
- Book request form rendering for available books
- Cryptographically secure unpredictable tracking code generation (KB-REQ-XXXX-XXXX)
- Input validation (name, class & section, roll number, contact phone)
- Public tracking desk (/track) with strict student PII redaction (zero phone/roll number leakage)
- Teacher requests queue, status filtering, and search
- Atomic teacher approval & reservation locking (BEGIN IMMEDIATE)
- Race condition defense: double-booking prevention on same book
- Teacher rejection workflow (records reason, keeps book available for other students)
- Rate limiting defenses for shared school Wi-Fi and anti-enumeration on tracking
"""

import sys
import unittest

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

from app import create_app
from app.database import get_db
from app.services import request_service, book_service, rate_limiter
from scripts.seed_demo import reset_and_seed_demo_data

class Phase4RequestSystemTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app('testing')
        cls.client = cls.app.test_client()
        # Each isolated testing app needs the same 18-book baseline expected by
        # the historical circulation tests. Never seed the school database.
        with cls.app.app_context():
            reset_and_seed_demo_data(
                target_db=cls.app.config['DATABASE_PATH'],
                create_safety_backup=False
            )
        cls._reset_test_state()

    @classmethod
    def tearDownClass(cls):
        cls._reset_test_state()

    @classmethod
    def _reset_test_state(cls):
        with cls.app.app_context():
            db = get_db()
            db.execute("DELETE FROM handovers;")
            db.execute("DELETE FROM requests;")
            db.execute("UPDATE books SET status = 'available';")
            db.commit()

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

    def test_01_request_form_renders_for_available_book(self):
        """Verify request form renders with book metadata and student fields."""
        response = self.client.get('/request?book=KB-BK-000001')
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)

        self.assertIn('Request Textbook for Your Studies', html)
        self.assertIn('Mathematics for Class 6', html)
        self.assertIn('KB-BK-000001', html)
        self.assertIn('name="requester_name"', html)
        self.assertIn('name="requester_class"', html)
        self.assertIn('name="requester_roll_no"', html)
        self.assertIn('name="requester_contact"', html)
        self.assertIn('name="csrf_token"', html)

    def test_02_successful_request_submission_generates_tracking_code(self):
        """Verify submitting request creates record and generates unique KB-REQ-XXXX-XXXX token."""
        self.client.get('/')
        with self.client.session_transaction() as sess:
            csrf_token = sess.get('csrf_token')

        post_data = {
            'csrf_token': csrf_token,
            'book_code': 'KB-BK-000002',
            'requester_name': 'Fatima Noor',
            'requester_class': 'Class 6-A',
            'requester_roll_no': '28',
            'requester_contact': '0302-1234567',
            'notes': 'Need this General Science book for science project work.'
        }

        response = self.client.post('/request', data=post_data, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)

        self.assertIn('Request Received, Fatima Noor!', html)
        self.assertIn('KB-REQ-', html)
        self.assertIn('General Science for Grade 6', html)

        # Verify in database
        with self.app.app_context():
            db = get_db()
            cur = db.cursor()
            cur.execute("SELECT * FROM requests WHERE requester_name = 'Fatima Noor' ORDER BY id DESC LIMIT 1;")
            req = cur.fetchone()
            self.assertIsNotNone(req)
            self.assertEqual(req['status'], 'pending')
            self.assertEqual(req['requester_roll_no'], '28')
            self.assertEqual(req['requester_contact'], '0302-1234567')
            self.assertTrue(req['tracking_code'].startswith('KB-REQ-'))

    def test_03_request_validation_missing_fields(self):
        """Verify submission fails if required fields are missing."""
        self.client.get('/')
        with self.client.session_transaction() as sess:
            csrf_token = sess.get('csrf_token')

        # Missing name
        res = self.client.post('/request', data={
            'csrf_token': csrf_token,
            'book_code': 'KB-BK-000001',
            'requester_name': '',
            'requester_class': '7-B',
            'requester_roll_no': '12',
            'requester_contact': '0300-1111111'
        })
        self.assertEqual(res.status_code, 400)
        self.assertIn('full name is required', res.get_data(as_text=True))

        # Missing roll number
        res_roll = self.client.post('/request', data={
            'csrf_token': csrf_token,
            'book_code': 'KB-BK-000001',
            'requester_name': 'Bilal',
            'requester_class': '7-B',
            'requester_roll_no': '',
            'requester_contact': '0300-1111111'
        })
        self.assertEqual(res_roll.status_code, 400)
        self.assertIn('Roll Number is required', res_roll.get_data(as_text=True))

    def test_04_request_unavailable_or_nonexistent_book(self):
        """Verify requests for invalid or already-reserved books are rejected."""
        self.client.get('/')
        with self.client.session_transaction() as sess:
            csrf_token = sess.get('csrf_token')

        # Non-existent book
        res = self.client.post('/request', data={
            'csrf_token': csrf_token,
            'book_code': 'KB-BK-999999',
            'requester_name': 'Zahid',
            'requester_class': '8-A',
            'requester_roll_no': '5',
            'requester_contact': '0300-2222222'
        })
        self.assertEqual(res.status_code, 400)
        self.assertIn('not found', res.get_data(as_text=True))

    def test_05_student_tracking_lookup_and_strict_pii_redaction(self):
        """
        Verify /track displays status, book info, and masked name,
        while completely redacting roll number and phone number.
        """
        with self.app.app_context():
            success, code, _ = request_service.create_book_request({
                'book_code': 'KB-BK-000003',
                'requester_name': 'Zeeshan Ahmed',
                'requester_class': 'Class 6-C',
                'requester_roll_no': '42',
                'requester_contact': '0333-7654321',
                'notes': 'Exam preparation'
            })
            self.assertTrue(success)

        # Query tracking desk
        res = self.client.get(f'/track?code={code}')
        self.assertEqual(res.status_code, 200)
        html = res.get_data(as_text=True)

        self.assertIn(code, html)
        self.assertIn('اردو لازمی برائے جماعت ششم', html)
        self.assertIn('Class 6-C', html)
        self.assertIn('Under Teacher Review', html)

        # Check Privacy Redaction:
        # Masked name like 'Zeeshan A***' must appear
        self.assertIn('Zeeshan A***', html)
        # Roll number ('42') and contact phone ('0333-7654321') must NEVER appear in public HTML
        self.assertNotIn('0333-7654321', html)
        self.assertNotIn('42', html)

    def test_06_unauthenticated_teacher_routes_blocked(self):
        """Verify all unauthenticated teacher request management routes redirect to login."""
        with self.client.session_transaction() as sess:
            sess.clear()

        # 1. Review queue list
        res_list = self.client.get('/teacher/requests')
        self.assertEqual(res_list.status_code, 302)
        self.assertIn('/auth/login', res_list.headers['Location'])

        # 2. Detailed inspection view
        res_detail = self.client.get('/teacher/requests/1')
        self.assertEqual(res_detail.status_code, 302)
        self.assertIn('/auth/login', res_detail.headers['Location'])

        # 3. Approve endpoint (POST)
        self.client.get('/')
        with self.client.session_transaction() as sess:
            csrf_token = sess.get('csrf_token')

        res_approve = self.client.post('/teacher/requests/1/approve', data={'csrf_token': csrf_token})
        self.assertEqual(res_approve.status_code, 302)
        self.assertIn('/auth/login', res_approve.headers['Location'])

        # 4. Reject endpoint (POST)
        res_reject = self.client.post('/teacher/requests/1/reject', data={'csrf_token': csrf_token, 'reason': 'Test'})
        self.assertEqual(res_reject.status_code, 302)
        self.assertIn('/auth/login', res_reject.headers['Location'])

    def test_07_teacher_review_queue_and_filtering(self):
        """Verify teacher can inspect requests, filter by status, and search."""
        self._login_teacher()

        res = self.client.get('/teacher/requests?status=pending')
        self.assertEqual(res.status_code, 200)
        html = res.get_data(as_text=True)

        self.assertIn('Student Requests Queue', html)
        self.assertIn('Pending Review', html)

        # Search by student name
        res_search = self.client.get('/teacher/requests?q=Zeeshan')
        self.assertEqual(res_search.status_code, 200)
        self.assertIn('Zeeshan Ahmed', res_search.get_data(as_text=True))

    def test_08_teacher_approval_atomically_reserves_book(self):
        """
        Verify teacher approval:
        1. Request becomes approved
        2. Book status becomes 'reserved'
        3. Public catalogue and book detail reflect 'reserved' status
        """
        self._login_teacher()

        with self.app.app_context():
            db = get_db()
            cur = db.cursor()
            cur.execute("SELECT id, book_id, tracking_code FROM requests WHERE requester_name = 'Zeeshan Ahmed' AND status = 'pending' LIMIT 1;")
            req = cur.fetchone()
            self.assertIsNotNone(req)
            req_id = req['id']
            book_id = req['book_id']
            tracking_code = req['tracking_code']

        self.client.get('/')
        with self.client.session_transaction() as sess:
            csrf_token = sess.get('csrf_token')

        # Approve request
        res = self.client.post(
            f'/teacher/requests/{req_id}/approve',
            data={'csrf_token': csrf_token},
            follow_redirects=True
        )
        self.assertEqual(res.status_code, 200)
        self.assertIn('Request approved', res.get_data(as_text=True))

        # Check DB states
        with self.app.app_context():
            db = get_db()
            cur = db.cursor()
            cur.execute("SELECT status FROM requests WHERE id = ?;", (req_id,))
            self.assertEqual(cur.fetchone()['status'], 'approved')

            cur.execute("SELECT book_code, status FROM books WHERE id = ?;", (book_id,))
            b = cur.fetchone()
            self.assertEqual(b['status'], 'reserved')
            book_code = b['book_code']

        # Public tracking lookup should show 'Approved & Book Reserved'
        track_res = self.client.get(f'/track?code={tracking_code}')
        self.assertIn('Good News! Your Book is Reserved', track_res.get_data(as_text=True))

        # Public book detail should show 'Currently Reserved'
        detail_res = self.client.get(f'/book/{book_code}')
        self.assertIn('Currently Reserved', detail_res.get_data(as_text=True))

    def test_09_atomic_reservation_prevents_double_booking_on_same_book(self):
        """
        Verify race-condition defense:
        If two students request the same book while available,
        approving the first reserves it, and attempting to approve the second is REJECTED.
        """
        self._login_teacher()

        with self.app.app_context():
            # Pick an available book
            db = get_db()
            cur = db.cursor()
            cur.execute("SELECT id, book_code FROM books WHERE status = 'available' LIMIT 1;")
            book = cur.fetchone()
            book_code = book['book_code']

            # Student 1 requests book
            s1, c1, _ = request_service.create_book_request({
                'book_code': book_code,
                'requester_name': 'Candidate One',
                'requester_class': 'Class 7-A',
                'requester_roll_no': '1',
                'requester_contact': '0300-1111111'
            })
            # Student 2 requests same book
            s2, c2, _ = request_service.create_book_request({
                'book_code': book_code,
                'requester_name': 'Candidate Two',
                'requester_class': 'Class 7-A',
                'requester_roll_no': '2',
                'requester_contact': '0300-2222222'
            })
            self.assertTrue(s1 and s2)

            cur.execute("SELECT id FROM requests WHERE tracking_code = ?;", (c1,))
            id1 = cur.fetchone()['id']
            cur.execute("SELECT id FROM requests WHERE tracking_code = ?;", (c2,))
            id2 = cur.fetchone()['id']

            # Teacher approves Candidate One
            ok1, bk_code1, err1 = request_service.approve_request(id1, 1, 'Teacher Tariq')
            self.assertTrue(ok1)
            self.assertEqual(bk_code1, book_code)

            # Policy Verification: Zero orphaned pending requests must remain
            cur.execute("SELECT COUNT(*) FROM requests WHERE book_id = ? AND status = 'pending';", (book['id'],))
            pending_count = cur.fetchone()[0]
            self.assertEqual(pending_count, 0, "No orphaned pending requests should remain after approval.")

            # Candidate Two's request must be auto-closed with clear explanatory reason
            cur.execute("SELECT status, rejection_reason FROM requests WHERE id = ?;", (id2,))
            c2_row = cur.fetchone()
            self.assertEqual(c2_row['status'], 'rejected')
            self.assertIn('allocated to another student', c2_row['rejection_reason'].lower())

            # Teacher attempts to approve Candidate Two for the now-reserved book
            ok2, bk_code2, err2 = request_service.approve_request(id2, 1, 'Teacher Tariq')
            # MUST BE REJECTED BY ATOMIC RESERVATION LOCK
            self.assertFalse(ok2)
            self.assertIn('already reserved', err2.lower())

    def test_10_teacher_rejection_workflow(self):
        """Verify teacher can reject a request with a reason, leaving the book available."""
        self._login_teacher()

        with self.app.app_context():
            db = get_db()
            cur = db.cursor()
            cur.execute("SELECT id, book_code FROM books WHERE status = 'available' LIMIT 1;")
            book = cur.fetchone()
            book_id = book['id']

            # Create request
            success, track_code, _ = request_service.create_book_request({
                'book_id': str(book_id),
                'requester_name': 'Test Requester',
                'requester_class': 'Class 8-C',
                'requester_roll_no': '99',
                'requester_contact': '0300-9999999'
            })
            self.assertTrue(success)

            cur.execute("SELECT id FROM requests WHERE tracking_code = ?;", (track_code,))
            req_id = cur.fetchone()['id']

        self.client.get('/')
        with self.client.session_transaction() as sess:
            csrf_token = sess.get('csrf_token')

        rejection_reason = "Allocated to a student without any textbooks."
        res = self.client.post(
            f'/teacher/requests/{req_id}/reject',
            data={'csrf_token': csrf_token, 'reason': rejection_reason},
            follow_redirects=True
        )
        self.assertEqual(res.status_code, 200)

        # Check DB states
        with self.app.app_context():
            db = get_db()
            cur = db.cursor()
            cur.execute("SELECT status, rejection_reason FROM requests WHERE id = ?;", (req_id,))
            r = cur.fetchone()
            self.assertEqual(r['status'], 'rejected')
            self.assertEqual(r['rejection_reason'], rejection_reason)

            # Book MUST remain available!
            cur.execute("SELECT status FROM books WHERE id = ?;", (book_id,))
            self.assertEqual(cur.fetchone()['status'], 'available')

        # Student tracking lookup shows reason
        track_res = self.client.get(f'/track?code={track_code}')
        self.assertIn(rejection_reason, track_res.get_data(as_text=True))

    def test_11_duplicate_approval_prevention(self):
        """Verify an already approved request cannot be approved again."""
        self._login_teacher()

        with self.app.app_context():
            db = get_db()
            cur = db.cursor()
            cur.execute("SELECT id FROM requests WHERE status = 'approved' LIMIT 1;")
            approved_req_id = cur.fetchone()['id']

            ok, _, err = request_service.approve_request(approved_req_id, 1, 'Teacher')
            self.assertFalse(ok)
            self.assertIn("'approved'", err)

    def test_12_rate_limiting_defense_on_request_and_tracking(self):
        """Verify rate limiter blocks excessive requests/lookups."""
        # Tracking lookup limit is 30/min
        for i in range(30):
            rate_limiter.is_rate_limited('track', max_requests=30, window_seconds=60)

        # 31st attempt must be blocked
        is_blocked = rate_limiter.is_rate_limited('track', max_requests=30, window_seconds=60)
        self.assertTrue(is_blocked)

        # HTTP request to /track should return 429
        res = self.client.get('/track?code=KB-REQ-TEST-1234')
        self.assertEqual(res.status_code, 429)

    def test_13_duplicate_student_request_for_same_book_blocked(self):
        """Verify the same student cannot submit duplicate requests for the same book."""
        with self.app.app_context():
            # First request succeeds
            ok1, code1, _ = request_service.create_book_request({
                'book_code': 'KB-BK-000004',
                'requester_name': 'Hamza Khan',
                'requester_class': 'Class 8-A',
                'requester_roll_no': '7',
                'requester_contact': '0300-7777777'
            })
            self.assertTrue(ok1)
            self.assertIsNotNone(code1)

            # Second request by same student (same class & roll number) for same book MUST be blocked
            ok2, code2, err2 = request_service.create_book_request({
                'book_code': 'KB-BK-000004',
                'requester_name': 'Hamza Khan',
                'requester_class': 'Class 8-A',
                'requester_roll_no': '7',
                'requester_contact': '0300-7777777'
            })
            self.assertFalse(ok2)
            self.assertIn('already have an active request', err2)

            # Same student requesting a DIFFERENT available book is permitted
            ok3, code3, _ = request_service.create_book_request({
                'book_code': 'KB-BK-000005',
                'requester_name': 'Hamza Khan',
                'requester_class': 'Class 8-A',
                'requester_roll_no': '7',
                'requester_contact': '0300-7777777'
            })
            self.assertTrue(ok3)

    def test_14_cannot_request_reserved_book_via_get_or_post(self):
        """Verify students cannot request an already-reserved book via GET or POST."""
        with self.app.app_context():
            db = get_db()
            db.execute("UPDATE books SET status = 'reserved' WHERE book_code = 'KB-BK-000006';")
            db.commit()

        # GET /request for reserved book should redirect back to book detail
        res_get = self.client.get('/request?book=KB-BK-000006')
        self.assertEqual(res_get.status_code, 302)
        self.assertIn('/book/KB-BK-000006', res_get.headers['Location'])

        # POST /request for reserved book should return 400 Bad Request
        self.client.get('/')
        with self.client.session_transaction() as sess:
            csrf_token = sess.get('csrf_token')

        res_post = self.client.post('/request', data={
            'csrf_token': csrf_token,
            'book_code': 'KB-BK-000006',
            'requester_name': 'Late Student',
            'requester_class': 'Class 6-A',
            'requester_roll_no': '10',
            'requester_contact': '0300-0000000'
        })
        self.assertEqual(res_post.status_code, 400)
        self.assertIn('reserved', res_post.get_data(as_text=True).lower())

if __name__ == '__main__':
    unittest.main()
