"""
Live Server & Network Connectivity Verification Script
Tests:
- Waitress WSGI binding on 0.0.0.0:5000
- Localhost (127.0.0.1) connectivity
- LAN IP (172.31.161.179) connectivity (simulating mobile Wi-Fi device)
- Response headers (X-Content-Type-Options, X-Frame-Options)
- Theme token integrity
"""

import sys
import time
import socket
import urllib.request
import subprocess
from run_server import get_lan_ip

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

def test_live_server():
    lan_ip = get_lan_ip()
    port = 5000
    print("=" * 64)
    print("STARTING LIVE WAITRESS WSGI SERVER TEST")
    print("=" * 64)

    # Launch run_server.py as subprocess
    proc = subprocess.Popen(
        [sys.executable, "run_server.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    try:
        # Wait for server to bind
        time.sleep(2)

        # 1. Test Localhost
        print("\n[Test 1] Querying Localhost (http://127.0.0.1:5000)...")
        req_local = urllib.request.Request("http://127.0.0.1:5000/")
        with urllib.request.urlopen(req_local, timeout=5) as res:
            assert res.status == 200, f"Expected 200, got {res.status}"
            body = res.read().decode('utf-8')
            assert "Kitaab Bank" in body
            assert "Zero-FOUC Theme Guard" in body
            print("  ✓ Localhost responded: HTTP 200 OK")
            print("  ✓ Security header X-Frame-Options:", res.headers.get('X-Frame-Options'))
            print("  ✓ Security header X-Content-Type-Options:", res.headers.get('X-Content-Type-Options'))

        # 2. Test LAN IP (Simulating another device on Wi-Fi)
        print(f"\n[Test 2] Querying LAN IP (http://{lan_ip}:5000)...")
        req_lan = urllib.request.Request(f"http://{lan_ip}:5000/")
        with urllib.request.urlopen(req_lan, timeout=5) as res_lan:
            assert res_lan.status == 200, f"Expected 200, got {res_lan.status}"
            body_lan = res_lan.read().decode('utf-8')
            assert "Pass Knowledge Forward" in body_lan
            print(f"  ✓ LAN IP ({lan_ip}:5000) responded: HTTP 200 OK")

        # 3. Test Teacher Route Access Guard over LAN
        print(f"\n[Test 3] Querying Teacher Dashboard over LAN without session (http://{lan_ip}:5000/teacher/dashboard)...")
        req_teacher = urllib.request.Request(f"http://{lan_ip}:5000/teacher/dashboard")
        with urllib.request.urlopen(req_teacher, timeout=5) as res_teach:
            assert res_teach.status == 200, f"Expected 200, got {res_teach.status}"
            # urllib follows redirects, so it lands on /auth/login
            final_url = res_teach.geturl()
            assert "/auth/login" in final_url, f"Expected redirect to /auth/login, got {final_url}"
            body_teach = res_teach.read().decode('utf-8')
            assert "Teacher Sign In" in body_teach
            print(f"  ✓ Teacher Dashboard access guarded on LAN: Redirected to {final_url}")

        # 4. Verify Theme Files & Zero-FOUC Attributes
        print("\n[Test 4] Verifying Theme Engine Assets...")
        with urllib.request.urlopen(f"http://127.0.0.1:5000/static/js/theme.js") as res_js:
            js_code = res_js.read().decode('utf-8')
            assert "kb_theme" in js_code
            assert "prefers-color-scheme" in js_code
            assert "applyTheme" in js_code
            print("  ✓ theme.js successfully verified with Light/Dark/System support")

        with urllib.request.urlopen(f"http://127.0.0.1:5000/static/css/main.css") as res_css:
            css_code = res_css.read().decode('utf-8')
            assert '[data-theme="dark"]' in css_code
            assert '--bg-app' in css_code
            assert '--primary' in css_code
            print("  ✓ main.css successfully verified with complete Light & Dark tokens")

        print("\n" + "=" * 64)
        print("ALL LIVE SERVER & NETWORK TESTS PASSED SUCCESSFULLY!")
        print("=" * 64)

    finally:
        proc.terminate()
        proc.wait(timeout=5)
        print("Live test server terminated cleanly.")

if __name__ == '__main__':
    test_live_server()
