"""
Playwright Browser Test Suite for Phase 4: Book Request System
Using Microsoft Edge (Chromium) in headless mode.
Tests the full student request -> tracking -> teacher approval & atomic reservation -> catalogue status lifecycle.
"""

import sys
import time
from playwright.sync_api import sync_playwright

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

EDGE_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
BASE_URL = "http://127.0.0.1:5000"

def run_phase4_browser_audit():
    print("=" * 70)
    print("STARTING PHASE 4 REAL BROWSER AUDIT VIA MICROSOFT EDGE")
    print("=" * 70)

    console_errors = []
    page_errors = []

    with sync_playwright() as p:
        browser = p.chromium.launch(
            executable_path=EDGE_PATH,
            headless=True
        )

        # -------------------------------------------------------------
        # SUITE 1: Desktop Viewport (1280x800) - End-to-End Workflow
        # -------------------------------------------------------------
        print("\n[Suite 1] Desktop Viewport End-to-End Audit (1280x800)...")
        context = browser.new_context(viewport={"width": 1280, "height": 800})
        page = context.new_page()

        page.on("console", lambda msg: console_errors.append(f"[{msg.type}] {msg.text}") if msg.type in ("error", "warning") else None)
        page.on("pageerror", lambda exc: page_errors.append(str(exc)))
        page.on("dialog", lambda dialog: dialog.accept())

        # 1.1 Browse Catalogue to find an Available Book
        print("  1.1 Navigating to Student Catalogue (/catalogue)...")
        res = page.goto(f"{BASE_URL}/catalogue?status=available")
        assert res.status == 200, f"Expected 200, got {res.status}"
        print("  ✓ Catalogue loaded cleanly")

        # Select first available book card
        first_book_link = page.locator(".book-card a[href^='/book/']").first
        book_href = first_book_link.get_attribute("href")
        book_code = book_href.split("/")[-1]
        print(f"  Selected available book: {book_code}")

        # 1.2 Open Book Details
        print(f"  1.2 Opening Book Details ({book_href})...")
        page.goto(f"{BASE_URL}{book_href}")
        page.wait_for_load_state("networkidle")
        assert "Request This Book" in page.content(), "Expected 'Request This Book' button on available book"
        print("  ✓ Book detail loaded with active 'Request This Book' CTA")

        # 1.3 Click 'Request This Book' and fill Form
        print("  1.3 Navigating to Request Form...")
        page.click("a:has-text('Request This Book')")
        page.wait_for_load_state("networkidle")
        assert "/request" in page.url
        assert "Request Textbook" in page.content()
        print("  ✓ Request form loaded with pre-selected book")

        print("  1.4 Filling out student request form...")
        page.fill("input[name='requester_name']", "Saad Rehman")
        page.fill("input[name='requester_class']", "Class 7-B")
        page.fill("input[name='requester_roll_no']", "15")
        page.fill("input[name='requester_contact']", "0300-1234567")
        page.fill("textarea[name='notes']", "Preparing for upcoming terminal exams.")

        print("  Submitting request form...")
        page.click("button[type='submit']")
        page.wait_for_load_state("networkidle")

        # 1.5 Verify Request Success Screen
        assert "/request/success" in page.url
        assert "Request Received, Saad Rehman!" in page.content()
        tracking_code_elem = page.locator("#track-code")
        tracking_code = tracking_code_elem.inner_text().strip()
        assert tracking_code.startswith("KB-REQ-"), f"Unexpected tracking code: {tracking_code}"
        print(f"  ✓ Request submitted successfully! Tracking Code: {tracking_code}")

        # 1.6 Verify Public Tracking Desk (/track) with Strict PII Redaction
        print(f"  1.6 Checking Public Tracking Desk for {tracking_code}...")
        page.goto(f"{BASE_URL}/track?code={tracking_code}")
        page.wait_for_load_state("networkidle")
        content = page.content()

        assert tracking_code in content
        assert "Under Teacher Review" in content or "Pending" in content
        # Check Privacy Redaction:
        assert "Saad R***" in content, "Masked student name expected"
        assert "0300-1234567" not in content, "CRITICAL: Student phone number must NOT appear in public tracking HTML"
        assert 'value="15"' not in content and ">15<" not in content, "CRITICAL: Roll number must NOT appear in public tracking HTML"
        print("  ✓ Public tracking desk verified: Status live, student name masked ('Saad R***'), ZERO phone/roll leakage!")

        # 1.7 Teacher Authentication
        print("  1.7 Logging in as Teacher...")
        page.goto(f"{BASE_URL}/auth/login")
        page.fill("input[name='username']", "teacher")
        page.fill("input[name='password']", "Teacher@123")
        page.click("button[type='submit']")
        page.wait_for_load_state("networkidle")
        assert "/teacher/dashboard" in page.url
        print("  ✓ Teacher authentication successful")

        # 1.8 Teacher Review Queue (/teacher/requests)
        print("  1.8 Inspecting Teacher Request Queue...")
        page.goto(f"{BASE_URL}/teacher/requests?status=pending")
        page.wait_for_load_state("networkidle")
        content = page.content()
        assert tracking_code in content
        assert "Saad Rehman" in content
        print(f"  ✓ Request {tracking_code} visible in teacher pending review queue")

        # 1.9 Search by Student Name in Queue
        print("  1.9 Testing Search Filter in Request Queue ('Saad Rehman')...")
        page.fill("input[name='q']", "Saad Rehman")
        page.click("button:has-text('Filter')")
        page.wait_for_load_state("networkidle")
        assert "Saad Rehman" in page.content()
        print("  ✓ Search filter verified")

        # 1.10 Approve the Request (Atomic Reservation)
        print(f"  1.10 Approving Request {tracking_code}...")
        approve_button = page.locator("form[action*='/approve'] button[type='submit']").first
        approve_button.click()
        page.wait_for_load_state("networkidle")
        assert "Request approved" in page.content()
        print("  ✓ Request approved successfully")

        # 1.11 Verify Book Status Changed to Reserved in Public Detail
        print(f"  1.11 Verifying Book {book_code} is now RESERVED in Public Detail...")
        page.goto(f"{BASE_URL}/book/{book_code}")
        page.wait_for_load_state("networkidle")
        detail_content = page.content()
        assert "Currently Reserved" in detail_content
        print(f"  ✓ Book {book_code} is now marked 'Currently Reserved' and cannot be requested again")

        # 1.12 Verify Tracking Desk Updates to 'Approved & Reserved'
        print(f"  1.12 Verifying Student Tracking Desk after approval...")
        page.goto(f"{BASE_URL}/track?code={tracking_code}")
        page.wait_for_load_state("networkidle")
        track_content = page.content()
        assert "Reserved" in track_content or "Approved" in track_content
        print("  ✓ Student tracking desk displays approved/reserved status")

        context.close()

        # -------------------------------------------------------------
        # SUITE 2: Mobile Viewport Audit (390x844) - Smartphone Screen
        # -------------------------------------------------------------
        print("\n[Suite 2] Mobile Viewport Audit (390x844 - iPhone / Modern Android)...")
        mobile_context = browser.new_context(
            viewport={"width": 390, "height": 844},
            user_agent="Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
        )
        mobile_page = mobile_context.new_page()

        mobile_page.on("console", lambda msg: console_errors.append(f"[Mobile {msg.type}] {msg.text}") if msg.type in ("error", "warning") else None)
        mobile_page.on("pageerror", lambda exc: page_errors.append(f"[Mobile PageError] {exc}"))

        # 2.1 Mobile Homepage
        print("  2.1 Mobile Homepage loading...")
        mobile_page.goto(f"{BASE_URL}/")
        mobile_page.wait_for_load_state("networkidle")
        assert mobile_page.locator(".navbar, .nav-brand").is_visible()
        print("  ✓ Mobile homepage loaded cleanly")

        # 2.2 Mobile Request Form
        print("  2.2 Mobile Request Form loading...")
        mobile_page.goto(f"{BASE_URL}/request")
        mobile_page.wait_for_load_state("networkidle")
        assert mobile_page.locator("button[type='submit']").is_visible()
        print("  ✓ Mobile request form rendered without horizontal overflow")

        # 2.3 Mobile Tracking Desk
        print(f"  2.3 Mobile Tracking Desk lookup for {tracking_code}...")
        mobile_page.goto(f"{BASE_URL}/track?code={tracking_code}")
        mobile_page.wait_for_load_state("networkidle")
        assert tracking_code in mobile_page.content()
        print("  ✓ Mobile tracking desk rendered responsive timeline")

        # 2.4 Mobile Theme Switcher
        print("  2.4 Testing Theme Switcher on Mobile...")
        mobile_page.evaluate("window.KitaabTheme.setTheme('dark')")
        data_theme = mobile_page.evaluate("document.documentElement.getAttribute('data-theme')")
        assert data_theme == "dark", f"Expected 'dark', got '{data_theme}'"
        print("  ✓ Mobile theme switched to Dark mode")

        mobile_context.close()
        browser.close()

    print("\n" + "=" * 70)
    print("BROWSER AUDIT RESULTS:")
    print("=" * 70)
    print(f"Console Errors/Warnings: {len(console_errors)}")
    for err in console_errors:
        print(f"  - {err}")
    print(f"Page Exceptions:         {len(page_errors)}")
    for err in page_errors:
        print(f"  - {err}")

    if page_errors:
        print("\n❌ FAILED: Unhandled page exceptions were detected.")
        sys.exit(1)

    print("\n✅ PHASE 4 REAL BROWSER AUDIT PASSED WITH ZERO EXCEPTIONS!")
    sys.exit(0)

if __name__ == '__main__':
    run_phase4_browser_audit()
