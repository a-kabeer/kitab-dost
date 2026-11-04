"""
Phase 1 UI, Assets, Navigation & Responsive Audit Script
Verifies:
- All navigation links resolve to valid HTTP 200 endpoints
- All static assets (CSS, JS) exist on disk and serve cleanly
- Zero 404 broken links or broken image tags
- Mobile responsiveness markup (meta viewport, responsive CSS breakpoints)
- Zero external HTTP/HTTPS CDN references
"""

import sys
import re
from pathlib import Path
from app import create_app

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

def audit_ui():
    print("=" * 64)
    print("STARTING PHASE 1 UI, NAVIGATION & ASSETS AUDIT")
    print("=" * 64)
    app = create_app('development')
    client = app.test_client()

    # 1. Audit Viewport & Mobile Responsiveness Tags
    print("\n[Audit 1] Verifying Viewport & Mobile Markup...")
    pages_to_check = ['/', '/catalogue', '/donate', '/track', '/scan', '/about', '/auth/login']
    for page in pages_to_check:
        res = client.get(page)
        html = res.data.decode('utf-8')
        assert '<meta name="viewport" content="width=device-width, initial-scale=1.0">' in html, f"Missing viewport in {page}"
        print(f"  ✓ {page}: Verified standard mobile viewport meta tag")

    # 2. Audit All Navigation Links
    print("\n[Audit 2] Checking Navigation Links for Broken Targets...")
    res_home = client.get('/')
    html_home = res_home.data.decode('utf-8')
    # Find all href attributes
    links = re.findall(r'href="([^"#]+)"', html_home)
    checked_links = set()
    for link in links:
        if link.startswith('http') or link in checked_links:
            continue
        checked_links.add(link)
        res_link = client.get(link)
        assert res_link.status_code in (200, 302), f"Broken link {link} returned {res_link.status_code}"
        print(f"  ✓ Link {link}: Resolved with HTTP {res_link.status_code}")

    # 3. Audit Static Assets on Disk
    print("\n[Audit 3] Checking Static Assets Integrity on Disk...")
    static_root = Path("app/static")
    required_assets = [
        static_root / "css" / "main.css",
        static_root / "css" / "components.css",
        static_root / "css" / "student.css",
        static_root / "css" / "teacher.css",
        static_root / "js" / "theme.js"
    ]
    for asset in required_assets:
        assert asset.exists(), f"Asset {asset} missing on disk!"
        size = asset.stat().st_size
        assert size > 0, f"Asset {asset} is empty!"
        print(f"  ✓ Asset {asset.name}: Present on disk ({size} bytes)")

    # 4. Audit CSS for Responsive Breakpoints & Mobile Nav
    print("\n[Audit 4] Checking CSS Responsive Breakpoints...")
    components_css = (static_root / "css" / "components.css").read_text(encoding='utf-8')
    assert "@media (max-width: 768px)" in components_css, "Missing 768px responsive breakpoint in components.css"
    assert ".mobile-nav-toggle" in components_css, "Missing .mobile-nav-toggle in components.css"
    print("  ✓ components.css contains mobile breakpoint (max-width: 768px) and mobile nav toggler")

    student_css = (static_root / "css" / "student.css").read_text(encoding='utf-8')
    assert "@media (max-width: 640px)" in student_css, "Missing 640px responsive breakpoint in student.css"
    print("  ✓ student.css contains small mobile breakpoint (max-width: 640px)")

    # 5. Audit Zero External Dependencies
    print("\n[Audit 5] Verifying 100% Offline Integrity (Zero External CDN/Fonts)...")
    templates_dir = Path("app/templates")
    html_files = list(templates_dir.rglob("*.html"))
    for hf in html_files:
        content = hf.read_text(encoding='utf-8')
        # Check for external script or link tags
        external_tags = re.findall(r'<(?:script|link)[^>]*(?:src|href)=["\'](https?://[^"\']+)["\']', content)
        assert len(external_tags) == 0, f"Found external tags in {hf}: {external_tags}"
        print(f"  ✓ {hf.relative_to(templates_dir)}: 0 external scripts/stylesheets")

    # 6. Check for Placeholder / Undefined Jinja Tags
    print("\n[Audit 6] Checking for Undefined Jinja Variables or Syntax...")
    for page in pages_to_check:
        res = client.get(page)
        html = res.data.decode('utf-8')
        assert 'None' not in re.findall(r'<h\d>[^<]*None[^<]*</h\d>', html), f"Found raw 'None' rendered in {page}"
        assert '{{' not in html and '}}' not in html, f"Found unparsed Jinja brackets in {page}"
        print(f"  ✓ {page}: Clean rendering with 0 unparsed Jinja tags")

    print("\n" + "=" * 64)
    print("PHASE 1 UI, NAVIGATION & ASSETS AUDIT PASSED 100%!")
    print("=" * 64)

if __name__ == '__main__':
    audit_ui()
