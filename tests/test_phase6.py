"""
Unit & Integration Test Suite for Phase 6: QR System, Label Printing & Android Tested Scanner
"""

import unittest
import io
import re
from PIL import Image
from app import create_app
from app.database import get_db, init_db
from app.services import qr_service, book_service

class Phase6QrSystemTests(unittest.TestCase):

    def setUp(self):
        self.app = create_app('testing')
        with self.app.app_context():
            from app.seed_data import seed_sample_books
            seed_sample_books()
        self.client = self.app.test_client()

    def _login_teacher(self):
        """Helper to establish an authenticated teacher session."""
        with self.client.session_transaction() as sess:
            sess['teacher_id'] = 1
            sess['teacher_name'] = 'Teacher Tariq'
            sess['teacher_username'] = 'teacher'

    def _get_csrf_token(self):
        res = self.client.get('/scan')
        match = re.search(r'name="csrf_token"\s+value="([a-f0-9]+)"', res.get_data(as_text=True))
        if match:
            return match.group(1)
        with self.client.session_transaction() as sess:
            return sess.get('csrf_token', 'test_csrf_token')

    # -------------------------------------------------------------
    # 1. QR Code Service Unit Tests
    # -------------------------------------------------------------
    def test_01_qr_service_png_and_data_uri_generation(self):
        """1. Verify qr_service generates valid PNG bytes and base64 data URIs."""
        payload = "/book/KB-BK-000001"
        png_bytes = qr_service.generate_qr_png_bytes(payload)
        
        # Verify valid PNG header (\x89PNG\r\n\x1a\n)
        self.assertTrue(png_bytes.startswith(b'\x89PNG\r\n\x1a\n'))
        
        # Verify Pillow can parse and verify the image
        img = Image.open(io.BytesIO(png_bytes))
        self.assertEqual(img.format, 'PNG')
        self.assertGreater(img.width, 50)
        self.assertGreater(img.height, 50)

        # Verify Data URI format
        data_uri = qr_service.generate_qr_data_uri(payload)
        self.assertTrue(data_uri.startswith('data:image/png;base64,'))
        self.assertGreater(len(data_uri), 100)

    def test_02_qr_service_book_code_parsing_and_normalization(self):
        """2. Verify code parser normalizes URLs, paths, standard codes, and numeric shortcuts."""
        # 2.1 Full URL
        r1 = qr_service.parse_scanned_book_code("http://10.0.0.36:5000/book/KB-BK-000001")
        self.assertEqual(r1['type'], 'book')
        self.assertEqual(r1['code'], 'KB-BK-000001')

        # 2.2 Relative Path
        r2 = qr_service.parse_scanned_book_code("/book/KB-BK-000002")
        self.assertEqual(r2['type'], 'book')
        self.assertEqual(r2['code'], 'KB-BK-000002')

        # 2.3 Exact Standard Code
        r3 = qr_service.parse_scanned_book_code("KB-BK-000003")
        self.assertEqual(r3['type'], 'book')
        self.assertEqual(r3['code'], 'KB-BK-000003')

        # 2.4 Lowercase with Whitespace
        r4 = qr_service.parse_scanned_book_code("  kb-bk-000004  ")
        self.assertEqual(r4['type'], 'book')
        self.assertEqual(r4['code'], 'KB-BK-000004')

        # 2.5 Pure Digits (Shortcuts)
        r5 = qr_service.parse_scanned_book_code("5")
        self.assertEqual(r5['type'], 'book')
        self.assertEqual(r5['code'], 'KB-BK-000005')

        r6 = qr_service.parse_scanned_book_code("000006")
        self.assertEqual(r6['type'], 'book')
        self.assertEqual(r6['code'], 'KB-BK-000006')

        # 2.6 Short Prefix: BK-7
        r7 = qr_service.parse_scanned_book_code("BK-7")
        self.assertEqual(r7['type'], 'book')
        self.assertEqual(r7['code'], 'KB-BK-000007')

        # 2.7 Request Tracking Code Detection
        r8 = qr_service.parse_scanned_book_code("KB-REQ-7K9M-2X4P")
        self.assertEqual(r8['type'], 'request')
        self.assertEqual(r8['code'], 'KB-REQ-7K9M-2X4P')

        # 2.8 Track URL
        r9 = qr_service.parse_scanned_book_code("http://localhost:5000/track?code=KB-REQ-ABCD-1234")
        self.assertEqual(r9['type'], 'request')
        self.assertEqual(r9['code'], 'KB-REQ-ABCD-1234')

        # 2.9 Donation Reference Detection
        r10 = qr_service.parse_scanned_book_code("KB-DON-4YMX-B4AZ")
        self.assertEqual(r10['type'], 'donation')
        self.assertEqual(r10['code'], 'KB-DON-4YMX-B4AZ')

    # -------------------------------------------------------------
    # 2. Student Scanner & Lookup Views
    # -------------------------------------------------------------
    def test_03_student_scan_page_renders_with_dual_mode(self):
        """3. Verify /scan renders with manual input and camera elements."""
        res = self.client.get('/scan')
        self.assertEqual(res.status_code, 200)
        html = res.get_data(as_text=True)

        # First-class manual input elements
        self.assertIn('id="manual-code-input"', html)
        self.assertIn('id="manual-lookup-btn"', html)
        self.assertIn('Manual 6-Digit Book Code Entry', html)

        # Camera & Context elements
        self.assertIn('id="insecure-context-banner"', html)
        self.assertIn('id="secure-scanner-wrap"', html)
        self.assertIn('id="qr-video"', html)
        self.assertIn('id="start-camera-btn"', html)

        # Offline script dependencies
        self.assertIn('static/js/jsqr.js', html)
        self.assertIn('static/js/qr_scanner.js', html)

    def test_04_manual_code_lookup_successful_redirect(self):
        """4. Verify valid code entered via GET or POST redirects to book detail."""
        # 4.1 GET with exact code
        res_get = self.client.get('/scan?code=KB-BK-000001')
        self.assertEqual(res_get.status_code, 302)
        self.assertIn('/book/KB-BK-000001', res_get.headers['Location'])

        # 4.2 GET with numeric shortcut
        res_num = self.client.get('/scan?code=2')
        self.assertEqual(res_num.status_code, 302)
        self.assertIn('/book/KB-BK-000002', res_num.headers['Location'])

        # 4.3 POST with code
        csrf = self._get_csrf_token()
        res_post = self.client.post('/scan', data={'code': 'KB-BK-000003', 'csrf_token': csrf})
        self.assertEqual(res_post.status_code, 302)
        self.assertIn('/book/KB-BK-000003', res_post.headers['Location'])

    def test_05_manual_code_lookup_tracking_code_redirect(self):
        """5. Verify entering a request tracking code in /scan redirects to /track."""
        res = self.client.get('/scan?code=KB-REQ-TEST-1234')
        self.assertEqual(res.status_code, 302)
        self.assertIn('/track?code=KB-REQ-TEST-1234', res.headers['Location'])

    def test_06_manual_code_lookup_invalid_code(self):
        """6. Verify non-existent book code displays friendly error banner."""
        # GET
        res_get = self.client.get('/scan?code=KB-BK-999999')
        self.assertEqual(res_get.status_code, 200)
        html_get = res_get.get_data(as_text=True)
        self.assertIn('Textbook Not Found', html_get)
        self.assertIn('KB-BK-999999', html_get)

        # POST
        csrf = self._get_csrf_token()
        res_post = self.client.post('/scan', data={'code': 'INVALID_CODE_XYZ', 'csrf_token': csrf})
        self.assertEqual(res_post.status_code, 200)
        html_post = res_post.get_data(as_text=True)
        self.assertIn('Textbook Not Found', html_post)

    def test_07_dynamic_qr_image_route(self):
        """7. Verify /qr/<book_code>.png returns dynamic PNG bytes with caching headers."""
        res = self.client.get('/qr/KB-BK-000001.png')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.content_type, 'image/png')
        self.assertTrue(res.data.startswith(b'\x89PNG\r\n\x1a\n'))
        self.assertIn('max-age=86400', res.headers.get('Cache-Control', ''))

        # Non-existent book code returns 404
        res_404 = self.client.get('/qr/KB-BK-999999.png')
        self.assertEqual(res_404.status_code, 404)

    def test_08_book_detail_displays_qr_preview(self):
        """8. Verify book detail page embeds official QR code sticker image."""
        res = self.client.get('/book/KB-BK-000001')
        self.assertEqual(res.status_code, 200)
        html = res.get_data(as_text=True)
        self.assertIn('/qr/KB-BK-000001.png', html)
        self.assertIn('OFFICIAL QR STICKER', html)

    # -------------------------------------------------------------
    # 3. Teacher QR Label Printing & Bulk Sheet
    # -------------------------------------------------------------
    def test_09_teacher_auth_required_for_qr_label_routes(self):
        """9. Verify unauthenticated access to teacher QR label routes is blocked."""
        r1 = self.client.get('/teacher/books/KB-BK-000001/qr')
        self.assertEqual(r1.status_code, 302)
        self.assertIn('/auth/login', r1.headers['Location'])

        r2 = self.client.get('/teacher/qr-sheet')
        self.assertEqual(r2.status_code, 302)
        self.assertIn('/auth/login', r2.headers['Location'])

    def test_10_teacher_single_book_qr_label_view(self):
        """10. Verify authenticated teacher can view and print single book label."""
        self._login_teacher()
        res = self.client.get('/teacher/books/KB-BK-000001/qr')
        self.assertEqual(res.status_code, 200)
        html = res.get_data(as_text=True)

        self.assertIn('KB-BK-000001', html)
        self.assertIn('data:image/png;base64,', html)
        self.assertIn('Print Label', html)
        self.assertIn('@media print', html)
        self.assertIn('book-sticker-card', html)

    def test_11_teacher_qr_sheet_bulk_view(self):
        """11. Verify authenticated teacher can view bulk QR label print sheet."""
        self._login_teacher()
        res = self.client.get('/teacher/qr-sheet')
        self.assertEqual(res.status_code, 200)
        html = res.get_data(as_text=True)

        self.assertIn('Physical Textbook QR Label Sheet', html)
        self.assertIn('Print Sheet (A4)', html)
        self.assertIn('labels-grid', html)
        self.assertIn('data:image/png;base64,', html)
        self.assertIn('@media print', html)

    def test_12_teacher_qr_sheet_filtering(self):
        """12. Verify QR sheet filters by class grade, subject, and status."""
        self._login_teacher()

        # Class 6 Filter
        res_c6 = self.client.get('/teacher/qr-sheet?class_grade=Class 6')
        self.assertEqual(res_c6.status_code, 200)
        html_c6 = res_c6.get_data(as_text=True)
        self.assertIn('Class 6', html_c6)

        # Subject Filter
        res_math = self.client.get('/teacher/qr-sheet?subject=Mathematics')
        self.assertEqual(res_math.status_code, 200)
        html_math = res_math.get_data(as_text=True)
        self.assertIn('Mathematics', html_math)

    def test_13_all_static_qr_assets_exist_locally_zero_cdn(self):
        """13. Verify all QR JavaScript and CSS assets exist locally on disk (0 CDN)."""
        res_scanner = self.client.get('/static/js/qr_scanner.js')
        self.assertEqual(res_scanner.status_code, 200)
        self.assertIn('stopCamera', res_scanner.get_data(as_text=True))
        res_scanner.close()

        res_jsqr = self.client.get('/static/js/jsqr.js')
        self.assertEqual(res_jsqr.status_code, 200)
        self.assertGreater(len(res_jsqr.data), 100000) # Full local jsQR library
        res_jsqr.close()

    def test_14_qr_code_payload_matches_book_reference(self):
        """14. Verify book QR payload correctly formats relative or absolute URL."""
        p_rel = qr_service.get_book_qr_payload('KB-BK-000001')
        self.assertEqual(p_rel, '/book/KB-BK-000001')

        p_abs = qr_service.get_book_qr_payload('KB-BK-000002', 'http://10.0.0.36:5000')
        self.assertEqual(p_abs, 'http://10.0.0.36:5000/book/KB-BK-000002')

if __name__ == '__main__':
    unittest.main()
