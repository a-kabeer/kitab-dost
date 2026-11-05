"""
Unit and Integration Tests for Phase 5: Physical Handover Ledger & Circulation Defense
Tests:
1. Successful physical handover.
2. Unique handover reference generation (KB-HO-000001).
3. Handover only for approved requests.
4. Rejection of pending requests.
5. Rejection of rejected requests.
6. Rejection of unavailable books.
7. Duplicate handover prevention.
8. Same physical book cannot be handed over twice.
9. Simultaneous handover attempts (race condition protection).
10. Missing identity confirmation.
11. Missing physical handover confirmation.
12. Student privacy on the public tracking page (zero PII leakage).
13. Teacher authentication on all handover routes.
14. Handover receipt access protection.
15. Reservation cancellation and book availability restoration.
16. Prevention of cancellation after completed handover.
17. Database rollback when a handover transaction fails.
"""

import sys
import unittest
from unittest.mock import patch

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

from app import create_app
from app.database import get_db, init_db
from app.services import request_service, handover_service, rate_limiter

class Phase5PhysicalHandoverTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app('testing')
        cls.client = cls.app.test_client()
        with cls.app.app_context():
            init_db(cls.app)
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
        rate_limiter.reset_rate_limits()

    def _login_teacher(self):
        """Helper to establish an authenticated teacher session."""
        with self.client.session_transaction() as sess:
            sess['teacher_id'] = 1
            sess['teacher_username'] = 'teacher'
            sess['teacher_name'] = 'School Teacher / Incharge'
            sess['teacher_role'] = 'admin'

    def _create_approved_request(self, book_code='KB-BK-000001', student_name='Ayesha Khan', roll_no='14'):
        """Helper to create and approve a student book request."""
        with self.app.app_context():
            db = get_db()
            # Ensure book is available
            db.execute("UPDATE books SET status = 'available' WHERE book_code = ?;", (book_code,))
            db.commit()

            ok, tracking_code, _ = request_service.create_book_request({
                'book_code': book_code,
                'requester_name': student_name,
                'requester_class': 'Class 7-A',
                'requester_roll_no': roll_no,
                'requester_contact': '0300-1234567',
                'notes': 'Preparation for exams'
            })
            assert ok, "Failed to create book request"

            cur = db.cursor()
            cur.execute("SELECT id FROM requests WHERE tracking_code = ?;", (tracking_code,))
            req_id = cur.fetchone()['id']

            ok_appr, _, _ = request_service.approve_request(req_id, 1, 'Teacher Tariq')
            assert ok_appr, "Failed to approve book request"

            return req_id, tracking_code

    def test_01_successful_physical_handover(self):
        """1. Verify successful physical handover workflow."""
        req_id, tracking_code = self._create_approved_request('KB-BK-000001', 'Ayesha Khan', '14')

        with self.app.app_context():
            success, handover_code, err = handover_service.confirm_physical_handover(
                request_id=req_id,
                teacher_id=1,
                teacher_name='Teacher Tariq',
                id_verified=True,
                book_handed_over=True,
                remarks='Textbook inspected in good condition'
            )
            self.assertTrue(success)
            self.assertTrue(handover_code.startswith('KB-HO-'))
            self.assertIsNone(err)

            # Check DB state
            db = get_db()
            cur = db.cursor()
            cur.execute("SELECT status FROM requests WHERE id = ?;", (req_id,))
            self.assertEqual(cur.fetchone()['status'], 'completed')

            cur.execute("SELECT status FROM books WHERE book_code = 'KB-BK-000001';")
            self.assertEqual(cur.fetchone()['status'], 'handed_over')

            # Verify ledger record
            cur.execute("SELECT * FROM handovers WHERE handover_code = ?;", (handover_code,))
            h = cur.fetchone()
            self.assertIsNotNone(h)
            self.assertEqual(h['recipient_name'], 'Ayesha Khan')
            self.assertEqual(h['recipient_roll_no'], '14')
            self.assertEqual(h['book_code'], 'KB-BK-000001')

    def test_02_unique_handover_reference_generation(self):
        """2. Verify sequential, unique reference format (KB-HO-000001, KB-HO-000002)."""
        req_id1, _ = self._create_approved_request('KB-BK-000002', 'Student One', '101')
        req_id2, _ = self._create_approved_request('KB-BK-000003', 'Student Two', '102')

        with self.app.app_context():
            s1, code1, _ = handover_service.confirm_physical_handover(req_id1, 1, 'Teacher', True, True)
            s2, code2, _ = handover_service.confirm_physical_handover(req_id2, 1, 'Teacher', True, True)

            self.assertTrue(s1 and s2)
            self.assertNotEqual(code1, code2)
            self.assertTrue(code1.startswith('KB-HO-'))
            self.assertTrue(code2.startswith('KB-HO-'))
            # Format check: KB-HO- followed by 6 digits
            self.assertEqual(len(code1), 12)
            self.assertEqual(len(code2), 12)

    def test_03_handover_only_for_approved_requests(self):
        """3. Verify handover succeeds when request is in approved state."""
        req_id, _ = self._create_approved_request('KB-BK-000004', 'Valid Student', '201')
        with self.app.app_context():
            ok, code, err = handover_service.confirm_physical_handover(req_id, 1, 'Teacher', True, True)
            self.assertTrue(ok)
            self.assertIsNotNone(code)

    def test_04_rejection_of_pending_requests(self):
        """4. Verify handover fails if request is still pending."""
        with self.app.app_context():
            db = get_db()
            db.execute("UPDATE books SET status = 'available' WHERE book_code = 'KB-BK-000005';")
            db.commit()

            ok_req, trk, _ = request_service.create_book_request({
                'book_code': 'KB-BK-000005',
                'requester_name': 'Pending Student',
                'requester_class': 'Class 6-B',
                'requester_roll_no': '301',
                'requester_contact': '0300-3333333'
            })
            self.assertTrue(ok_req)

            cur = db.cursor()
            cur.execute("SELECT id FROM requests WHERE tracking_code = ?;", (trk,))
            pending_req_id = cur.fetchone()['id']

            ok_ho, _, err = handover_service.confirm_physical_handover(pending_req_id, 1, 'Teacher', True, True)
            self.assertFalse(ok_ho)
            self.assertIn('pending', err.lower())

    def test_05_rejection_of_rejected_requests(self):
        """5. Verify handover fails if request was rejected."""
        with self.app.app_context():
            db = get_db()
            db.execute("UPDATE books SET status = 'available' WHERE book_code = 'KB-BK-000006';")
            db.commit()

            ok_req, trk, _ = request_service.create_book_request({
                'book_code': 'KB-BK-000006',
                'requester_name': 'Rejected Student',
                'requester_class': 'Class 6-B',
                'requester_roll_no': '401',
                'requester_contact': '0300-4444444'
            })
            self.assertTrue(ok_req)

            cur = db.cursor()
            cur.execute("SELECT id FROM requests WHERE tracking_code = ?;", (trk,))
            req_id = cur.fetchone()['id']

            # Reject request
            request_service.reject_request(req_id, 1, 'Teacher', 'Not eligible')

            ok_ho, _, err = handover_service.confirm_physical_handover(req_id, 1, 'Teacher', True, True)
            self.assertFalse(ok_ho)
            self.assertIn('rejected', err.lower())

    def test_06_rejection_of_unavailable_books(self):
        """6. Verify handover fails if book is not currently reserved."""
        req_id, _ = self._create_approved_request('KB-BK-000007', 'Unavail Test', '501')
        with self.app.app_context():
            db = get_db()
            # Force book to available or retired
            db.execute("UPDATE books SET status = 'available' WHERE book_code = 'KB-BK-000007';")
            db.commit()

            ok_ho, _, err = handover_service.confirm_physical_handover(req_id, 1, 'Teacher', True, True)
            self.assertFalse(ok_ho)
            self.assertIn('must be \'reserved\'', err.lower())

    def test_07_duplicate_handover_prevention(self):
        """7. Verify duplicate handover attempts on same request are blocked."""
        req_id, _ = self._create_approved_request('KB-BK-000008', 'Dup Test', '601')
        with self.app.app_context():
            # First handover succeeds
            s1, _, _ = handover_service.confirm_physical_handover(req_id, 1, 'Teacher', True, True)
            self.assertTrue(s1)

            # Second handover attempt on same request MUST fail
            s2, _, err = handover_service.confirm_physical_handover(req_id, 1, 'Teacher', True, True)
            self.assertFalse(s2)
            self.assertIn('already', err.lower())

    def test_08_same_physical_book_cannot_be_handed_over_twice(self):
        """8. Verify book already handed over cannot be handed over again."""
        req_id, _ = self._create_approved_request('KB-BK-000009', 'Circulation Test', '701')
        with self.app.app_context():
            s1, _, _ = handover_service.confirm_physical_handover(req_id, 1, 'Teacher', True, True)
            self.assertTrue(s1)

            # Book status is now handed_over
            db = get_db()
            cur = db.cursor()
            cur.execute("SELECT status FROM books WHERE book_code = 'KB-BK-000009';")
            self.assertEqual(cur.fetchone()['status'], 'handed_over')

            # Attempting another handover with manual approved status on a request for this book
            cur.execute(
                "INSERT INTO requests (tracking_code, book_id, requester_name, requester_class, requester_roll_no, requester_contact, status) "
                "VALUES ('KB-REQ-TEST-CIRC', 9, 'Other', '8-A', '999', '0300', 'approved');"
            )
            other_id = cur.lastrowid
            db.commit()

            s2, _, err = handover_service.confirm_physical_handover(other_id, 1, 'Teacher', True, True)
            self.assertFalse(s2)
            self.assertIn('already handed over', err.lower())

    def test_09_simultaneous_handover_attempts(self):
        """9. Verify race condition defense: simultaneous handover attempts."""
        req_id, _ = self._create_approved_request('KB-BK-000010', 'Race Test', '801')
        with self.app.app_context():
            # First attempt succeeds
            s1, c1, _ = handover_service.confirm_physical_handover(req_id, 1, 'Teacher One', True, True)
            self.assertTrue(s1)

            # Second attempt receives atomic rejection
            s2, c2, err2 = handover_service.confirm_physical_handover(req_id, 1, 'Teacher Two', True, True)
            self.assertFalse(s2)
            self.assertIn('already', err2.lower())

    def test_10_missing_identity_confirmation(self):
        """10. Verify submission fails if student identity checkbox is unchecked."""
        req_id, _ = self._create_approved_request('KB-BK-000011', 'Checklist Test', '901')
        with self.app.app_context():
            ok, _, err = handover_service.confirm_physical_handover(
                req_id, 1, 'Teacher', id_verified=False, book_handed_over=True
            )
            self.assertFalse(ok)
            self.assertIn("identity", err.lower())

    def test_11_missing_physical_handover_confirmation(self):
        """11. Verify submission fails if physical book handover checkbox is unchecked."""
        req_id, _ = self._create_approved_request('KB-BK-000012', 'Checklist Test 2', '902')
        with self.app.app_context():
            ok, _, err = handover_service.confirm_physical_handover(
                req_id, 1, 'Teacher', id_verified=True, book_handed_over=False
            )
            self.assertFalse(ok)
            self.assertIn("physical textbook", err.lower())

    def test_12_student_privacy_on_public_tracking_page(self):
        """12. Verify /track shows completed status & handover ref while keeping zero PII leakage."""
        req_id, tracking_code = self._create_approved_request('KB-BK-000013', 'Sumbul Noor', '45')
        with self.app.app_context():
            s, h_code, _ = handover_service.confirm_physical_handover(req_id, 1, 'Teacher Tariq', True, True)
            self.assertTrue(s)

        res = self.client.get(f'/track?code={tracking_code}')
        self.assertEqual(res.status_code, 200)
        html = res.get_data(as_text=True)

        # Must display handover reference & completed confirmation
        self.assertIn(h_code, html)
        self.assertIn('Book Successfully Handed Over', html)
        self.assertIn('Sumbul N***', html)

        # STRICT PRIVACY: Roll number '45' and contact phone '0300-1234567' must NEVER be in HTML
        self.assertNotIn('0300-1234567', html)
        self.assertNotIn('>45<', html)
        self.assertNotIn('value="45"', html)

    def test_13_teacher_authentication_on_all_handover_routes(self):
        """13. Verify all teacher handover routes require valid login."""
        with self.client.session_transaction() as sess:
            sess.clear()

        # 1. Handover ledger list
        r1 = self.client.get('/teacher/handovers')
        self.assertEqual(r1.status_code, 302)
        self.assertIn('/auth/login', r1.headers['Location'])

        # 2. Handover detail inspection
        r2 = self.client.get('/teacher/handovers/1')
        self.assertEqual(r2.status_code, 302)
        self.assertIn('/auth/login', r2.headers['Location'])

        # 3. Handover receipt
        r3 = self.client.get('/teacher/handovers/1/receipt')
        self.assertEqual(r3.status_code, 302)
        self.assertIn('/auth/login', r3.headers['Location'])

        # 4. Handover confirmation form
        r4 = self.client.get('/teacher/requests/1/handover')
        self.assertEqual(r4.status_code, 302)
        self.assertIn('/auth/login', r4.headers['Location'])

        # 5. Handover confirmation action (POST)
        self.client.get('/')
        with self.client.session_transaction() as sess:
            token = sess.get('csrf_token')
        r5 = self.client.post('/teacher/requests/1/confirm-handover', data={'csrf_token': token})
        self.assertEqual(r5.status_code, 302)
        self.assertIn('/auth/login', r5.headers['Location'])

        # 6. Reservation cancellation action (POST)
        r6 = self.client.post('/teacher/requests/1/cancel-reservation', data={'csrf_token': token, 'reason': 'Test'})
        self.assertEqual(r6.status_code, 302)
        self.assertIn('/auth/login', r6.headers['Location'])

    def test_14_handover_receipt_access_protection(self):
        """14. Verify handover receipt is accessible to teacher and contains required fields."""
        req_id, _ = self._create_approved_request('KB-BK-000014', 'Receipt Student', '88')
        with self.app.app_context():
            s, h_code, _ = handover_service.confirm_physical_handover(req_id, 1, 'Teacher Tariq', True, True)
            self.assertTrue(s)
            h = handover_service.get_handover_by_code(h_code)
            h_id = h['id']

        self._login_teacher()
        res = self.client.get(f'/teacher/handovers/{h_id}/receipt')
        self.assertEqual(res.status_code, 200)
        html = res.get_data(as_text=True)

        self.assertIn(h_code, html)
        self.assertIn('Receipt Student', html)
        self.assertIn('KB-BK-000014', html)
        self.assertIn('Teacher Tariq', html)
        self.assertIn('Print Receipt', html)

    def test_15_reservation_cancellation_and_book_availability_restoration(self):
        """15. Verify cancellation restores book to Available in catalogue and updates request to cancelled."""
        req_id, trk = self._create_approved_request('KB-BK-000015', 'Cancelled Student', '99')

        with self.app.app_context():
            # Book is currently reserved
            db = get_db()
            cur = db.cursor()
            cur.execute("SELECT status FROM books WHERE book_code = 'KB-BK-000015';")
            self.assertEqual(cur.fetchone()['status'], 'reserved')

            # Teacher cancels reservation
            cancel_reason = "Student moved out of district"
            ok, bk_code, err = handover_service.cancel_approved_reservation(
                request_id=req_id,
                teacher_id=1,
                teacher_name='Teacher Tariq',
                reason=cancel_reason
            )
            self.assertTrue(ok)
            self.assertEqual(bk_code, 'KB-BK-000015')

            # Book status MUST be restored to 'available'
            cur.execute("SELECT status FROM books WHERE book_code = 'KB-BK-000015';")
            self.assertEqual(cur.fetchone()['status'], 'available')

            # Request status MUST be 'cancelled' with recorded reason
            cur.execute("SELECT status, rejection_reason FROM requests WHERE id = ?;", (req_id,))
            r = cur.fetchone()
            self.assertEqual(r['status'], 'cancelled')
            self.assertEqual(r['rejection_reason'], cancel_reason)

        # Public tracking lookup reflects cancellation
        track_res = self.client.get(f'/track?code={trk}')
        self.assertIn('Reservation Released', track_res.get_data(as_text=True))
        self.assertIn(cancel_reason, track_res.get_data(as_text=True))

    def test_16_prevention_of_cancellation_after_completed_handover(self):
        """16. Verify reservation cancellation is blocked after physical handover is completed."""
        req_id, _ = self._create_approved_request('KB-BK-000016', 'Immutable Student', '77')
        with self.app.app_context():
            # Complete physical handover
            s, _, _ = handover_service.confirm_physical_handover(req_id, 1, 'Teacher Tariq', True, True)
            self.assertTrue(s)

            # Attempting cancellation on completed handover MUST fail
            ok, _, err = handover_service.cancel_approved_reservation(
                req_id, 1, 'Teacher Tariq', 'Attempted cancellation'
            )
            self.assertFalse(ok)
            self.assertIn('already been physically handed over', err.lower())

    def test_17_database_rollback_when_handover_transaction_fails(self):
        """17. Verify transaction rollback: failure leaves request and book in approved/reserved state."""
        req_id, _ = self._create_approved_request('KB-BK-000017', 'Rollback Student', '66')

        with self.app.app_context():
            db = get_db()
            cur = db.cursor()

            with patch('app.services.handover_service.generate_next_handover_code', side_effect=Exception("Simulated disk error during handover write")):
                ok, code, err = handover_service.confirm_physical_handover(
                    req_id, 1, 'Teacher Tariq', True, True
                )
                self.assertFalse(ok)
                self.assertIn("Simulated disk error", err)

            # Verify complete rollback: request MUST still be 'approved', book MUST still be 'reserved'
            cur.execute("SELECT status FROM requests WHERE id = ?;", (req_id,))
            self.assertEqual(cur.fetchone()['status'], 'approved')

            cur.execute("SELECT status FROM books WHERE book_code = 'KB-BK-000017';")
            self.assertEqual(cur.fetchone()['status'], 'reserved')

            # Zero handovers recorded
            cur.execute("SELECT COUNT(*) FROM handovers WHERE request_id = ?;", (req_id,))
            self.assertEqual(cur.fetchone()[0], 0)

if __name__ == '__main__':
    unittest.main()
