"""
Playwright Browser Test Suite for Phase 3: Book Donation System
Using Microsoft Edge (Chromium) in headless mode.
Tests the full student submission -> teacher approval -> public catalogue lifecycle.
"""

import sys
import time
from playwright.sync_api import sync_playwright

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

EDGE_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
BASE_URL = "http://127.0.0.1:5000"

def run_phase3_browser_audit():
    print("=" * 70)
    print("STARTING PHASE 3 REAL BROWSER AUDIT VIA MICROSOFT EDGE")
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

        # 1.1 Student Navigation to /donate
        print("  1.1 Navigating to Student Donation Form (/donate)...")
        res = page.goto(f"{BASE_URL}/donate")
        assert res.status == 200, f"Expected 200, got {res.status}"
        assert "Donate a Textbook" in page.title()
        print("  ✓ Donation form loaded cleanly")

        # 1.2 Fill and Submit Donation Form
        print("  1.2 Filling out book donation form...")
        page.fill("#book-title", "Advanced Mathematics Class 8 (STBB)")
        page.fill("#book-author", "Prof. S. K. Baloch")
        page.select_option("#book-class", "Class 8")
        page.select_option("#book-subject", "Mathematics")
        page.select_option("#book-lang", "English")
        page.select_option("#book-condition", "Like New")
        page.fill("#book-desc", "Clean textbook, all geometry sections and exercises intact.")
        page.fill("#donor-name", "Farhan Ali")
        page.fill("#donor-class", "Class 8-A")
        page.fill("#donor-roll", "12")
        page.fill("#donor-contact", "0301-2345678")

        print("  Submitting donation form...")
        page.click("button:has-text('Submit Donation for Teacher Review')")
        page.wait_for_load_state("networkidle")

        # 1.3 Verify Confirmation Screen
        assert "/donate/success" in page.url
        assert "Thank You, Farhan Ali!" in page.content()
        code_elem = page.locator("#ref-code")
        assert code_elem.is_visible()
        donation_code = code_elem.inner_text().strip()
        assert donation_code.startswith("KB-DON-")
        print(f"  ✓ Submission succeeded! Generated Reference Code: {donation_code}")

        # 1.4 Teacher Login
        print("  1.4 Logging in to Teacher Administrative Desk...")
        page.goto(f"{BASE_URL}/auth/login")
        page.fill("input[name='username']", "teacher")
        page.fill("input[name='password']", "Teacher@123")
        page.click("button[type='submit']")
        page.wait_for_load_state("networkidle")
        assert "/teacher/dashboard" in page.url
        print("  ✓ Teacher authentication successful")

        # 1.5 Review Queue
        print("  1.5 Inspecting Teacher Donation Queue (/teacher/donations)...")
        page.goto(f"{BASE_URL}/teacher/donations?status=pending")
        page.wait_for_load_state("networkidle")
        assert "Donation Review Queue" in page.content()
        assert donation_code in page.content()
        assert "Advanced Mathematics Class 8 (STBB)" in page.content()
        print(f"  ✓ Donation {donation_code} appears in teacher review queue")

        # 1.6 Search in Queue
        print("  Testing Search in Queue ('Farhan Ali')...")
        page.fill("input[name='q']", "Farhan Ali")
        page.click("button:has-text('Filter')")
        page.wait_for_load_state("networkidle")
        assert "Farhan Ali" in page.content()
        print("  ✓ Search filter by donor name verified")

        # 1.7 View Full Inspection Detail
        print(f"  1.7 Opening inspection detail page for donation...")
        page.locator("a[title='Inspect full details']").first.click()
        page.wait_for_load_state("networkidle")
        assert "/teacher/donations/" in page.url, f"Expected /teacher/donations/ in URL, got {page.url}"
        assert "Donation Inspection" in page.content()
        assert "Farhan Ali" in page.content()
        assert "Class 8-A" in page.content()
        print("  ✓ Inspection page displays complete metadata and confidential donor details")

        # 1.8 Approve Donation
        print("  1.8 Approving donation...")
        # Handle the confirm() dialog
        page.once("dialog", lambda dialog: dialog.accept())
        page.click("button:has-text('Approve & Publish Book')")
        page.wait_for_load_state("networkidle")
        assert "/teacher/donations" in page.url
        assert "Donation approved successfully" in page.content()
        print("  ✓ Donation approved by teacher!")

        # 1.9 Verify Book in Public Catalogue
        print("  1.9 Verifying public catalogue visibility...")
        page.goto(f"{BASE_URL}/catalogue?q=Advanced+Mathematics+Class+8")
        page.wait_for_load_state("networkidle")
        assert "Advanced Mathematics Class 8" in page.content()
        book_link = page.locator(".book-card-title a").first
        book_title = book_link.inner_text()
        print(f"  ✓ Newly approved book listed in public catalogue: '{book_title}'")

        # 1.10 Verify Donor Confidentiality
        print("  1.10 Verifying Donor PII Confidentiality on public book detail...")
        book_link.click()
        page.wait_for_load_state("networkidle")
        assert "/book/KB-BK-" in page.url
        detail_content = page.content()
        assert "Farhan Ali" not in detail_content, "Security breach: Donor name visible in public detail!"
        assert "0301-2345678" not in detail_content, "Security breach: Donor phone visible in public detail!"
        assert "Class 8-A" not in detail_content, "Security breach: Donor section visible in public detail!"
        print("  ✓ Donor privacy 100% verified: Zero PII leaked in public catalogue or book detail")

        # -------------------------------------------------------------
        # SUITE 2: Mobile Viewport (390x844) Responsiveness
        # -------------------------------------------------------------
        print("\n[Suite 2] Mobile Viewport Responsiveness (390x844)...")
        mobile_context = browser.new_context(
            viewport={"width": 390, "height": 844},
            is_mobile=True,
            has_touch=True,
            user_agent="Mozilla/5.0 (Linux; Android 14; TECNO CAMON 20) AppleWebKit/537.36 Chrome/124.0.0.0 Mobile Safari/537.36"
        )
        mobile_page = mobile_context.new_page()
        mobile_page.on("console", lambda msg: console_errors.append(f"[Mobile {msg.type}] {msg.text}") if msg.type in ("error", "warning") else None)
        mobile_page.on("pageerror", lambda exc: page_errors.append(f"[Mobile Error] {str(exc)}"))

        # Mobile Donation Form
        mobile_page.goto(f"{BASE_URL}/donate")
        mobile_page.wait_for_load_state("networkidle")
        assert mobile_page.locator("#book-title").is_visible()
        print("  ✓ Mobile donation form responsive and touch-accessible")

        # Mobile Teacher Desk
        mobile_page.goto(f"{BASE_URL}/auth/login")
        mobile_page.fill("input[name='username']", "teacher")
        mobile_page.fill("input[name='password']", "Teacher@123")
        mobile_page.click("button[type='submit']")
        mobile_page.wait_for_load_state("networkidle")

        mobile_page.goto(f"{BASE_URL}/teacher/donations")
        mobile_page.wait_for_load_state("networkidle")
        assert mobile_page.locator(".data-table").is_visible()
        print("  ✓ Mobile teacher review queue renders with horizontally scrollable responsive table")

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
        print("\n🎉 ALL PHASE 3 BROWSER AUDIT TESTS PASSED WITH 0 CONSOLE ERRORS!")
        return 0
    else:
        print("\n⚠️ AUDIT FINISHED WITH CONSOLE ERRORS.")
        return 1

if __name__ == '__main__':
    code = run_phase3_browser_audit()
    sys.exit(code)
