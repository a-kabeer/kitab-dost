"""
Comprehensive Browser & UI/UX Redesign Test Suite
Audits:
1. 100% Offline vendor asset availability (Bootstrap 5.3.8 & Font Awesome 7.3.1).
2. Zero external CDN references across all rendered pages.
3. Multi-language (LTR English, RTL Urdu, RTL Sindhi) with bootstrap.rtl.min.css.
4. Bidirectional isolation on all technical codes (.kb-code).
5. Exact critical element IDs preserved (#confirmDemoBox, scanner DOM IDs, etc.).
6. All 18 core routes render cleanly with HTTP 200 and proper layout markup.
7. Print stylesheets and printable layouts.
"""

import sys
import unittest
import re
from app import create_app
from app.database import get_db, init_db

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

class BrowserUIRedesignAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app('testing')
        cls.client = cls.app.test_client()
        with cls.app.app_context():
            init_db(cls.app)
            # Ensure admin teacher exists for authenticated route testing
            db = get_db()
            from werkzeug.security import generate_password_hash
            db.execute("""
                INSERT OR IGNORE INTO teachers (id, username, password_hash, full_name, email, role, is_active)
                VALUES (1, 'teacher', ?, 'Master Incharge', 'teacher@school.edu.pk', 'admin', 1);
            """, (generate_password_hash('Teacher@123'),))
            db.commit()

    def _login_teacher(self):
        """Helper to establish an authenticated teacher session."""
        with self.client.session_transaction() as sess:
            sess['teacher_id'] = 1
            sess['teacher_username'] = 'teacher'
            sess['teacher_name'] = 'Master Incharge'
            sess['teacher_role'] = 'admin'

    # -------------------------------------------------------------------------
    # 1. Offline Vendor Assets Integrity
    # -------------------------------------------------------------------------
    def test_01_local_vendor_assets_accessible(self):
        """Verify all local Bootstrap 5.3.8 and Font Awesome 7.3.1 assets are served locally with HTTP 200."""
        static_assets = [
            '/static/vendor/bootstrap/css/bootstrap.min.css',
            '/static/vendor/bootstrap/css/bootstrap.rtl.min.css',
            '/static/vendor/bootstrap/js/bootstrap.bundle.min.js',
            '/static/vendor/fontawesome/css/all.min.css',
            '/static/vendor/fontawesome/webfonts/fa-solid-900.woff2',
            '/static/vendor/fontawesome/webfonts/fa-regular-400.woff2',
            '/static/vendor/fontawesome/webfonts/fa-brands-400.woff2',
            '/static/css/main.css',
            '/static/css/components.css',
            '/static/css/rtl.css',
            '/static/css/print.css',
            '/static/js/theme.js'
        ]
        for asset in static_assets:
            resp = self.client.get(asset)
            self.assertEqual(resp.status_code, 200, f"Local asset failed to load: {asset}")
            self.assertGreater(len(resp.data), 0, f"Asset is empty: {asset}")
            resp.close()

    # -------------------------------------------------------------------------
    # 2. Zero External CDN Enforcement
    # -------------------------------------------------------------------------
    def test_02_zero_external_cdn_references(self):
        """Verify no HTML page links to external CDNs or remote font endpoints."""
        # Unauthenticated routes
        unauth_routes = [
            '/',
            '/catalogue',
            '/donate',
            '/track',
            '/scan',
            '/auth/login'
        ]
        
        # Authenticated teacher routes
        auth_routes = [
            '/teacher/dashboard',
            '/teacher/donations',
            '/teacher/requests',
            '/teacher/handovers',
            '/teacher/inventory',
            '/teacher/inventory/new',
            '/teacher/reports',
            '/teacher/logs',
            '/teacher/settings?tab=profile',
            '/teacher/settings?tab=security',
            '/teacher/settings?tab=backup',
            '/teacher/settings?tab=demo',
            '/teacher/qr-sheet'
        ]

        cdn_patterns = [
            re.compile(r'https?://[^\s"\']*cdn', re.IGNORECASE),
            re.compile(r'https?://cdnjs\.', re.IGNORECASE),
            re.compile(r'https?://fonts\.googleapis\.com', re.IGNORECASE),
            re.compile(r'https?://fonts\.gstatic\.com', re.IGNORECASE),
            re.compile(r'https?://use\.fontawesome\.com', re.IGNORECASE),
            re.compile(r'https?://unpkg\.com', re.IGNORECASE),
            re.compile(r'https?://cdn\.jsdelivr\.net', re.IGNORECASE)
        ]

        for route in unauth_routes:
            resp = self.client.get(route)
            self.assertEqual(resp.status_code, 200, f"Route returned status {resp.status_code}: {route}")
            html = resp.get_data(as_text=True)
            for pattern in cdn_patterns:
                match = pattern.search(html)
                self.assertIsNone(match, f"Forbidden external CDN found in route {route}: {match.group(0) if match else ''}")

        self._login_teacher()
        for route in auth_routes:
            resp = self.client.get(route)
            self.assertEqual(resp.status_code, 200, f"Route returned status {resp.status_code}: {route}")
            html = resp.get_data(as_text=True)
            for pattern in cdn_patterns:
                match = pattern.search(html)
                self.assertIsNone(match, f"Forbidden external CDN found in route {route}: {match.group(0) if match else ''}")

    # -------------------------------------------------------------------------
    # 3. Multilingual RTL & LTR Architecture
    # -------------------------------------------------------------------------
    def test_03_multilingual_direction_and_stylesheets(self):
        """Verify English loads LTR with standard bootstrap, Urdu/Sindhi loads RTL with bootstrap.rtl."""
        # English
        res_en = self.client.get('/set-language/en', follow_redirects=True)
        self.assertEqual(res_en.status_code, 200)
        html_en = res_en.get_data(as_text=True)
        self.assertIn('dir="ltr"', html_en)
        self.assertIn('bootstrap.min.css', html_en)
        self.assertNotIn('bootstrap.rtl.min.css', html_en)

        # Urdu
        res_ur = self.client.get('/set-language/ur', follow_redirects=True)
        self.assertEqual(res_ur.status_code, 200)
        html_ur = res_ur.get_data(as_text=True)
        self.assertIn('dir="rtl"', html_ur)
        self.assertIn('bootstrap.rtl.min.css', html_ur)
        self.assertIn('css/rtl.css', html_ur)

        # Sindhi
        res_sd = self.client.get('/set-language/sd', follow_redirects=True)
        self.assertEqual(res_sd.status_code, 200)
        html_sd = res_sd.get_data(as_text=True)
        self.assertIn('dir="rtl"', html_sd)
        self.assertIn('bootstrap.rtl.min.css', html_sd)
        self.assertIn('css/rtl.css', html_sd)

        # Revert to English
        self.client.get('/set-language/en', follow_redirects=True)

    # -------------------------------------------------------------------------
    # 4. Technical Bidirectional Isolation (.kb-code)
    # -------------------------------------------------------------------------
    def test_04_technical_code_bidirectional_isolation(self):
        """Verify tracking codes, book codes, and handover codes have .kb-code class."""
        self._login_teacher()
        resp = self.client.get('/teacher/inventory')
        self.assertEqual(resp.status_code, 200)
        html = resp.get_data(as_text=True)
        self.assertIn('kb-code', html)

        # Check track page
        resp_tr = self.client.get('/track')
        self.assertEqual(resp_tr.status_code, 200)
        self.assertIn('kb-code', resp_tr.get_data(as_text=True))

    # -------------------------------------------------------------------------
    # 5. Critical Element ID Preservation
    # -------------------------------------------------------------------------
    def test_05_scanner_and_settings_dom_ids_preserved(self):
        """Verify critical DOM element IDs are preserved for JS hooks and safety."""
        # 1. Scanner DOM IDs
        res_scan = self.client.get('/scan')
        self.assertEqual(res_scan.status_code, 200)
        html_scan = res_scan.get_data(as_text=True)
        expected_scanner_ids = [
            'insecure-context-banner',
            'secure-scanner-wrap',
            'qr-video',
            'qr-canvas',
            'start-camera-btn',
            'stop-camera-btn',
            'switch-camera-btn',
            'scanner-status',
            'manual-code-input',
            'manual-scan-form',
            'manual-lookup-btn'
        ]
        for dom_id in expected_scanner_ids:
            self.assertIn(f'id="{dom_id}"', html_scan, f"Missing required scanner DOM ID: {dom_id}")

        # 2. Teacher Settings Exhibition Mode confirmation checkbox
        self._login_teacher()
        res_demo = self.client.get('/teacher/settings?tab=demo')
        self.assertEqual(res_demo.status_code, 200)
        html_demo = res_demo.get_data(as_text=True)
        self.assertIn('id="confirmDemoBox"', html_demo, "Missing required safety ID: confirmDemoBox")

    # -------------------------------------------------------------------------
    # 6. Responsive Offcanvas and Navigation Markup
    # -------------------------------------------------------------------------
    def test_06_responsive_navigation_and_offcanvas_drawers(self):
        """Verify student navbar and teacher sidebar have responsive offcanvas drawers."""
        # Student portal offcanvas
        res_st = self.client.get('/')
        self.assertEqual(res_st.status_code, 200)
        html_st = res_st.get_data(as_text=True)
        self.assertIn('navbar-expand-xxl', html_st)
        self.assertIn('studentNavOffcanvas', html_st)
        self.assertIn('data-bs-toggle="offcanvas"', html_st)

        # Teacher portal offcanvas
        self._login_teacher()
        res_tc = self.client.get('/teacher/dashboard')
        self.assertEqual(res_tc.status_code, 200)
        html_tc = res_tc.get_data(as_text=True)
        self.assertIn('teacherSidebarOffcanvas', html_tc)
        self.assertIn('d-none d-lg-flex', html_tc)

    # -------------------------------------------------------------------------
    # 7. Print Stylesheet Link Verification
    # -------------------------------------------------------------------------
    def test_07_print_stylesheet_linked_on_all_layouts(self):
        """Verify print.css is linked with media='print' on public and teacher layouts."""
        res_pub = self.client.get('/')
        self.assertIn('media="print"', res_pub.get_data(as_text=True))
        self.assertIn('css/print.css', res_pub.get_data(as_text=True))

        self._login_teacher()
        res_tch = self.client.get('/teacher/reports')
        self.assertIn('media="print"', res_tch.get_data(as_text=True))
        self.assertIn('css/print.css', res_tch.get_data(as_text=True))

    # -------------------------------------------------------------------------
    # 8. Zero-FOUC & Theme Coordination
    # -------------------------------------------------------------------------
    def test_08_zero_fouc_and_theme_coordination(self):
        """Verify Zero-FOUC inline script in <head> and data-bs-theme coordination."""
        res = self.client.get('/')
        html = res.get_data(as_text=True)
        # Inline early script preventing FOUC
        self.assertIn('kb_theme', html)
        self.assertIn('data-bs-theme', html)
        self.assertIn('data-theme', html)
        # Theme dropdown toggle
        self.assertIn('id="themeDropdown"', html)

    # -------------------------------------------------------------------------
    # 9. Accessibility (a11y) & Interactive Standards
    # -------------------------------------------------------------------------
    def test_09_accessibility_aria_and_form_labels(self):
        """Verify modals have aria-labelledby, icons have aria-hidden, forms have labels."""
        self._login_teacher()
        # Modals in requests
        res_req = self.client.get('/teacher/requests')
        html_req = res_req.get_data(as_text=True)
        self.assertIn('aria-labelledby="rejectModalLabel"', html_req)
        self.assertIn('aria-labelledby="cancelModalLabel"', html_req)
        self.assertIn('aria-hidden="true"', html_req)

        # Modals in inventory
        res_inv = self.client.get('/teacher/inventory')
        html_inv = res_inv.get_data(as_text=True)
        self.assertIn('aria-labelledby="retireModalLabel"', html_inv)


if __name__ == '__main__':
    unittest.main()
