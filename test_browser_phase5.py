"""
Playwright Browser Test Suite for Phase 5: Physical Handover Ledger & Circulation Defense
Using Microsoft Edge (Chromium) in headless mode.
Tests the complete physical handover flow: Request -> Approval -> Physical Verification -> Handover Confirmation -> Ledger Audit -> Printable Receipt -> Public Tracking & Reservation Cancellation.
"""

import sys
import time
from playwright.sync_api import sync_playwright

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

EDGE_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
BASE_URL = "http://127.0.0.1:5000"

def run_phase5_browser_audit():
    print("=" * 75)
    print("STARTING PHASE 5 REAL BROWSER AUDIT VIA MICROSOFT EDGE")
    print("=" * 75)

    console_errors = []
    page_errors = []

    with sync_playwright() as p:
        browser = p.chromium.launch(
            executable_path=EDGE_PATH,
            headless=True
        )

        # -------------------------------------------------------------
        # SUITE 1: Desktop Viewport (1280x800) - Full Physical Handover Flow
        # -------------------------------------------------------------
        print("\n[Suite 1] Desktop Viewport Handover Lifecycle Audit (1280x800)...")
        context = browser.new_context(viewport={"width": 1280, "height": 800})
        page = context.new_page()

        page.on("console", lambda msg: console_errors.append(f"[{msg.type}] {msg.text}") if msg.type in ("error", "warning") else None)
        page.on("pageerror", lambda exc: page_errors.append(str(exc)))
        page.on("dialog", lambda dialog: dialog.accept())

        # 1.1 Find an Available Book in Catalogue
        print("  1.1 Browsing available books in student catalogue...")
        res = page.goto(f"{BASE_URL}/catalogue?status=available")
        assert res.status == 200, f"Expected 200, got {res.status}"

        first_book_link = page.locator(".book-card a[href^='/book/']").first
        book_href = first_book_link.get_attribute("href")
        book_code = book_href.split("/")[-1]
        print(f"  Selected available book: {book_code}")

        # 1.2 Submit Student Request
        ts = int(time.time())
        student_name = f"Farhan Ahmed {ts % 1000}"
        student_roll = str((ts % 900) + 10)
        print(f"  1.2 Submitting student request for {book_code} by {student_name}...")
        page.goto(f"{BASE_URL}/request/{book_code}")
        page.wait_for_load_state("networkidle")
        page.fill("input[name='requester_name']", student_name)
        page.fill("input[name='requester_class']", "Class 8-C")
        page.fill("input[name='requester_roll_no']", student_roll)
        page.fill("input[name='requester_contact']", "0311-9876543")
        page.fill("textarea[name='notes']", "Needs book for annual examinations.")
        page.click("button[type='submit']")
        page.wait_for_load_state("networkidle")

        if "/request/success" not in page.url:
            print("  [ERROR] Page content on request failure:\n", page.content()[:1000])
        assert "/request/success" in page.url
        tracking_code = page.locator("#track-code").inner_text().strip()
        print(f"  ✓ Request submitted successfully. Tracking Code: {tracking_code}")

        # 1.3 Teacher Login
        print("  1.3 Authenticating as Teacher...")
        page.goto(f"{BASE_URL}/auth/login")
        page.fill("input[name='username']", "teacher")
        page.fill("input[name='password']", "Teacher@123")
        page.click("button[type='submit']")
        page.wait_for_load_state("networkidle")
        assert "/teacher/dashboard" in page.url
        print("  ✓ Teacher logged in to Dashboard")

        # 1.4 Approve Request to Reserve Book
        print(f"  1.4 Locating request {tracking_code} in requests queue...")
        page.goto(f"{BASE_URL}/teacher/requests?q={tracking_code}")
        page.wait_for_load_state("networkidle")
        assert tracking_code in page.content()

        print("  Approving request to reserve book...")
        page.click("form[action*='/approve'] button[type='submit']")
        page.wait_for_load_state("networkidle")
        assert "Request approved" in page.content()
        print("  ✓ Request approved, book successfully reserved for student")

        # 1.5 Open Handover Confirmation Form
        print(f"  1.5 Opening Handover Confirmation Screen for {tracking_code}...")
        page.goto(f"{BASE_URL}/teacher/requests?status=approved&q={tracking_code}")
        page.wait_for_load_state("networkidle")

        # Click the "Handover" action button in the requests table
        handover_btn = page.locator("table a:has-text('Handover')").first
        handover_btn.click()
        page.wait_for_load_state("networkidle")
        assert "/handover" in page.url
        assert "Confirm Physical" in page.content()
        print("  ✓ Handover confirmation screen loaded with verification checklist")

        # 1.6 Verify Identity & Verification Checklist in Form
        print("  1.6 Verifying student verification checklist and safety controls...")
        assert student_name in page.content()
        assert "Class 8-C" in page.content()
        assert student_roll in page.content()
        assert "confirm_id" in page.content()
        assert "confirm_physical" in page.content()
        print("  ✓ Student school credentials and mandatory verification checkboxes confirmed")

        # 1.7 Confirm Physical Handover
        print("  1.7 Completing Physical Handover...")
        page.check("input[name='confirm_id']")
        page.check("input[name='confirm_physical']")
        page.fill("textarea[name='remarks']", "Verified student ID card. Book handed over in good condition.")
        page.click("#submit-handover-btn")
        page.wait_for_load_state("networkidle")

        # 1.8 Verify Handover Detail View
        assert "/teacher/handovers/" in page.url
        assert "Handover Record" in page.content() or "Physical Handover Completed" in page.content()
        handover_content = page.content()
        assert student_name in handover_content
        assert tracking_code in handover_content
        assert "KB-HO-" in handover_content
        print("  ✓ Handover transaction committed! Permanent ledger detail page rendered.")

        # Extract Handover Code and ID
        handover_code = page.locator("code:has-text('KB-HO-')").first.inner_text().strip()
        handover_id = page.url.rstrip('/').split('/')[-1]
        print(f"  ✓ Handover Reference Code: {handover_code} (ID: {handover_id})")

        # 1.9 Verify Printable Receipt View
        print("  1.9 Navigating to Printable A4 Receipt...")
        page.goto(f"{BASE_URL}/teacher/handovers/{handover_id}/receipt")
        page.wait_for_load_state("networkidle")
        assert "/receipt" in page.url
        receipt_html = page.content()
        assert "Kitaab Bank – Book Distribution Receipt" in receipt_html
        assert handover_code in receipt_html
        assert tracking_code in receipt_html
        assert student_name in receipt_html
        assert "Authorized Teacher" in receipt_html
        assert "Student / Parent Recipient Signature" in receipt_html
        print("  ✓ Official printable receipt verified with dual signature lines and styling")

        # 1.10 Verify Handover Ledger Queue (/teacher/handovers)
        print("  1.10 Inspecting Handover Ledger (/teacher/handovers)...")
        page.goto(f"{BASE_URL}/teacher/handovers")
        page.wait_for_load_state("networkidle")
        ledger_html = page.content()
        assert handover_code in ledger_html
        assert student_name in ledger_html
        assert "Handover Ledger" in ledger_html
        print("  ✓ Handover Ledger displays completed transaction record")

        # Search filter in Ledger
        print(f"  Testing ledger search filter for '{handover_code}'...")
        page.fill("input[name='q']", handover_code)
        page.click("button:has-text('Filter')")
        page.wait_for_load_state("networkidle")
        assert handover_code in page.content()
        print("  ✓ Ledger search filter verified")

        # 1.11 Verify Student Public Tracking Page (/track)
        print(f"  1.11 Checking Public Tracking Desk for {tracking_code}...")
        page.goto(f"{BASE_URL}/track?code={tracking_code}")
        page.wait_for_load_state("networkidle")
        track_html = page.content()
        assert tracking_code in track_html
        assert "Handed Over" in track_html or "Completed" in track_html
        assert handover_code in track_html
        # Privacy verification
        assert "Farhan" in track_html and "***" in track_html, "Student name must be masked"
        assert "0311-9876543" not in track_html, "Phone number must NOT leak in public tracking"
        assert f'value="{student_roll}"' not in track_html and f">{student_roll}<" not in track_html, "Roll number must NOT leak in public tracking"
        print("  ✓ Student tracking page verified: Completed status, handover reference, ZERO PII leakage!")

        # 1.12 Reservation Cancellation & Circulation Release Workflow
        print("\n  1.12 Testing Reservation Cancellation Workflow (Release uncollected book)...")
        # Submit another request
        page.goto(f"{BASE_URL}/catalogue?status=available")
        page.wait_for_load_state("networkidle")
        second_book_link = page.locator(".book-card a[href^='/book/']").first
        cancel_book_code = second_book_link.get_attribute("href").split("/")[-1]

        cancel_student = f"Zainab Bibi {ts % 1000}"
        cancel_roll = str((ts % 900) + 50)
        page.goto(f"{BASE_URL}/request/{cancel_book_code}")
        page.wait_for_load_state("networkidle")
        page.fill("input[name='requester_name']", cancel_student)
        page.fill("input[name='requester_class']", "Class 6-A")
        page.fill("input[name='requester_roll_no']", cancel_roll)
        page.fill("input[name='requester_contact']", "0322-1112233")
        page.click("button[type='submit']")
        page.wait_for_load_state("networkidle")
        cancel_track_code = page.locator("#track-code").inner_text().strip()

        # Teacher approves request
        page.goto(f"{BASE_URL}/teacher/requests?q={cancel_track_code}")
        page.wait_for_load_state("networkidle")
        page.click("form[action*='/approve'] button[type='submit']")
        page.wait_for_load_state("networkidle")

        # Now Teacher cancels/releases reservation
        print("  Cancelling reservation from requests list...")
        page.goto(f"{BASE_URL}/teacher/requests?status=approved&q={cancel_track_code}")
        page.wait_for_load_state("networkidle")
        page.click("button:has-text('Release')")
        page.wait_for_timeout(300)
        page.fill("#cancel-reason-input", "Student requested cancellation due to family relocation.")
        page.click("button:has-text('Confirm Release to Catalogue')")
        page.wait_for_load_state("networkidle")
        assert "Reservation released" in page.content() or "cancelled" in page.content().lower()
        print("  ✓ Reservation cancelled successfully")

        # Verify book returned to Available in Catalogue
        page.goto(f"{BASE_URL}/book/{cancel_book_code}")
        page.wait_for_load_state("networkidle")
        assert "Available" in page.content()
        assert "Request This Book" in page.content()
        print(f"  ✓ Book {cancel_book_code} returned to Available in catalogue!")

        # Verify tracking page reflects cancellation
        page.goto(f"{BASE_URL}/track?code={cancel_track_code}")
        page.wait_for_load_state("networkidle")
        assert "Reservation Released" in page.content() or "Cancelled" in page.content()
        print("  ✓ Tracking desk accurately displays reservation release explanation")

        context.close()

        # -------------------------------------------------------------
        # SUITE 2: Mobile Viewport (390x844) - Smartphone Screen
        # -------------------------------------------------------------
        print("\n[Suite 2] Mobile Viewport Audit (390x844 - Smartphone Screen)...")
        mobile_context = browser.new_context(
            viewport={"width": 390, "height": 844},
            user_agent="Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
        )
        mobile_page = mobile_context.new_page()

        mobile_page.on("console", lambda msg: console_errors.append(f"[Mobile {msg.type}] {msg.text}") if msg.type in ("error", "warning") else None)
        mobile_page.on("pageerror", lambda exc: page_errors.append(f"[Mobile PageError] {exc}"))

        # 2.1 Mobile Tracking Desk
        print(f"  2.1 Mobile Tracking Desk for {tracking_code}...")
        mobile_page.goto(f"{BASE_URL}/track?code={tracking_code}")
        mobile_page.wait_for_load_state("networkidle")
        assert tracking_code in mobile_page.content()
        assert handover_code in mobile_page.content()
        print("  ✓ Mobile tracking desk loaded responsive handover status")

        # 2.2 Mobile Theme Switching
        print("  2.2 Testing Theme Switching on Mobile...")
        mobile_page.evaluate("window.KitaabTheme.setTheme('dark')")
        theme = mobile_page.evaluate("document.documentElement.getAttribute('data-theme')")
        assert theme == "dark", f"Expected 'dark', got '{theme}'"
        print("  ✓ Mobile dark theme switch verified")

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
        print("\n❌ FAILED: Unhandled page exceptions were detected.")
        sys.exit(1)

    print("\n✅ PHASE 5 REAL BROWSER AUDIT PASSED WITH ZERO EXCEPTIONS!")
    sys.exit(0)

if __name__ == '__main__':
    run_phase5_browser_audit()
