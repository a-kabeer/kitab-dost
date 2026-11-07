"""
Automated Browser Acceptance & Regression Test Suite
For Data Tables Improvement & Book Detail Navbar Overlap Resolution
Tests:
1. Column sorting & ascending/descending toggle on all data tables
2. Pagination navigation and page-size options (10, 25, 50, 100)
3. Sorting and pagination synergy (sorting across pages)
4. Table row styling in Light (#FFFFFF) and Dark (#1E293B) themes
5. Clickable rows navigation with action button click-isolation
6. Book detail cover positioning and navbar non-overlap during scrolling
"""

import unittest
from playwright.sync_api import sync_playwright

EDGE_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
BASE_URL = "http://127.0.0.1:5000"

def rgb_to_hex(rgb_str):
    if not rgb_str:
        return ""
    if rgb_str.startswith('#'):
        return rgb_str.upper()
    import re
    m = re.search(r'rgba?\s*\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)', rgb_str)
    if not m:
        return rgb_str
    nums = [int(x) for x in m.groups()]
    return f"#{nums[0]:02X}{nums[1]:02X}{nums[2]:02X}"

class TestDataTablesAndBookDetail(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pw = sync_playwright().start()
        cls.browser = cls.pw.chromium.launch(executable_path=EDGE_PATH, headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.pw.stop()

    def _login_teacher(self, page):
        page.goto(f"{BASE_URL}/auth/login")
        page.fill('input[name="username"]', 'teacher')
        page.fill('input[name="password"]', 'Teacher@123')
        page.click('button[type="submit"]')
        page.wait_for_url(f"{BASE_URL}/teacher/dashboard")
        page.wait_for_timeout(200)

    # -------------------------------------------------------------------------
    # Phase 1: Sorting, Pagination & Page-Size (10, 25, 50, 100)
    # -------------------------------------------------------------------------
    def test_01_inventory_table_sorting_and_pagination(self):
        """Verify sorting, pagination, and page-size dropdowns in Inventory table."""
        page = self.browser.new_page(viewport={"width": 1280, "height": 800})
        self._login_teacher(page)
        page.goto(f"{BASE_URL}/teacher/inventory")
        page.wait_for_selector("table.table")

        # 1. Verify Page-size selector exists with 10, 25, 50, 100
        size_select = page.locator(".table-page-size")
        self.assertTrue(size_select.is_visible(), "Page size selector should be visible")
        options = size_select.locator("option").all_inner_texts()
        self.assertEqual(options, ["10", "25", "50", "100"], "Must offer 10, 25, 50, 100 options")

        # 2. Verify default page size (10) limits visible rows
        visible_rows = page.locator("table.table tbody tr:visible").count()
        self.assertLessEqual(visible_rows, 10, "With page size 10, at most 10 rows visible")

        # 3. Change page size to 25 -> all 18 demo books become visible
        size_select.select_option("25")
        page.wait_for_timeout(200)
        visible_rows_25 = page.locator("table.table tbody tr:visible").count()
        self.assertEqual(visible_rows_25, 18, "With page size 25, all 18 books should be visible")

        # 4. Verify Column Sorting (Title column, idx 2)
        # Select page size 100 to sort all books
        size_select.select_option("100")
        page.wait_for_timeout(200)

        # Click Book Code header (idx 0)
        code_th = page.locator("table.table thead th.sortable-th").nth(0)
        code_th.click()
        page.wait_for_timeout(200)

        # Check ascending sort on Book Code
        first_code = page.locator("table.table tbody tr:visible").first.locator("bdi.kb-code").inner_text().strip()
        self.assertEqual(first_code, "KB-BK-000001", "Ascending sort first book code should be KB-BK-000001")

        # Click again for descending sort
        code_th.click()
        page.wait_for_timeout(200)
        first_code_desc = page.locator("table.table tbody tr:visible").first.locator("bdi.kb-code").inner_text().strip()
        self.assertEqual(first_code_desc, "KB-BK-000018", "Descending sort first book code should be KB-BK-000018")

        # 5. Verify Pagination Navigation with Page Size 10
        size_select.select_option("10")
        page.wait_for_timeout(200)
        
        # Click Next button
        next_btn = page.locator(".table-btn-next")
        if next_btn.is_visible():
            next_btn.click()
            page.wait_for_timeout(200)
            page_2_rows = page.locator("table.table tbody tr:visible").count()
            self.assertEqual(page_2_rows, 8, "Page 2 should show remaining 8 books (18 total - 10)")

        page.close()

    def test_02_all_teacher_data_tables_have_sorting_and_pagination(self):
        """Verify donations, requests, handovers, reports, settings all have EnhancedDataTable."""
        page = self.browser.new_page(viewport={"width": 1280, "height": 800})
        self._login_teacher(page)

        routes_to_check = [
            "/teacher/donations?status=all",
            "/teacher/requests?status=all",
            "/teacher/handovers",
            "/teacher/reports",
            "/teacher/settings?tab=backup"
        ]

        for route in routes_to_check:
            page.goto(f"{BASE_URL}{route}")
            page.wait_for_selector("table.table")
            
            # Check sortable headers
            sortable_count = page.locator("table.table thead th.sortable-th").count()
            self.assertGreater(sortable_count, 0, f"Table at {route} must have sortable column headers")

            # Check toolbar exists
            toolbars = page.locator(".table-toolbar").count()
            self.assertGreater(toolbars, 0, f"Table at {route} must have top toolbar")

            # Check page size dropdown has 10, 25, 50, 100
            first_select = page.locator(".table-page-size").first
            opts = first_select.locator("option").all_inner_texts()
            self.assertEqual(opts, ["10", "25", "50", "100"], f"Table at {route} must offer 10, 25, 50, 100")

        page.close()

    # -------------------------------------------------------------------------
    # Phase 2: Table Row Styling (Light vs Dark Theme)
    # -------------------------------------------------------------------------
    def test_03_table_row_styling_light_and_dark(self):
        """Verify Light Mode has white rows (#FFFFFF) and Dark Mode has card background (#1E293B)."""
        page = self.browser.new_page(viewport={"width": 1280, "height": 800})
        self._login_teacher(page)
        page.goto(f"{BASE_URL}/teacher/inventory")
        page.wait_for_selector("table.table tbody tr")

        # 1. Light Mode Check
        page.evaluate("() => { localStorage.setItem('kb_theme', 'light'); }")
        page.reload()
        page.wait_for_selector("table.table tbody tr")
        
        row_bg_light = page.evaluate("""() => {
            const row = document.querySelector('table.table tbody tr');
            return window.getComputedStyle(row).backgroundColor;
        }""")
        self.assertEqual(rgb_to_hex(row_bg_light), "#FFFFFF", "Light mode table row background must be white (#FFFFFF)")

        # 2. Dark Mode Check
        page.evaluate("() => { localStorage.setItem('kb_theme', 'dark'); }")
        page.reload()
        page.wait_for_selector("table.table tbody tr")

        row_bg_dark = page.evaluate("""() => {
            const row = document.querySelector('table.table tbody tr');
            return window.getComputedStyle(row).backgroundColor;
        }""")
        self.assertEqual(rgb_to_hex(row_bg_dark), "#1E293B", "Dark mode table row background must match card surface (#1E293B)")

        # Restore light theme
        page.evaluate("() => { localStorage.setItem('kb_theme', 'light'); }")
        page.close()

    # -------------------------------------------------------------------------
    # Phase 3: Clickable Rows & Action Button Click-Isolation
    # -------------------------------------------------------------------------
    def test_04_clickable_rows_and_view_buttons_removed(self):
        """Verify View buttons removed from rows and clicking row opens detail page."""
        page = self.browser.new_page(viewport={"width": 1280, "height": 800})
        self._login_teacher(page)

        # 1. Check Donations: View button removed from desktop table
        page.goto(f"{BASE_URL}/teacher/donations?status=all")
        page.wait_for_selector("table.table")
        view_btns = page.locator("table.table tbody a[title='View details']").count()
        self.assertEqual(view_btns, 0, "View details button must be removed from donations table rows")

        # Row should have data-href and clickable-row class
        first_row = page.locator("table.table tbody tr.clickable-row").first
        data_href = first_row.get_attribute("data-href")
        self.assertIn("/teacher/donations/", data_href, "Donations row must link to donation_detail")

        # Click the row -> navigates to donation detail
        first_row.click()
        page.wait_for_url("**/teacher/donations/*")
        self.assertIn("/teacher/donations/", page.url)

        # 2. Check Requests: View button removed from desktop table
        page.goto(f"{BASE_URL}/teacher/requests?status=all")
        page.wait_for_selector("table.table")
        req_view_btns = page.locator("table.table tbody a[title='View details']").count()
        self.assertEqual(req_view_btns, 0, "View details button must be removed from requests table rows")

        # Row should have data-href
        first_req_row = page.locator("table.table tbody tr.clickable-row").first
        req_href = first_req_row.get_attribute("data-href")
        self.assertIn("/teacher/requests/", req_href, "Requests row must link to request_detail")

        # Click the row -> navigates to request detail
        first_req_row.click()
        page.wait_for_url("**/teacher/requests/*")
        self.assertIn("/teacher/requests/", page.url)

        # 3. Check Handovers: View button removed
        page.goto(f"{BASE_URL}/teacher/handovers")
        page.wait_for_selector("table.table")
        ho_view_btns = page.locator("table.table tbody a[title='View detail']").count()
        self.assertEqual(ho_view_btns, 0, "View detail button must be removed from handovers table rows")

        page.close()

    def test_05_action_button_click_isolation(self):
        """Clicking action buttons inside a row must NOT trigger row navigation."""
        page = self.browser.new_page(viewport={"width": 1280, "height": 800})
        self._login_teacher(page)

        # In inventory, click the Edit button in a row
        page.goto(f"{BASE_URL}/teacher/inventory")
        page.wait_for_selector("table.table tbody tr.clickable-row")

        current_url = page.url
        edit_btn = page.locator("table.table tbody tr.clickable-row").first.locator("a[title='Edit Textbook Details']")
        edit_btn.click()
        page.wait_for_url("**/teacher/inventory/*/edit")
        self.assertIn("/edit", page.url, "Clicking Edit button must navigate to edit page, not detail page")

        page.close()

    # -------------------------------------------------------------------------
    # Phase 4: Book Detail Cover Navbar Non-Overlap
    # -------------------------------------------------------------------------
    def test_06_book_detail_navbar_non_overlap_during_scroll(self):
        """Verify book cover scrolls normally and navbar stays above page content."""
        page = self.browser.new_page(viewport={"width": 1280, "height": 800})
        page.goto(f"{BASE_URL}/book/KB-BK-000001")
        page.wait_for_selector(".book-detail-cover-card")

        # 1. Verify Header z-index is 1030
        header_z = page.evaluate("() => window.getComputedStyle(document.querySelector('header')).zIndex")
        self.assertEqual(header_z, "1030", "Header sticky-top z-index must be 1030")

        # 2. Verify Card z-index is 1 (lower than header)
        card_z = page.evaluate("() => window.getComputedStyle(document.querySelector('.book-detail-cover-card')).zIndex")
        self.assertEqual(card_z, "1", "Book cover card z-index must be 1 (lower than navbar)")

        # 3. Check positioning before scroll
        card = page.locator(".book-detail-cover-card")
        header = page.locator("header")
        initial_header_box = header.bounding_box()
        initial_card_box = card.bounding_box()

        self.assertGreater(initial_card_box['y'], initial_header_box['y'] + initial_header_box['height'], 
                           "Initial card position must be below header")

        # 4. Scroll down 400px
        page.evaluate("window.scrollTo(0, 400)")
        page.wait_for_timeout(200)

        scrolled_header_box = header.bounding_box()
        scrolled_card_box = card.bounding_box()

        # Header remains sticky at top
        self.assertEqual(scrolled_header_box['y'], 0, "Navbar must stay sticky at y=0")

        # Card has scrolled up normally
        self.assertLess(scrolled_card_box['y'], 0, "Card must scroll up naturally with page flow")

        # 5. Mobile check (390px)
        page.set_viewport_size({"width": 390, "height": 844})
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(200)

        m_card = page.locator(".book-detail-cover-card")
        m_header = page.locator("header")
        m_initial_card_box = m_card.bounding_box()
        m_initial_header_box = m_header.bounding_box()

        self.assertGreater(m_initial_card_box['y'], m_initial_header_box['y'] + m_initial_header_box['height'],
                           "On mobile, card must be below header initially")

        page.evaluate("window.scrollTo(0, 500)")
        page.wait_for_timeout(200)

        m_scrolled_header = m_header.bounding_box()
        m_scrolled_card = m_card.bounding_box()

        self.assertEqual(m_scrolled_header['y'], 0, "Mobile navbar must stay sticky at top")
        self.assertLess(m_scrolled_card['y'], 0, "Mobile card must scroll normally without sticking over content")

        page.close()

if __name__ == '__main__':
    unittest.main()
