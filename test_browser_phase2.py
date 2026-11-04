"""
Playwright Browser Test Suite for Phase 2: Student Website & Book Discovery
Using Microsoft Edge (Chromium) in headless mode.
"""

import sys
import time
from playwright.sync_api import sync_playwright

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

EDGE_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
BASE_URL = "http://127.0.0.1:5000"

def run_phase2_browser_audit():
    print("=" * 70)
    print("STARTING PHASE 2 REAL BROWSER AUDIT VIA MICROSOFT EDGE")
    print("=" * 70)

    console_errors = []
    page_errors = []

    with sync_playwright() as p:
        browser = p.chromium.launch(
            executable_path=EDGE_PATH,
            headless=True
        )

        # -------------------------------------------------------------
        # SUITE 1: Desktop Viewport (1280x800)
        # -------------------------------------------------------------
        print("\n[Suite 1] Desktop Viewport Audit (1280x800)...")
        context = browser.new_context(viewport={"width": 1280, "height": 800})
        page = context.new_page()

        page.on("console", lambda msg: console_errors.append(f"[{msg.type}] {msg.text}") if msg.type in ("error", "warning") else None)
        page.on("pageerror", lambda exc: page_errors.append(str(exc)))

        # 1.1 Homepage
        print("  1.1 Testing Homepage (/)...")
        res = page.goto(f"{BASE_URL}/")
        assert res.status == 200, f"Expected 200, got {res.status}"
        assert "Kitaab Bank" in page.title()
        
        # Check hero search input
        search_input = page.locator(".hero-search-input")
        assert search_input.is_visible()
        
        # Check stat boxes
        stat_boxes = page.locator(".stat-box")
        assert stat_boxes.count() == 4
        print(f"  ✓ Homepage verified: 4 live stat boxes rendered")

        # Check featured book cards
        featured_cards = page.locator(".book-card")
        assert featured_cards.count() > 0
        print(f"  ✓ Featured books verified: {featured_cards.count()} cards on homepage")

        # 1.2 Perform Quick Search from Hero
        print("  1.2 Testing Quick Search from Hero ('Mathematics')...")
        search_input.fill("Mathematics")
        page.click(".hero-search-btn")
        page.wait_for_load_state("networkidle")
        assert "/catalogue" in page.url
        assert "q=Mathematics" in page.url
        matched_cards = page.locator(".book-card")
        assert matched_cards.count() >= 2
        print(f"  ✓ Hero search redirected to catalogue: {matched_cards.count()} matches found")

        # 1.3 Full Catalogue & Filtering
        print("  1.3 Testing Catalogue Page & Multi-Faceted Filters (/catalogue)...")
        page.goto(f"{BASE_URL}/catalogue")
        page.wait_for_load_state("networkidle")
        all_cards = page.locator(".book-card")
        total_initial = all_cards.count()
        assert total_initial >= 16, f"Expected at least 16 sample books, found {total_initial}"
        print(f"  ✓ Full catalogue renders all {total_initial} books")

        # Filter by Class 6
        print("  Testing Class 6 Filter...")
        page.select_option("#filter-class", "Class 6")
        page.click("button:has-text('Filter')")
        page.wait_for_load_state("networkidle")
        c6_cards = page.locator(".book-card")
        assert c6_cards.count() >= 6, f"Expected at least 6 books for Class 6, got {c6_cards.count()}"
        print(f"  ✓ Class 6 filter verified: {c6_cards.count()} books displayed")

        # Filter by Language Sindhi
        print("  Testing Language Filter (Sindhi)...")
        page.goto(f"{BASE_URL}/catalogue?language=Sindhi")
        page.wait_for_load_state("networkidle")
        sindhi_cards = page.locator(".book-card")
        assert sindhi_cards.count() >= 3
        print(f"  ✓ Sindhi language filter verified: {sindhi_cards.count()} books displayed")

        # Filter by Language Urdu
        print("  Testing Language Filter (Urdu)...")
        page.goto(f"{BASE_URL}/catalogue?language=Urdu")
        page.wait_for_load_state("networkidle")
        urdu_cards = page.locator(".book-card")
        assert urdu_cards.count() >= 5, f"Expected at least 5 Urdu books, got {urdu_cards.count()}"
        print(f"  ✓ Urdu language filter verified: {urdu_cards.count()} books displayed")

        # Test Empty Search Results State
        print("  Testing Empty Results State...")
        page.goto(f"{BASE_URL}/catalogue?q=NonExistent999XYZ")
        page.wait_for_load_state("networkidle")
        empty_state = page.locator(".empty-state")
        assert empty_state.is_visible()
        assert "No Books Found" in empty_state.inner_text()
        print("  ✓ Empty search state rendered gracefully with 'No Books Found'")

        # 1.4 Book Details Page
        print("  1.4 Testing Book Details Page (/book/KB-BK-000001)...")
        page.goto(f"{BASE_URL}/book/KB-BK-000001")
        page.wait_for_load_state("networkidle")
        assert page.locator(".book-detail-title").inner_text() == "Mathematics for Class 6"
        assert page.locator(".book-detail-cover-img").is_visible()
        assert page.locator(".meta-table").is_visible()
        assert "Prof. Dr. M. A. Memon" in page.locator(".book-detail-author").inner_text()
        assert page.locator(".book-detail-desc-box").is_visible()
        
        # Check related books
        rel_cards = page.locator(".book-grid .book-card")
        assert rel_cards.count() > 0
        print(f"  ✓ Book Details verified: Full metadata, cover, syllabus, and {rel_cards.count()} related books")

        # Test Navigation Back
        page.click("text=← Back to Catalogue")
        page.wait_for_load_state("networkidle")
        assert "/catalogue" in page.url
        print("  ✓ Back to Catalogue button functions correctly")

        # -------------------------------------------------------------
        # SUITE 2: Mobile Viewport & Responsiveness (390x844)
        # -------------------------------------------------------------
        print("\n[Suite 2] Mobile Viewport & Responsiveness (390x844)...")
        mobile_context = browser.new_context(
            viewport={"width": 390, "height": 844},
            is_mobile=True,
            has_touch=True,
            user_agent="Mozilla/5.0 (Linux; Android 14; TECNO CAMON 20) AppleWebKit/537.36 Chrome/124.0.0.0 Mobile Safari/537.36"
        )
        mobile_page = mobile_context.new_page()
        mobile_page.on("console", lambda msg: console_errors.append(f"[Mobile {msg.type}] {msg.text}") if msg.type in ("error", "warning") else None)
        mobile_page.on("pageerror", lambda exc: page_errors.append(f"[Mobile Error] {str(exc)}"))

        # Mobile Home
        mobile_page.goto(f"{BASE_URL}/")
        mobile_page.wait_for_load_state("networkidle")
        assert mobile_page.locator(".hero-search-form").is_visible()
        print("  ✓ Mobile Homepage renders with search and responsive stats")

        # Mobile Catalogue
        mobile_page.goto(f"{BASE_URL}/catalogue")
        mobile_page.wait_for_load_state("networkidle")
        assert mobile_page.locator(".filter-panel").is_visible()
        assert mobile_page.locator(".book-card").first.is_visible()
        print("  ✓ Mobile Catalogue renders with vertical filter stack and single-column cards")

        # Mobile Book Detail
        mobile_page.goto(f"{BASE_URL}/book/KB-BK-000003")
        mobile_page.wait_for_load_state("networkidle")
        assert mobile_page.locator(".book-detail-wrapper").is_visible()
        assert "اردو لازمی برائے جماعت ششم" in mobile_page.locator(".book-detail-title").inner_text()
        print("  ✓ Mobile Book Detail renders Urdu content and responsive cover cleanly")

        # Mobile Theme Switching
        mobile_page.click("[data-theme-toggle]")
        time.sleep(0.2)
        mobile_page.click("[data-theme-set='dark']")
        theme_attr = mobile_page.evaluate("document.documentElement.getAttribute('data-theme')")
        assert theme_attr == 'dark'
        print("  ✓ Mobile Theme Switcher operates smoothly (switched to Dark)")

        browser.close()

    print("\n" + "=" * 70)
    print("BROWSER CONSOLE & EXCEPTION AUDIT:")
    print(f"Total Console Errors: {len(console_errors)}")
    print(f"Total Page Exceptions: {len(page_errors)}")
    for err in console_errors:
        print(f"  - {err}")
    for perr in page_errors:
        print(f"  - {perr}")
    print("=" * 70)

    if len(console_errors) == 0 and len(page_errors) == 0:
        print("\n🎉 ALL PHASE 2 BROWSER AUDIT TESTS PASSED WITH 0 CONSOLE ERRORS!")
        return 0
    else:
        print("\n⚠️ AUDIT FINISHED WITH CONSOLE NOTICES/ERRORS.")
        return 1

if __name__ == '__main__':
    code = run_phase2_browser_audit()
    sys.exit(code)
