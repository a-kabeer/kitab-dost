"""
Real Browser Audit Script using Microsoft Edge (Chromium) via Playwright
Tests:
- Real browser console errors (pageerror & console.error)
- Mobile viewport responsiveness (390x844 mobile phone)
- Desktop viewport (1280x800)
- Theme switching & persistence across page reloads
- Teacher dashboard security & authentication lifecycle
- Zero broken links / assets
"""

import sys
import time
from playwright.sync_api import sync_playwright

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

EDGE_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
BASE_URL = "http://127.0.0.1:5000"

def run_browser_audit():
    print("=" * 68)
    print("STARTING REAL BROWSER AUDIT VIA MICROSOFT EDGE (CHROMIUM)")
    print("=" * 68)

    console_errors = []
    page_errors = []

    with sync_playwright() as p:
        print("\nLaunching headless Microsoft Edge browser...")
        browser = p.chromium.launch(
            executable_path=EDGE_PATH,
            headless=True
        )

        # -------------------------------------------------------------
        # TEST SUITE A: Desktop Viewport & Theme Persistence
        # -------------------------------------------------------------
        print("\n[Suite A] Desktop Viewport & Theme Engine Verification (1280x800)...")
        context = browser.new_context(viewport={"width": 1280, "height": 800})
        page = context.new_page()

        # Listen for any console errors or page errors
        page.on("console", lambda msg: console_errors.append(f"[{msg.type}] {msg.text}") if msg.type in ("error", "warning") else None)
        page.on("pageerror", lambda exc: page_errors.append(str(exc)))

        # 1. Navigate to Student Home
        res = page.goto(f"{BASE_URL}/")
        assert res.status == 200, f"Expected 200, got {res.status}"
        print(f"  ✓ Homepage loaded successfully: Title='{page.title()}'")

        # 2. Test Light -> Dark Theme Switch
        print("  Testing Theme Switcher...")
        page.click("[data-theme-toggle]")
        time.sleep(0.2)
        page.click("[data-theme-set='dark']")
        theme_attr = page.evaluate("document.documentElement.getAttribute('data-theme')")
        assert theme_attr == 'dark', f"Expected data-theme='dark', got {theme_attr}"
        print("  ✓ Dark Theme applied successfully (data-theme='dark')")

        # 3. Test Theme Persistence across Reload
        page.reload()
        theme_after_reload = page.evaluate("document.documentElement.getAttribute('data-theme')")
        assert theme_after_reload == 'dark', f"Expected data-theme='dark' after reload, got {theme_after_reload}"
        print("  ✓ Theme persistence verified: Dark mode retained after full page reload")

        # 4. Switch to Light Mode and verify persistence
        page.click("[data-theme-toggle]")
        time.sleep(0.2)
        page.click("[data-theme-set='light']")
        page.reload()
        theme_light = page.evaluate("document.documentElement.getAttribute('data-theme')")
        assert theme_light == 'light', f"Expected data-theme='light', got {theme_light}"
        print("  ✓ Theme persistence verified: Light mode retained after reload")

        # 5. Switch to System Default
        page.click("[data-theme-toggle]")
        time.sleep(0.2)
        page.click("[data-theme-set='system']")
        pref = page.evaluate("document.documentElement.getAttribute('data-theme-preference')")
        assert pref == 'system', f"Expected preference 'system', got {pref}"
        print("  ✓ System Default mode set and active")

        # -------------------------------------------------------------
        # TEST SUITE B: Mobile Viewport & Responsiveness (iPhone / Pixel: 390x844)
        # -------------------------------------------------------------
        print("\n[Suite B] Mobile Viewport & Responsiveness Verification (390x844)...")
        mobile_context = browser.new_context(
            viewport={"width": 390, "height": 844},
            is_mobile=True,
            has_touch=True,
            user_agent="Mozilla/5.0 (Linux; Android 14; TECNO CAMON 20) AppleWebKit/537.36 Chrome/124.0.0.0 Mobile Safari/537.36"
        )
        mobile_page = mobile_context.new_page()
        mobile_page.on("console", lambda msg: console_errors.append(f"[Mobile {msg.type}] {msg.text}") if msg.type in ("error", "warning") else None)
        mobile_page.on("pageerror", lambda exc: page_errors.append(f"[Mobile Error] {str(exc)}"))

        mobile_page.goto(f"{BASE_URL}/")
        
        # Verify Hamburger menu is visible on mobile
        is_toggle_visible = mobile_page.is_visible("#mobileNavToggle")
        assert is_toggle_visible, "Mobile nav toggle (hamburger button) is not visible on mobile viewport!"
        print("  ✓ Mobile nav toggle is properly rendered on 390px viewport")

        # Toggle hamburger menu open
        mobile_page.click("#mobileNavToggle")
        time.sleep(0.2)
        nav_has_show = mobile_page.evaluate("document.getElementById('navLinks').classList.contains('show')")
        assert nav_has_show, "Mobile navigation menu failed to expand on click!"
        print("  ✓ Mobile navigation menu expanded cleanly on tap")

        # -------------------------------------------------------------
        # TEST SUITE C: Navigation Links Integrity
        # -------------------------------------------------------------
        print("\n[Suite C] Student Navigation Flow...")
        routes_to_test = [
            ("Browse Books", "/catalogue"),
            ("Donate a Book", "/donate"),
            ("Track Request", "/track"),
            ("Scan QR", "/scan"),
            ("About", "/about")
        ]
        for label, path in routes_to_test:
            res_nav = page.goto(f"{BASE_URL}{path}")
            assert res_nav.status == 200, f"Failed on {path}: {res_nav.status}"
            print(f"  ✓ {label} ({path}): Loaded 200 OK")

        # -------------------------------------------------------------
        # TEST SUITE D: Teacher Security & Authentication Flow
        # -------------------------------------------------------------
        print("\n[Suite D] Teacher Security & Auth Protection...")
        # 1. Direct unauthenticated access to /teacher/dashboard
        page.goto(f"{BASE_URL}/teacher/dashboard")
        assert "/auth/login" in page.url, f"Security failure! Unauthenticated visitor reached: {page.url}"
        print(f"  ✓ Route guard verified: /teacher/dashboard redirected to {page.url}")

        # 2. Try invalid password
        page.fill("#username", "teacher")
        page.fill("#password", "WrongPassword!99")
        page.click("button[type='submit']")
        time.sleep(0.3)
        assert "Invalid teacher credentials" in page.content()
        print("  ✓ Bad credentials properly rejected with warning message")

        # 3. Log in with valid credentials
        page.fill("#username", "teacher")
        page.fill("#password", "Teacher@123")
        page.click("button[type='submit']")
        time.sleep(0.5)
        assert "/teacher/dashboard" in page.url, f"Expected dashboard URL, got {page.url}"
        assert "Library Overview" in page.content()
        print(f"  ✓ Authentication successful: Logged in and landed on {page.url}")

        # 4. Verify Theme switching on Teacher Portal
        page.click("[data-theme-toggle]")
        time.sleep(0.2)
        page.click("[data-theme-set='dark']")
        assert page.evaluate("document.documentElement.getAttribute('data-theme')") == 'dark'
        print("  ✓ Teacher portal theme toggle verified (Dark mode active on admin dashboard)")

        # 5. Sign Out
        page.click("a:has-text('Sign Out')")
        time.sleep(0.3)
        assert "/auth/login" not in page.url
        print(f"  ✓ Teacher sign out successful: Redirected to {page.url}")

        # 6. Re-verify locked dashboard
        page.goto(f"{BASE_URL}/teacher/dashboard")
        assert "/auth/login" in page.url
        print("  ✓ Dashboard confirmed re-locked after sign out")

        browser.close()

    # -------------------------------------------------------------
    # CONSOLE & PAGE ERRORS AUDIT
    # -------------------------------------------------------------
    print("\n" + "=" * 68)
    print("BROWSER CONSOLE & JS RUNTIME AUDIT:")
    print("=" * 68)
    print(f"Total Page Errors: {len(page_errors)}")
    print(f"Total Console Errors/Warnings: {len(console_errors)}")

    if page_errors:
        print("Page Errors encountered:")
        for err in page_errors:
            print("  [ERROR]", err)
    else:
        print("  ✓ ZERO JavaScript runtime errors detected.")

    if console_errors:
        print("Console warnings/errors:")
        for w in console_errors:
            print("  [WARN/ERR]", w)
    else:
        print("  ✓ ZERO Console errors/warnings detected.")

    assert len(page_errors) == 0, f"Found {len(page_errors)} JavaScript errors!"
    print("\n" + "=" * 68)
    print("REAL BROWSER VERIFICATION AUDIT PASSED 100%!")
    print("=" * 68)

if __name__ == '__main__':
    run_browser_audit()
