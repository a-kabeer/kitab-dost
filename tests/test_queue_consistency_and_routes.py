"""
Kitaab Bank - Queue Consistency & Screenshot Routes Verification Tests
Verifies:
1. Teacher Dashboard & Student Requests queue count consistency across pending, approved, completed, and all tabs.
2. Completed Handovers KPI and ledger query consistency.
3. Multi-faceted date and class filters return matching subsets.
4. Empty state banners appear strictly when datasets are empty.
5. All 23 screenshot audit routes return HTTP 200 with valid headings.
"""

import unittest
import tempfile
import shutil
import sqlite3
from pathlib import Path
from app import create_app
from app.services import request_service, handover_service, donation_service
from scripts.seed_demo import reset_and_seed_demo_data

class TestQueueConsistencyAndRoutes(unittest.TestCase):
    def setUp(self):
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

        from app.database import init_db
        init_db(self.app)
        reset_and_seed_demo_data(target_db=self.db_path, create_safety_backup=False)

        self.client = self.app.test_client()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _login_teacher(self):
        """Helper to establish an authenticated teacher session."""
        with self.client.session_transaction() as sess:
            sess['teacher_id'] = 1
            sess['teacher_username'] = 'teacher'
            sess['teacher_name'] = 'Sir Tariq Mahmood'

    # -------------------------------------------------------------------------
    # 1. Queue Counts & Consistency
    # -------------------------------------------------------------------------
    def test_pending_request_count_matches_displayed(self):
        """Assert pending requests count matches the actual records displayed in pending queue."""
        with self.app.app_context():
            pending_count = request_service.get_pending_requests_count()
            pending_records, total_count = request_service.get_requests_for_teacher(status='pending')

            self.assertEqual(pending_count, 1)
            self.assertEqual(len(pending_records), 1)
            self.assertEqual(total_count, 1)
            self.assertEqual(pending_records[0]['requester_name'], 'Ayesha Siddiqua')
            self.assertEqual(pending_records[0]['book_code'], 'KB-BK-000001')

    def test_all_requests_count_matches_total_requests(self):
        """Assert the All Requests tab displays the total sum of all requests across all statuses."""
        with self.app.app_context():
            # In database
            conn = sqlite3.connect(str(self.db_path))
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM requests;")
            db_total = cur.fetchone()[0]
            conn.close()

            all_records, total_count = request_service.get_requests_for_teacher(status=None)
            self.assertEqual(db_total, 5)
            self.assertEqual(total_count, 5)
            self.assertEqual(len(all_records), 5)

            # Check individual statuses sum up to total
            approved_records, app_count = request_service.get_requests_for_teacher(status='approved')
            completed_records, comp_count = request_service.get_requests_for_teacher(status='completed')
            pending_records, pend_count = request_service.get_requests_for_teacher(status='pending')
            self.assertEqual(app_count, 2)
            self.assertEqual(comp_count, 2)
            self.assertEqual(pend_count, 1)
            self.assertEqual(app_count + comp_count + pend_count, total_count)

    def test_completed_handover_kpi_matches_ledger_records(self):
        """Assert completed handover KPI matches the actual records in the handover ledger."""
        with self.app.app_context():
            metrics = handover_service.get_handover_metrics()
            handovers, total_count = handover_service.get_handovers_for_teacher()

            self.assertEqual(metrics['total_handovers'], 2)
            self.assertEqual(total_count, 2)
            self.assertEqual(len(handovers), 2)
            self.assertEqual(metrics['unique_recipients'], 2)
            self.assertEqual(metrics['reused_books'], 2)

            codes = [h['handover_code'] for h in handovers]
            self.assertIn('KB-HO-000001', codes)
            self.assertIn('KB-HO-000002', codes)

            # Assert joined book fields are populated
            for h in handovers:
                self.assertIsNotNone(h['book_title'])
                self.assertTrue(h['book_code'].startswith('KB-BK-'))

    def test_date_and_class_filters_return_matching_subsets(self):
        """Assert class and date filters filter correctly without suppressing valid matching records."""
        with self.app.app_context():
            # Class filter on requests
            c6_reqs, c6_count = request_service.get_requests_for_teacher(status=None, class_grade='Class 6')
            self.assertGreaterEqual(c6_count, 1)
            for r in c6_reqs:
                self.assertTrue('Class 6' in r['requester_class'] or r['book_class'] == 'Class 6')

            # Class filter on handovers
            c7_hos, c7_count = handover_service.get_handovers_for_teacher(class_grade='Class 7')
            self.assertGreaterEqual(c7_count, 1)
            for h in c7_hos:
                self.assertTrue('Class 7' in h['recipient_class'] or h['book_class'] == 'Class 7')

    def test_empty_states_appear_only_when_truly_empty(self):
        """Assert empty state banners appear only when query yields zero results."""
        self._login_teacher()

        # Non-empty request page load (Pending has 1 record)
        res = self.client.get('/teacher/requests?status=pending')
        self.assertEqual(res.status_code, 200)
        self.assertNotIn(b'No Requests in this Queue', res.data)
        self.assertIn(b'Ayesha Siddiqua', res.data)

        # Empty request page load (Non-existent class filter)
        res_empty = self.client.get('/teacher/requests?class=Class+99')
        self.assertEqual(res_empty.status_code, 200)
        self.assertIn(b'No Requests in this Queue', res_empty.data)

        # Non-empty handover page load (has 2 records)
        res_ho = self.client.get('/teacher/handovers')
        self.assertEqual(res_ho.status_code, 200)
        self.assertNotIn(b'No Handover Records Found', res_ho.data)
        self.assertIn(b'KB-HO-000001', res_ho.data)

        # Empty handover page load (non-existent search)
        res_ho_empty = self.client.get('/teacher/handovers?q=NONEXISTENT_STUDENT')
        self.assertEqual(res_ho_empty.status_code, 200)
        self.assertIn(b'No Handover Records Found', res_ho_empty.data)

    # -------------------------------------------------------------------------
    # 2. Screenshot Routes Integrity (All HTTP 200 + Headings)
    # -------------------------------------------------------------------------
    def test_screenshot_route_urls_return_200_and_valid_headings(self):
        """Assert that every audited screenshot route returns HTTP 200 and renders valid headings."""
        with self.app.app_context():
            # Fetch dynamic live IDs from seeded database
            conn = sqlite3.connect(str(self.db_path))
            cur = conn.cursor()
            cur.execute("SELECT id, book_code FROM books WHERE status='available' LIMIT 1;")
            avail_book_id, avail_book_code = cur.fetchone()

            cur.execute("SELECT id, tracking_code FROM requests WHERE status='approved' LIMIT 1;")
            approved_req_id, approved_tracking = cur.fetchone()

            cur.execute("SELECT tracking_code FROM requests WHERE status='pending' LIMIT 1;")
            pending_tracking = cur.fetchone()[0]

            cur.execute("SELECT id, donation_code FROM donations LIMIT 1;")
            don_id, don_code = cur.fetchone()

            cur.execute("SELECT id, handover_code FROM handovers LIMIT 1;")
            ho_id, ho_code = cur.fetchone()
            conn.close()

            # 1. student_home
            res = self.client.get('/')
            self.assertEqual(res.status_code, 200)
            self.assertIn(b'Kitaab Bank', res.data)

            # 2. student_catalogue
            res = self.client.get('/catalogue')
            self.assertEqual(res.status_code, 200)
            self.assertIn(b'School Book Catalogue', res.data)

            # 3. student_book_detail
            res = self.client.get(f'/book/{avail_book_code}')
            self.assertEqual(res.status_code, 200)
            self.assertIn(avail_book_code.encode(), res.data)

            # 4. student_donate
            res = self.client.get('/donate')
            self.assertEqual(res.status_code, 200)
            self.assertIn(b'Donate', res.data)

            # 5. student_request
            res = self.client.get(f'/request/{avail_book_id}')
            self.assertEqual(res.status_code, 200)
            self.assertIn(b'Request', res.data)

            # 6. student_track
            res = self.client.get(f'/track?code={pending_tracking}')
            self.assertEqual(res.status_code, 200)
            self.assertIn(b'Track', res.data)

            # 7. student_scan
            res = self.client.get('/scan')
            self.assertEqual(res.status_code, 200)
            self.assertIn(b'Scan', res.data)

            # 8. student_donation_success
            res = self.client.get(f'/donate/success/{don_code}')
            self.assertEqual(res.status_code, 200)
            self.assertIn(don_code.encode(), res.data)

            # 9. student_request_success (Priority 0 Verification: MUST NOT BE 404!)
            res = self.client.get(f'/request/success/{pending_tracking}')
            self.assertEqual(res.status_code, 200)
            self.assertIn(b'Request Received', res.data)
            self.assertIn(pending_tracking.encode(), res.data)

            # 10. auth_login (Unauthenticated)
            res = self.client.get('/auth/login')
            self.assertEqual(res.status_code, 200)
            self.assertIn(b'Sign In', res.data)

            # Now log in teacher for protected routes
            self._login_teacher()

            # 11. teacher_dashboard
            res = self.client.get('/teacher/dashboard')
            self.assertEqual(res.status_code, 200)
            self.assertIn(b'Dashboard', res.data)

            # 12. teacher_donations
            res = self.client.get('/teacher/donations')
            self.assertEqual(res.status_code, 200)
            self.assertIn(b'Donation', res.data)

            # 13. teacher_donation_detail
            res = self.client.get(f'/teacher/donations/{don_id}')
            self.assertEqual(res.status_code, 200)
            self.assertIn(b'Donation', res.data)

            # 14. teacher_requests
            res = self.client.get('/teacher/requests')
            self.assertEqual(res.status_code, 200)
            self.assertIn(b'Request', res.data)

            # 15. teacher_request_detail (Priority 0 Verification: MUST NOT BE 404!)
            res = self.client.get(f'/teacher/requests/{approved_req_id}')
            self.assertEqual(res.status_code, 200)
            self.assertIn(b'Request', res.data)
            self.assertIn(approved_tracking.encode(), res.data)

            # 16. teacher_handover_confirm (Priority 0 Verification: MUST NOT BE 404!)
            res = self.client.get(f'/teacher/requests/{approved_req_id}/handover')
            self.assertEqual(res.status_code, 200)
            self.assertIn(b'Handover', res.data)

            # 17. teacher_handovers
            res = self.client.get('/teacher/handovers')
            self.assertEqual(res.status_code, 200)
            self.assertIn(b'Handover', res.data)

            # 18. teacher_handover_receipt (Priority 0 Verification: MUST NOT BE 404!)
            res = self.client.get(f'/teacher/handovers/{ho_id}/receipt')
            self.assertEqual(res.status_code, 200)
            self.assertIn(b'Receipt', res.data)
            self.assertIn(ho_code.encode(), res.data)

            # 19. teacher_inventory
            res = self.client.get('/teacher/inventory')
            self.assertEqual(res.status_code, 200)
            self.assertIn(b'Inventory', res.data)

            # 20. teacher_reports
            res = self.client.get('/teacher/reports')
            self.assertEqual(res.status_code, 200)
            self.assertIn(b'Reports', res.data)

            # 21. teacher_settings
            res = self.client.get('/teacher/settings')
            self.assertEqual(res.status_code, 200)
            self.assertIn(b'Settings', res.data)

            # 22. teacher_logs
            res = self.client.get('/teacher/logs')
            self.assertEqual(res.status_code, 200)
            self.assertIn(b'Logs', res.data)

            # 23. teacher_qr_sheet
            res = self.client.get('/teacher/qr-sheet')
            self.assertEqual(res.status_code, 200)
            self.assertIn(b'QR', res.data)

    def test_teacher_dashboard_donation_metric_and_rtl_localization(self):
        """Assert Teacher Dashboard displays Total Donations matching analytics.summary.total_donations and RTL localization works."""
        from app.services import analytics_service
        self._login_teacher()

        with self.app.app_context():
            analytics = analytics_service.get_dashboard_analytics()
            self.assertEqual(analytics['summary']['total_donations'], 3)
            self.assertEqual(analytics['summary']['pending_donations'], 1)

            # English Dashboard
            res = self.client.get('/teacher/dashboard')
            self.assertEqual(res.status_code, 200)
            # Must show Total Donations KPI
            self.assertIn(b'Total Donations', res.data)
            self.assertIn(b'3', res.data)
            self.assertIn(b'Queue', res.data)

            # Switch to Urdu
            self.client.get('/set-language/ur')
            res_ur = self.client.get('/teacher/dashboard')
            self.assertEqual(res_ur.status_code, 200)
            # Must show Urdu Total Donations label: کل عطیات
            self.assertIn('کل عطیات'.encode('utf-8'), res_ur.data)
            # Must show Urdu status label: کیٹلاگ میں دستیاب
            self.assertIn('کیٹلاگ میں دستیاب'.encode('utf-8'), res_ur.data)

            # Switch to Sindhi
            self.client.get('/set-language/sd')
            res_sd = self.client.get('/catalogue')
            self.assertEqual(res_sd.status_code, 200)
            # Must show Sindhi Available status label
            self.assertIn('دستياب'.encode('utf-8'), res_sd.data)

    def test_urdu_teacher_dashboard_complete_rendered_strings(self):
        """Assert Urdu Teacher Dashboard completely localizes greetings, names, actions, and status badges."""
        self._login_teacher()
        self.client.get('/set-language/ur')
        res = self.client.get('/teacher/dashboard')
        self.assertEqual(res.status_code, 200)
        html = res.data.decode('utf-8')

        # Welcome message in Urdu with teacher name
        self.assertIn('خوش آمدید', html)
        self.assertIn('Sir Tariq Mahmood', html)
        # Localized status breakdown
        self.assertIn('کیٹلاگ میں دستیاب', html)
        self.assertIn('محفوظ شدہ (حصول باقی)', html)
        self.assertIn('جاری شدہ (دوبارہ زیرِ استعمال)', html)

        # Now test when logged in with default 'School Teacher / Incharge'
        with self.client.session_transaction() as sess:
            sess['teacher_name'] = 'School Teacher / Incharge'
        res_default = self.client.get('/teacher/dashboard')
        html_default = res_default.data.decode('utf-8')
        self.assertIn('اسکول استاد / انچارج', html_default)
        self.assertNotIn('School Teacher / Incharge', html_default)

    def test_sindhi_homepage_complete_rendered_strings(self):
        """Assert Sindhi Homepage renders localized class grade badges and metrics."""
        self.client.get('/set-language/sd')
        res = self.client.get('/')
        self.assertEqual(res.status_code, 200)
        html = res.data.decode('utf-8')

        # Class badges localized to Sindhi
        self.assertTrue('ڪلاس اٺين' in html or 'ڪلاس ستين' in html or 'ڪلاس ڇهين' in html)
        # Metrics strip localized
        self.assertIn('ڪل عطيو ڪيل ڪتاب', html)
        self.assertIn('هن وقت دستياب', html)
        self.assertIn('ٻيهر واپرائل ڪتاب', html)

    def test_settings_mobile_selector_and_desktop_tabs_guard(self):
        """Assert Settings template includes mobile tab selector and hides desktop tablist on mobile."""
        self._login_teacher()
        res = self.client.get('/teacher/settings')
        self.assertEqual(res.status_code, 200)
        html = res.data.decode('utf-8')

        # Mobile tab selector exists
        self.assertIn('id="mobileSettingsTabSelect"', html)
        self.assertIn('tab=profile', html)
        self.assertIn('tab=security', html)
        self.assertIn('tab=backup', html)
        self.assertIn('tab=demo', html)

        # Desktop tabs have d-none d-md-flex
        self.assertIn('class="d-none d-md-flex gap-2', html)

    def test_student_book_detail_compact_related_books(self):
        """Assert Student Book Detail related books uses compact horizontal card style on mobile."""
        res = self.client.get('/book/KB-BK-000001')
        self.assertEqual(res.status_code, 200)
        html = res.data.decode('utf-8')

        # Compact mobile container exists with constrained height
        self.assertIn('max-height: 120px;', html)
        self.assertIn('d-md-none', html)

    def test_zero_dashed_information_borders(self):
        """Assert no info container or code row has dashed border style."""
        res = self.client.get('/scan')
        self.assertEqual(res.status_code, 200)
        html = res.data.decode('utf-8')
        self.assertNotIn('border: 2px dashed', html)
        self.assertIn('border: 2px solid', html)

if __name__ == '__main__':
    unittest.main()
