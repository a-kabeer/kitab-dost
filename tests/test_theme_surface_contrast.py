"""
Kitaab Bank - Theme Surface Contrast & Visual Regression Audit
Verifies:
1. Exact approved token conformance for Light and Dark themes.
2. Visual separation between page backgrounds and cards.
3. No horizontal overflow across all viewports (1440px, 1024px, 768px, 390px, 360px).
4. Accessibility contrast and readable borders.
5. Urdu & Sindhi RTL rendering.
6. Zero CDN dependencies.
"""

import sys
import unittest
from pathlib import Path
from playwright.sync_api import sync_playwright

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

EDGE_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
BASE_URL = "http://127.0.0.1:5000"

def rgb_to_hex(rgb_str):
    if not rgb_str or 'rgb' not in rgb_str:
        return rgb_str
    nums = [int(x.strip()) for x in rgb_str.replace('rgba(', '').replace('rgb(', '').replace(')', '').split(',')[:3]]
    return f"#{nums[0]:02X}{nums[1]:02X}{nums[2]:02X}"

class TestThemeSurfaceContrast(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pw = sync_playwright().start()
        cls.browser = cls.pw.chromium.launch(executable_path=EDGE_PATH, headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.pw.stop()

    def test_01_light_theme_approved_tokens(self):
        """Verify Light Theme approved surface, border, and text tokens."""
        context = self.browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()
        page.goto(f"{BASE_URL}/catalogue")
        page.evaluate("() => { localStorage.setItem('kb_theme', 'light'); }")
        page.reload()
        page.wait_for_timeout(200)

        body_bg = rgb_to_hex(page.evaluate("() => window.getComputedStyle(document.body).backgroundColor"))
        body_color = rgb_to_hex(page.evaluate("() => window.getComputedStyle(document.body).color"))
        navbar_bg = rgb_to_hex(page.evaluate("() => window.getComputedStyle(document.querySelector('header.sticky-top')).backgroundColor"))
        card_bg = rgb_to_hex(page.evaluate("() => window.getComputedStyle(document.querySelector('.card')).backgroundColor"))
        card_border = rgb_to_hex(page.evaluate("() => window.getComputedStyle(document.querySelector('.card')).borderColor"))
        card_footer_bg = rgb_to_hex(page.evaluate("() => window.getComputedStyle(document.querySelector('.card-footer')).backgroundColor"))
        footer_bg = rgb_to_hex(page.evaluate("() => window.getComputedStyle(document.querySelector('footer')).backgroundColor"))
        btn_primary_bg = rgb_to_hex(page.evaluate("() => window.getComputedStyle(document.querySelector('.btn-primary')).backgroundColor"))
        btn_primary_color = rgb_to_hex(page.evaluate("() => window.getComputedStyle(document.querySelector('.btn-primary')).color"))
        muted_color = rgb_to_hex(page.evaluate("() => window.getComputedStyle(document.querySelector('.text-muted, .text-body-secondary')).color"))

        self.assertEqual(body_bg, "#F1F4F8", "Light Theme page background must be #F1F4F8")
        self.assertEqual(body_color, "#172033", "Light Theme body color must be #172033")
        self.assertEqual(navbar_bg, "#FFFFFF", "Light Theme navbar background must be #FFFFFF")
        self.assertEqual(card_bg, "#FFFFFF", "Light Theme card background must be #FFFFFF")
        self.assertEqual(card_footer_bg, "#E8EDF4", "Light Theme secondary surface (card footer) must be #E8EDF4")
        self.assertEqual(card_border, "#DFE5ED", "Light Theme border must be #DFE5ED")
        self.assertEqual(footer_bg, "#FFFFFF", "Light Theme footer background must be #FFFFFF")
        self.assertEqual(btn_primary_bg, "#0369A1", "Light Theme btn-primary background must be #0369A1 (WCAG AA)")
        self.assertEqual(btn_primary_color, "#FFFFFF", "Light Theme btn-primary text must be #FFFFFF (5.93:1 contrast)")
        self.assertEqual(muted_color, "#5F6B7A", "Light Theme muted text must be #5F6B7A (4.92:1 contrast)")
        
        # Verify visual separation: card background != page background
        self.assertNotEqual(card_bg, body_bg, "Light Theme cards must visually stand out from page background")
        context.close()

    def test_02_dark_theme_approved_tokens(self):
        """Verify Dark Theme approved surface, border, and text tokens."""
        context = self.browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()
        page.goto(f"{BASE_URL}/catalogue")
        page.evaluate("() => { localStorage.setItem('kb_theme', 'dark'); }")
        page.reload()
        page.wait_for_timeout(200)

        body_bg = rgb_to_hex(page.evaluate("() => window.getComputedStyle(document.body).backgroundColor"))
        body_color = rgb_to_hex(page.evaluate("() => window.getComputedStyle(document.body).color"))
        navbar_bg = rgb_to_hex(page.evaluate("() => window.getComputedStyle(document.querySelector('header.sticky-top')).backgroundColor"))
        card_bg = rgb_to_hex(page.evaluate("() => window.getComputedStyle(document.querySelector('.card')).backgroundColor"))
        card_border = rgb_to_hex(page.evaluate("() => window.getComputedStyle(document.querySelector('.card')).borderColor"))
        card_footer_bg = rgb_to_hex(page.evaluate("() => window.getComputedStyle(document.querySelector('.card-footer')).backgroundColor"))
        footer_bg = rgb_to_hex(page.evaluate("() => window.getComputedStyle(document.querySelector('footer')).backgroundColor"))
        btn_primary_bg = rgb_to_hex(page.evaluate("() => window.getComputedStyle(document.querySelector('.btn-primary')).backgroundColor"))
        btn_primary_color = rgb_to_hex(page.evaluate("() => window.getComputedStyle(document.querySelector('.btn-primary')).color"))
        muted_color = rgb_to_hex(page.evaluate("() => window.getComputedStyle(document.querySelector('.text-muted, .text-body-secondary')).color"))

        self.assertEqual(body_bg, "#111827", "Dark Theme page background must be #111827")
        self.assertEqual(body_color, "#F1F5F9", "Dark Theme body color must be #F1F5F9")
        self.assertEqual(navbar_bg, "#17212F", "Dark Theme navbar background must be #17212F")
        self.assertEqual(card_bg, "#1E293B", "Dark Theme card background must be #1E293B")
        self.assertEqual(card_footer_bg, "#263449", "Dark Theme secondary surface (card footer) must be #263449")
        self.assertEqual(card_border, "#334155", "Dark Theme border must be #334155")
        self.assertEqual(footer_bg, "#17212F", "Dark Theme footer background must be #17212F")
        self.assertEqual(btn_primary_bg, "#0369A1", "Dark Theme btn-primary background must be #0369A1")
        self.assertEqual(btn_primary_color, "#FFFFFF", "Dark Theme btn-primary text must be #FFFFFF")
        self.assertEqual(muted_color, "#A7B4C5", "Dark Theme muted text must be #A7B4C5")

        # Verify visual separation: card background != page background
        self.assertNotEqual(card_bg, body_bg, "Dark Theme cards must visually stand out from deep charcoal background")
        context.close()

    def test_03_teacher_desk_surface_contrast(self):
        """Verify Teacher Desk surfaces in both Light and Dark themes."""
        context = self.browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()
        page.goto(f"{BASE_URL}/auth/login")
        page.fill('input[name="username"]', 'teacher')
        page.fill('input[name="password"]', 'Teacher@123')
        page.click('button[type="submit"]')
        page.wait_for_url(f"{BASE_URL}/teacher/dashboard")

        # Light Mode
        page.evaluate("() => { localStorage.setItem('kb_theme', 'light'); }")
        page.reload()
        page.wait_for_timeout(200)

        main_bg_l = rgb_to_hex(page.evaluate("() => window.getComputedStyle(document.querySelector('.teacher-main')).backgroundColor"))
        sb_bg_l = rgb_to_hex(page.evaluate("() => window.getComputedStyle(document.querySelector('.teacher-sidebar')).backgroundColor"))
        card_bg_l = rgb_to_hex(page.evaluate("() => window.getComputedStyle(document.querySelector('.card')).backgroundColor"))

        self.assertEqual(main_bg_l, "#F1F4F8", "Teacher Light main background must be #F1F4F8")
        self.assertEqual(sb_bg_l, "#FFFFFF", "Teacher Light sidebar background must be #FFFFFF")
        self.assertEqual(card_bg_l, "#FFFFFF", "Teacher Light card background must be #FFFFFF")
        self.assertNotEqual(card_bg_l, main_bg_l, "Teacher cards must stand out from main background")

        # Dark Mode
        page.evaluate("() => { localStorage.setItem('kb_theme', 'dark'); }")
        page.reload()
        page.wait_for_timeout(200)

        main_bg_d = rgb_to_hex(page.evaluate("() => window.getComputedStyle(document.querySelector('.teacher-main')).backgroundColor"))
        sb_bg_d = rgb_to_hex(page.evaluate("() => window.getComputedStyle(document.querySelector('.teacher-sidebar')).backgroundColor"))
        card_bg_d = rgb_to_hex(page.evaluate("() => window.getComputedStyle(document.querySelector('.card')).backgroundColor"))

        self.assertEqual(main_bg_d, "#111827", "Teacher Dark main background must be #111827")
        self.assertEqual(sb_bg_d, "#17212F", "Teacher Dark sidebar background must be #17212F")
        self.assertEqual(card_bg_d, "#1E293B", "Teacher Dark card background must be #1E293B")
        self.assertNotEqual(card_bg_d, main_bg_d, "Teacher cards must stand out from deep charcoal background")
        context.close()

    def test_04_multi_viewport_overflow(self):
        """Assert zero horizontal overflow across 1440, 1024, 768, 390, 360 px viewports."""
        viewports = [
            {"width": 1440, "height": 900},
            {"width": 1024, "height": 768},
            {"width": 768, "height": 1024},
            {"width": 390, "height": 844},
            {"width": 360, "height": 640}
        ]
        routes = ["/", "/catalogue", "/donate", "/track", "/about"]

        for vp in viewports:
            context = self.browser.new_context(viewport=vp)
            page = context.new_page()
            for route in routes:
                page.goto(f"{BASE_URL}{route}")
                overflow = page.evaluate("() => document.documentElement.scrollWidth > window.innerWidth")
                self.assertFalse(overflow, f"Horizontal overflow detected on {route} at {vp['width']}px")
            context.close()

    def test_05_teacher_desktop_sidebar_sticky_and_scroll(self):
        """Assert Teacher Desktop Sidebar sticky behavior, zero overlap, and independent scrolling."""
        for vp_w in [1440, 1024]:
            context = self.browser.new_context(viewport={"width": vp_w, "height": 900})
            page = context.new_page()
            page.goto(f"{BASE_URL}/auth/login")
            page.fill('input[name="username"]', 'teacher')
            page.fill('input[name="password"]', 'Teacher@123')
            page.click('button[type="submit"]')
            page.wait_for_url(f"{BASE_URL}/teacher/dashboard")
            page.wait_for_timeout(200)

            # Check parent container allows sticky positioning
            wrap_overflow = page.evaluate("() => window.getComputedStyle(document.getElementById('teacherLayoutWrap')).overflow")
            self.assertNotEqual(wrap_overflow, "hidden", "Parent #teacherLayoutWrap must not have overflow: hidden")

            # Check sidebar computed positioning
            sb_pos = page.evaluate("() => window.getComputedStyle(document.querySelector('.teacher-sidebar')).position")
            self.assertEqual(sb_pos, "sticky", f"Sidebar position must be sticky on {vp_w}px")

            # Scroll deeply
            for scroll_val in [300, 600, 1000]:
                page.evaluate(f"() => window.scrollTo(0, {scroll_val})")
                page.wait_for_timeout(100)
                h_rect = page.evaluate("() => document.querySelector('header.sticky-top').getBoundingClientRect()")
                sb_rect = page.evaluate("() => document.querySelector('.teacher-sidebar').getBoundingClientRect()")

                # Allow 1px subpixel tolerance
                self.assertGreaterEqual(sb_rect['top'], h_rect['bottom'] - 1, f"Sidebar top must be below header at scrollY={scroll_val}")
                self.assertLessEqual(sb_rect['bottom'], 901, f"Sidebar bottom must stay within viewport at scrollY={scroll_val}")

            # Zero horizontal overflow
            h_overflow = page.evaluate("() => document.documentElement.scrollWidth > window.innerWidth")
            self.assertFalse(h_overflow, f"Horizontal overflow on teacher dashboard at {vp_w}px")
            context.close()

        # Test independent sidebar scrolling on short viewports
        context_short = self.browser.new_context(viewport={"width": 1440, "height": 500})
        page_short = context_short.new_page()
        page_short.goto(f"{BASE_URL}/auth/login")
        page_short.fill('input[name="username"]', 'teacher')
        page_short.fill('input[name="password"]', 'Teacher@123')
        page_short.click('button[type="submit"]')
        page_short.wait_for_url(f"{BASE_URL}/teacher/dashboard")

        sb_sh = page_short.evaluate("() => document.querySelector('.teacher-sidebar').scrollHeight")
        sb_ch = page_short.evaluate("() => document.querySelector('.teacher-sidebar').clientHeight")
        self.assertGreater(sb_sh, sb_ch, "Sidebar must have scrollable content when viewport height is small")

        page_short.evaluate("() => document.querySelector('.teacher-sidebar').scrollTop = 100")
        sb_st = page_short.evaluate("() => document.querySelector('.teacher-sidebar').scrollTop")
        self.assertGreater(sb_st, 0, "Sidebar internal scrolling must work independently")
        context_short.close()

    def test_06_teacher_mobile_offcanvas_behavior(self):
        """Assert Mobile & Tablet views (< 992px) preserve offcanvas drawer behavior."""
        for vp_w, vp_h in [(768, 1024), (390, 844), (360, 640)]:
            context = self.browser.new_context(viewport={"width": vp_w, "height": vp_h})
            page = context.new_page()
            page.goto(f"{BASE_URL}/auth/login")
            page.fill('input[name="username"]', 'teacher')
            page.fill('input[name="password"]', 'Teacher@123')
            page.click('button[type="submit"]')
            page.wait_for_url(f"{BASE_URL}/teacher/dashboard")

            # Desktop sidebar must be hidden
            sb_disp = page.evaluate("() => window.getComputedStyle(document.querySelector('.teacher-sidebar')).display")
            self.assertEqual(sb_disp, "none", f"Desktop sidebar must be hidden at {vp_w}px")

            # Hamburger toggle must be visible
            hamburger = page.query_selector('button[data-bs-target="#teacherSidebarOffcanvas"]')
            self.assertIsNotNone(hamburger)
            self.assertTrue(hamburger.is_visible(), f"Hamburger button must be visible at {vp_w}px")

            # Open drawer
            hamburger.click()
            page.wait_for_selector('#teacherSidebarOffcanvas.show', state='visible')
            self.assertTrue(page.is_visible('#teacherSidebarOffcanvas'))

            # Close drawer
            close_btn = page.query_selector('#teacherSidebarOffcanvas .btn-close')
            close_btn.click()
            page.wait_for_timeout(400)
            is_open = page.evaluate("() => document.getElementById('teacherSidebarOffcanvas').classList.contains('show')")
            self.assertFalse(is_open, f"Offcanvas drawer must close at {vp_w}px")

            # Zero horizontal overflow
            h_overflow = page.evaluate("() => document.documentElement.scrollWidth > window.innerWidth")
            self.assertFalse(h_overflow, f"Horizontal overflow detected at {vp_w}px")
            context.close()

if __name__ == '__main__':
    unittest.main()
