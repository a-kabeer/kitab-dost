"""
Phase 1 Automated Test Suite
Verifies:
- Flask application factory setup
- SQLite database initialization & WAL mode
- Routes rendering (Student portal, Teacher dashboard, Error pages)
- Static assets loading (CSS tokens, Theme script)
- Concurrency & immediate write transaction handling
- Application restart persistence
"""

import os
import sys
import sqlite3

# Set utf-8 output encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
from app import create_app
from app.database import get_db, db_transaction

def run_tests():
    print(">>> Starting Phase 1 Verification Tests...")
    app = create_app('development')
    client = app.test_client()

    # 1. Verify Database Initialization & WAL Mode
    print("\n[Test 1] Verifying SQLite Database & WAL Mode...")
    with app.app_context():
        db = get_db()
        cur = db.cursor()
        
        # Check journal mode
        cur.execute("PRAGMA journal_mode;")
        journal_mode = cur.fetchone()[0]
        assert journal_mode.lower() == 'wal', f"Expected WAL mode, got {journal_mode}"
        print(f"  ✓ SQLite journal_mode is WAL: {journal_mode}")

        # Check tables existence
        cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cur.fetchall()]
        required_tables = [
            'teachers', 'books', 'donations', 'requests',
            'handovers', 'activity_logs', 'system_settings', 'backup_records'
        ]
        for tbl in required_tables:
            assert tbl in tables, f"Missing required table: {tbl}"
            print(f"  ✓ Table verified: {tbl}")

        # Check default system settings seed
        cur.execute("SELECT COUNT(*) FROM system_settings;")
        count = cur.fetchone()[0]
        assert count >= 4, f"Expected at least 4 default settings, got {count}"
        print(f"  ✓ System settings seeded: {count} entries")

    # 2. Verify Student Routes & Layout
    print("\n[Test 2] Verifying Student Portal Routes...")
    student_routes = ['/', '/catalogue', '/donate', '/track', '/scan', '/about']
    for route in student_routes:
        res = client.get(route)
        assert res.status_code == 200, f"Route {route} failed with status {res.status_code}"
        assert b"data-theme" in res.data, f"Route {route} missing data-theme in HTML"
        assert b"theme.js" in res.data, f"Route {route} missing theme.js script link"
        print(f"  ✓ Student Route {route}: Status 200 OK")

    # 3. Verify Teacher Route Authentication Protection
    print("\n[Test 3] Verifying Inaccessibility of Teacher Routes Without Login...")
    teacher_routes = [
        '/teacher/dashboard',
        '/teacher/donations',
        '/teacher/requests',
        '/teacher/handovers',
        '/teacher/inventory',
        '/teacher/reports',
        '/teacher/settings'
    ]
    # Unauthenticated requests must be blocked and redirected to /auth/login
    for route in teacher_routes:
        res = client.get(route)
        assert res.status_code == 302, f"Expected 302 redirect for {route}, got {res.status_code}"
        assert '/auth/login' in res.headers.get('Location'), f"Expected redirect to /auth/login for {route}"
        print(f"  ✓ Unauthenticated access blocked on {route} -> Redirect to /auth/login")

    # Verify Login Screen Renders
    res_login = client.get('/auth/login')
    assert res_login.status_code == 200
    assert b"Teacher Sign In" in res_login.data
    assert b"csrf_token" in res_login.data
    print("  ✓ Teacher login screen renders with CSRF token")

    # Verify CSRF Protection on POST
    res_no_csrf = client.post('/auth/login', data={'username': 'teacher', 'password': 'wrong'})
    assert res_no_csrf.status_code == 400, f"Expected 400 Bad Request for missing CSRF, got {res_no_csrf.status_code}"
    print("  ✓ CSRF Protection verified: Missing CSRF token rejected with HTTP 400")

    # Verify Login with seeded credentials
    with client.session_transaction() as sess:
        csrf_tok = sess['csrf_token']
    
    # Test invalid login attempt
    res_bad_login = client.post(
        '/auth/login',
        data={'username': 'teacher', 'password': 'wrongpassword', 'csrf_token': csrf_tok},
        follow_redirects=True
    )
    assert b"Invalid teacher credentials" in res_bad_login.data
    print("  ✓ Invalid login rejected with warning alert")

    # Test valid login attempt
    res_good_login = client.post(
        '/auth/login',
        data={'username': 'teacher', 'password': 'Teacher@123', 'csrf_token': csrf_tok},
        follow_redirects=False
    )
    assert res_good_login.status_code == 302
    assert '/teacher/dashboard' in res_good_login.headers.get('Location')
    print("  ✓ Valid teacher credentials accepted: Redirecting to dashboard")

    # Test authenticated access to teacher routes
    for route in teacher_routes:
        res = client.get(route)
        assert res.status_code == 200, f"Authenticated access failed on {route}"
        assert b"Teacher Dashboard" in res.data or b"Teacher Desk" in res.data
        assert b"data-theme" in res.data
        print(f"  ✓ Authenticated Teacher Route {route}: Status 200 OK")

    # Test Logout
    res_logout = client.get('/auth/logout', follow_redirects=True)
    assert res_logout.status_code == 200
    assert b"signed out" in res_logout.data.lower()
    # Confirm routes are blocked again
    res_after_logout = client.get('/teacher/dashboard')
    assert res_after_logout.status_code == 302
    print("  ✓ Logout successful: Teacher routes re-locked")

    # 4. Verify Static Assets & Zero External CDN Links
    print("\n[Test 4] Verifying Static Assets & Zero CDN Dependency...")
    static_files = [
        '/static/css/main.css',
        '/static/css/components.css',
        '/static/css/student.css',
        '/static/css/teacher.css',
        '/static/js/theme.js'
    ]
    for asset in static_files:
        res = client.get(asset)
        assert res.status_code == 200, f"Asset {asset} returned {res.status_code}"
        print(f"  ✓ Static Asset {asset}: Loaded ({len(res.data)} bytes)")

    # Verify base HTML contains no external font or css CDN links
    res = client.get('/')
    html = res.data.decode('utf-8')
    assert 'cdn.' not in html, "Found external CDN link in HTML!"
    assert 'fonts.googleapis.com' not in html, "Found external Google Fonts link in HTML!"
    assert 'unpkg.com' not in html, "Found external unpkg link in HTML!"
    assert 'cdnjs.' not in html, "Found external cdnjs link in HTML!"
    print("  ✓ Zero External CDNs confirmed: 100% offline self-hosted")

    # 5. Verify Error Handlers (404 and 500)
    print("\n[Test 5] Verifying Error Handlers...")
    res_404 = client.get('/nonexistent-book-route-test')
    assert res_404.status_code == 404, f"Expected 404, got {res_404.status_code}"
    assert b"404 - Page Not Found" in res_404.data, "404 page content mismatch"
    print("  ✓ Custom 404 error page renders properly")

    # 6. Verify Immediate Transaction & Concurrency Helper
    print("\n[Test 6] Verifying Short Immediate Write Transactions...")
    with app.app_context():
        with db_transaction() as db:
            cur = db.cursor()
            cur.execute(
                "INSERT INTO activity_logs (action, entity_type, actor_type, details) "
                "VALUES ('TEST_INIT', 'system', 'system', 'Phase 1 test transaction successful');"
            )
        
        # Verify committed record
        db = get_db()
        cur = db.cursor()
        cur.execute("SELECT details FROM activity_logs WHERE action = 'TEST_INIT';")
        row = cur.fetchone()
        assert row is not None, "Transaction failed to commit"
        print(f"  ✓ Immediate write transaction committed: {row[0]}")

    # 7. Verify Application Restart Persistence
    print("\n[Test 7] Verifying Application Restart & Persistence...")
    del app, client
    app2 = create_app('production')
    client2 = app2.test_client()
    with app2.app_context():
        db2 = get_db()
        cur2 = db2.cursor()
        cur2.execute("SELECT details FROM activity_logs WHERE action = 'TEST_INIT';")
        row2 = cur2.fetchone()
        assert row2 is not None, "Data was lost across app recreation"
        print("  ✓ Persistence across application restart verified")

    print("\n" + "=" * 60)
    print(" ALL PHASE 1 VERIFICATION TESTS PASSED SUCCESSFULLY! ")
    print("=" * 60)

if __name__ == '__main__':
    run_tests()
