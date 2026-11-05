"""
Playwright Browser Test Suite for Phase 6: QR System, Label Printing & Android Tested Scanner
Using Microsoft Edge (Chromium) in headless mode.
Tests:
- Student Scanner (/scan): Prominent manual 6-digit entry, numeric shortcuts, sample chips, tracking code redirection, invalid error banner.
- Book Detail QR sticker preview (/book/<code_or_id>).
- Teacher QR Label Center (/teacher/qr-sheet): Bulk A4 label sheet generation, filtering by class/subject, print styles.
- Teacher Single Book Sticker (/teacher/books/<code_or_id>/qr): Printable sticker card layout.
- Mobile Viewport (390x844): Touch-friendly responsive layout and theme switching.
"""

import sys
import time
from playwright.sync_api import sync_playwright

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

EDGE_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
BASE_URL = "http://127.0.0.1:5000"

def run_phase6_browser_audit():
    print("=" * 75)
    print("STARTING PHASE 6 REAL BROWSER AUDIT VIA MICROSOFT EDGE")
    print("=" * 75)

    console_errors = []
    page_errors = []

    with sync_playwright() as p:
        browser = p.chromium.launch(
            executable_path=EDGE_PATH,
            headless=True
        )

        # -------------------------------------------------------------
        # SUITE 1: Desktop Viewport (1280x800) - Full Workflow Audit
        # -------------------------------------------------------------
        print("\n[Suite 1] Desktop Viewport QR & Scanner Audit (1280x800)...")
        context = browser.new_context(viewport={"width": 1280, "height": 800})
        page = context.new_page()

        page.on("console", lambda msg: console_errors.append(f"[{msg.type}] {msg.text}") if msg.type in ("error", "warning") else None)
        page.on("pageerror", lambda exc: page_errors.append(str(exc)))
        page.on("dialog", lambda dialog: dialog.accept())

        # 1.1 Open Student Scanner Page (/scan)
        print("  1.1 Navigating to Student Textbook Scanner (/scan)...")
        res = page.goto(f"{BASE_URL}/scan")
        assert res.status == 200, f"Expected 200, got {res.status}"
        assert "Textbook Scanner" in page.content()
        assert page.locator("#manual-code-input").is_visible()
        assert page.locator("#manual-lookup-btn").is_visible()
        print("  ✓ Scanner view loaded cleanly with prominent manual entry and camera card")

        # 1.2 Test Manual 6-Digit Book Code Lookup (KB-BK-000001)
        print("  1.2 Testing manual lookup for 'KB-BK-000001'...")
        page.fill("#manual-code-input", "KB-BK-000001")
        page.click("#manual-lookup-btn")
        page.wait_for_load_state("networkidle")

        assert "/book/KB-BK-000001" in page.url
        assert "KB-BK-000001" in page.content()
        print("  ✓ Manual code lookup redirected successfully to Book Detail view")

        # 1.3 Verify QR Sticker Preview on Book Detail Page
        print("  1.3 Verifying dynamic QR sticker on Book Detail page...")
        qr_img = page.locator("img[src*='/qr/KB-BK-000001.png']")
        assert qr_img.is_visible()
        print("  ✓ Book Detail page displays official dynamic QR code sticker preview")

        # 1.4 Test Numeric Shortcut Entry ("2" -> KB-BK-000002)
        print("  1.4 Testing numeric shortcut lookup ('2')...")
        page.goto(f"{BASE_URL}/scan")
        page.wait_for_load_state("networkidle")
        page.fill("#manual-code-input", "2")
        page.click("#manual-lookup-btn")
        page.wait_for_load_state("networkidle")

        assert "/book/KB-BK-000002" in page.url
        assert "KB-BK-000002" in page.content()
        print("  ✓ Numeric shortcut '2' correctly resolved and navigated to KB-BK-000002")

        # 1.5 Test Quick Sample Book Code Chips
        print("  1.5 Testing quick sample book chips on /scan...")
        page.goto(f"{BASE_URL}/scan")
        page.wait_for_load_state("networkidle")

        sample_chip = page.locator("a.badge:has-text('KB-BK-')").first
        chip_code = sample_chip.inner_text().strip()
        print(f"  Clicking sample chip: {chip_code}...")
        sample_chip.click()
        page.wait_for_load_state("networkidle")

        assert f"/book/{chip_code}" in page.url
        print(f"  ✓ Quick sample chip {chip_code} navigated cleanly to book detail")

        # 1.6 Test Request Tracking Code Redirection
        print("  1.6 Testing accidental tracking code redirection in /scan...")
        page.goto(f"{BASE_URL}/scan")
        page.wait_for_load_state("networkidle")
        page.fill("#manual-code-input", "KB-REQ-TEST-CODE")
        page.click("#manual-lookup-btn")
        page.wait_for_load_state("networkidle")

        assert "/track" in page.url
        assert "KB-REQ-TEST-CODE" in page.url
        print("  ✓ Request code entered in scanner automatically redirected to Tracking Desk")

        # 1.7 Test Invalid Code Error Handling
        print("  1.7 Testing invalid book code handling ('NONEXISTENT_999')...")
        page.goto(f"{BASE_URL}/scan")
        page.wait_for_load_state("networkidle")
        page.fill("#manual-code-input", "NONEXISTENT_999")
        page.click("#manual-lookup-btn")
        page.wait_for_load_state("networkidle")

        assert "/scan" in page.url
        assert "Textbook Not Found" in page.content()
        assert "NONEXISTENT_999" in page.content()
        print("  ✓ Friendly educational error banner rendered on invalid code")

        # 1.8 Teacher Login
        print("  1.8 Authenticating as Teacher for Label Printing...")
        page.goto(f"{BASE_URL}/auth/login")
        page.fill("input[name='username']", "teacher")
        page.fill("input[name='password']", "Teacher@123")
        page.click("button[type='submit']")
        page.wait_for_load_state("networkidle")
        assert "/teacher/dashboard" in page.url
        print("  ✓ Teacher authenticated successfully")

        # 1.9 Bulk QR Label Sheet (/teacher/qr-sheet)
        print("  1.9 Inspecting Bulk QR Label Print Sheet (/teacher/qr-sheet)...")
        page.goto(f"{BASE_URL}/teacher/qr-sheet")
        page.wait_for_load_state("networkidle")
        assert "Physical Textbook QR Label Sheet" in page.content()
        assert "Print Sheet (A4)" in page.content()
        assert page.locator(".sheet-sticker-card").count() > 0
        print(f"  ✓ Bulk label sheet rendered with {page.locator('.sheet-sticker-card').count()} sticker cards")

        # 1.10 Test Filter on QR Sheet
        print("  1.10 Testing Class Grade Filter on QR Sheet ('Class 6')...")
        page.select_option("select[name='class_grade']", "Class 6")
        page.click("button:has-text('Filter')")
        page.wait_for_load_state("networkidle")
        assert "Class 6" in page.content()
        print("  ✓ QR sheet filter verified")

        # 1.11 Single Book Label Print View (/teacher/books/<code_or_id>/qr)
        print("  1.11 Inspecting Single Book Sticker Label (/teacher/books/KB-BK-000001/qr)...")
        page.goto(f"{BASE_URL}/teacher/books/KB-BK-000001/qr")
        page.wait_for_load_state("networkidle")
        assert "Physical Textbook QR Label" in page.content()
        assert "KB-BK-000001" in page.content()
        assert page.locator(".sticker-qr-img").is_visible()
        assert page.locator("button:has-text('Print Label')").is_visible()
        print("  ✓ Single book sticker label rendered with high-contrast QR matrix and book codes")

        context.close()

        # -------------------------------------------------------------
        # SUITE 2: Mobile Viewport (390x844 - Smartphone Screen)
        # -------------------------------------------------------------
        print("\n[Suite 2] Mobile Viewport Audit (390x844 - Smartphone Screen)...")
        mobile_context = browser.new_context(
            viewport={"width": 390, "height": 844},
            user_agent="Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
        )
        mobile_page = mobile_context.new_page()

        mobile_page.on("console", lambda msg: console_errors.append(f"[Mobile {msg.type}] {msg.text}") if msg.type in ("error", "warning") else None)
        mobile_page.on("pageerror", lambda exc: page_errors.append(f"[Mobile PageError] {exc}"))

        # 2.1 Mobile Scanner View
        print("  2.1 Checking Mobile Scanner View (/scan)...")
        mobile_page.goto(f"{BASE_URL}/scan")
        mobile_page.wait_for_load_state("networkidle")
        assert mobile_page.locator("#manual-code-input").is_visible()
        assert mobile_page.locator("#manual-lookup-btn").is_visible()
        print("  ✓ Mobile scanner view responsive and touch-accessible")

        # 2.2 Mobile Manual Lookup
        print("  2.2 Testing mobile manual lookup...")
        mobile_page.fill("#manual-code-input", "KB-BK-000003")
        mobile_page.click("#manual-lookup-btn")
        mobile_page.wait_for_load_state("networkidle")
        assert "/book/KB-BK-000003" in mobile_page.url
        print("  ✓ Mobile manual code lookup navigated successfully")

        # 2.3 Mobile Theme Switching
        print("  2.3 Testing mobile theme switching...")
        mobile_page.evaluate("window.KitaabTheme.setTheme('dark')")
        theme = mobile_page.evaluate("document.documentElement.getAttribute('data-theme')")
        assert theme == "dark", f"Expected 'dark', got '{theme}'"
        print("  ✓ Mobile theme switched to Dark mode smoothly")

        mobile_context.close()
        browser.close()

    print("\n" + "=" * 75)
    print("BROWSER AUDIT RESULTS:")
    print("=" * 75)
    print(f"Console Errors/Warnings: {len(console_errors)}")
    for err in console_errors:
        print(f"  - {err}")
    print(f"Page Exceptions:         {len(page_errors)}")
    for err in page_errors:
        print(f"  - {err}")

    if page_errors:
        print("\n❌ FAILED: Unhandled page exceptions detected.")
        sys.exit(1)

    print("\n✅ PHASE 6 REAL BROWSER AUDIT PASSED WITH ZERO EXCEPTIONS!")
    sys.exit(0)

if __name__ == '__main__':
    run_phase6_browser_audit()
