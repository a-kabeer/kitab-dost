import sys
from playwright.sync_api import sync_playwright

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

EDGE_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
BASE_URL = "http://127.0.0.1:5000"

def login_teacher(page):
    page.goto(f"{BASE_URL}/auth/login")
    page.fill('input[name="username"]', 'teacher')
    page.fill('input[name="password"]', 'Teacher@123')
    page.click('button[type="submit"]')
    page.wait_for_url(f"{BASE_URL}/teacher/dashboard")
    page.wait_for_timeout(300)

def run_checks():
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=EDGE_PATH, headless=True)
        
        # 1. Desktop Tests (1440px and 1024px)
        for vp_w in [1440, 1024]:
            print(f"\n==================================================")
            print(f" TESTING DESKTOP VIEWPORT: {vp_w} x 900")
            print(f"==================================================")
            context = browser.new_context(viewport={"width": vp_w, "height": 900})
            page = context.new_page()
            login_teacher(page)
            
            # Check parent container overflow
            wrap_overflow = page.evaluate("() => window.getComputedStyle(document.getElementById('teacherLayoutWrap')).overflow")
            print(f"Parent #teacherLayoutWrap overflow: {wrap_overflow} (Must not be 'hidden')")
            assert wrap_overflow != 'hidden', "Parent #teacherLayoutWrap must allow sticky child"
            
            # Check sidebar computed positioning
            sb_pos = page.evaluate("() => window.getComputedStyle(document.querySelector('.teacher-sidebar')).position")
            sb_top_style = page.evaluate("() => window.getComputedStyle(document.querySelector('.teacher-sidebar')).top")
            print(f"Sidebar position: {sb_pos} (Expected 'sticky')")
            print(f"Sidebar computed top: {sb_top_style}")
            assert sb_pos == 'sticky', f"Sidebar position must be sticky, got {sb_pos}"
            
            # Initial rects at scrollY = 0
            h_rect_0 = page.evaluate("() => document.querySelector('header.sticky-top').getBoundingClientRect()")
            sb_rect_0 = page.evaluate("() => document.querySelector('.teacher-sidebar').getBoundingClientRect()")
            print(f"ScrollY = 0:")
            print(f"  Header bottom: {h_rect_0['bottom']}px, Sidebar top: {sb_rect_0['top']}px, Sidebar bottom: {sb_rect_0['bottom']}px")
            
            # Scroll page down deeply (300px, 600px, 1000px)
            for scroll_val in [300, 600, 1000]:
                page.evaluate(f"() => window.scrollTo(0, {scroll_val})")
                page.wait_for_timeout(100)
                
                win_scroll = page.evaluate("() => window.scrollY")
                h_rect = page.evaluate("() => document.querySelector('header.sticky-top').getBoundingClientRect()")
                sb_rect = page.evaluate("() => document.querySelector('.teacher-sidebar').getBoundingClientRect()")
                
                overlap = sb_rect['top'] < (h_rect['bottom'] - 1)
                in_viewport = (sb_rect['top'] >= 0 and sb_rect['bottom'] <= 901)
                
                print(f"ScrollY = {win_scroll}px:")
                print(f"  Header bottom: {h_rect['bottom']}px, Sidebar top: {sb_rect['top']}px, Sidebar bottom: {sb_rect['bottom']}px")
                print(f"  Overlap with header: {overlap} (Must be False)")
                print(f"  Sidebar within viewport: {in_viewport} (Must be True)")
                
                assert not overlap, f"Sidebar overlapped header at scrollY={scroll_val}"
                assert in_viewport, f"Sidebar outside viewport bounds at scrollY={scroll_val}"
                assert sb_rect['top'] >= h_rect['bottom'] - 1, f"Sidebar top ({sb_rect['top']}) should be at or below header bottom ({h_rect['bottom']})"
            
            # Check horizontal overflow
            h_overflow = page.evaluate("() => document.documentElement.scrollWidth > window.innerWidth")
            print(f"Horizontal overflow at {vp_w}px: {h_overflow} (Must be False)")
            assert not h_overflow, f"Horizontal overflow detected at {vp_w}px"
            
            context.close()
            
        # 2. Independent Sidebar Scrolling on Short Viewport (500px)
        print(f"\n==================================================")
        print(f" TESTING INDEPENDENT SIDEBAR SCROLLING: 1440 x 500")
        print(f"==================================================")
        context = browser.new_context(viewport={"width": 1440, "height": 500})
        page = context.new_page()
        login_teacher(page)
        
        sb_sh = page.evaluate("() => document.querySelector('.teacher-sidebar').scrollHeight")
        sb_ch = page.evaluate("() => document.querySelector('.teacher-sidebar').clientHeight")
        print(f"Sidebar scrollHeight: {sb_sh}px, clientHeight: {sb_ch}px")
        assert sb_sh > sb_ch, "Sidebar must have scrollable content when viewport is short"
        
        # Test internal scroll
        page.evaluate("() => document.querySelector('.teacher-sidebar').scrollTop = 120")
        sb_st = page.evaluate("() => document.querySelector('.teacher-sidebar').scrollTop")
        print(f"Sidebar internal scrollTop: {sb_st}px (Must be > 0)")
        assert sb_st > 0, "Sidebar internal scrolling failed"
        context.close()
        
        # 3. Mobile Viewports (768px, 390px, 360px) & Offcanvas
        for vp_w, vp_h in [(768, 1024), (390, 844), (360, 640)]:
            print(f"\n==================================================")
            print(f" TESTING MOBILE/TABLET VIEWPORT: {vp_w} x {vp_h}")
            print(f"==================================================")
            context = browser.new_context(viewport={"width": vp_w, "height": vp_h})
            page = context.new_page()
            login_teacher(page)
            
            # Check desktop sidebar is hidden
            sb_disp = page.evaluate("() => window.getComputedStyle(document.querySelector('.teacher-sidebar')).display")
            print(f"Desktop sidebar display: {sb_disp} (Must be 'none')")
            assert sb_disp == 'none', f"Desktop sidebar should be hidden at {vp_w}px"
            
            # Check hamburger button is visible
            hamburger = page.query_selector('button[data-bs-target="#teacherSidebarOffcanvas"]')
            assert hamburger is not None and hamburger.is_visible(), "Hamburger button must be visible"
            
            # Open offcanvas
            hamburger.click()
            page.wait_for_selector('#teacherSidebarOffcanvas.show', state='visible')
            offcanvas_visible = page.is_visible('#teacherSidebarOffcanvas')
            print(f"Offcanvas drawer opened: {offcanvas_visible}")
            assert offcanvas_visible, "Offcanvas drawer failed to open"
            
            # Close offcanvas
            close_btn = page.query_selector('#teacherSidebarOffcanvas .btn-close')
            close_btn.click()
            page.wait_for_timeout(400)
            offcanvas_open_after = page.evaluate("() => document.getElementById('teacherSidebarOffcanvas').classList.contains('show')")
            print(f"Offcanvas drawer closed: {not offcanvas_open_after}")
            assert not offcanvas_open_after, "Offcanvas drawer failed to close"
            
            # Check horizontal overflow
            h_overflow = page.evaluate("() => document.documentElement.scrollWidth > window.innerWidth")
            print(f"Horizontal overflow at {vp_w}px: {h_overflow} (Must be False)")
            assert not h_overflow, f"Horizontal overflow detected at {vp_w}px"
            
            context.close()
            
        # 4. RTL Multilingual (Urdu & Sindhi) Sticky Check
        print(f"\n==================================================")
        print(f" TESTING RTL (URDU & SINDHI) STICKY SIDEBAR")
        print(f"==================================================")
        for lang in ['ur', 'sd']:
            context = browser.new_context(viewport={"width": 1440, "height": 900})
            page = context.new_page()
            login_teacher(page)
            page.goto(f"{BASE_URL}/set_language/{lang}")
            page.goto(f"{BASE_URL}/teacher/dashboard")
            page.wait_for_timeout(200)
            
            # Scroll down
            page.evaluate("() => window.scrollTo(0, 600)")
            page.wait_for_timeout(100)
            
            h_rect = page.evaluate("() => document.querySelector('header.sticky-top').getBoundingClientRect()")
            sb_rect = page.evaluate("() => document.querySelector('.teacher-sidebar').getBoundingClientRect()")
            
            overlap = sb_rect['top'] < (h_rect['bottom'] - 1)
            in_viewport = (sb_rect['top'] >= 0 and sb_rect['bottom'] <= 901)
            
            print(f"Language {lang}:")
            print(f"  Header bottom: {h_rect['bottom']}px, Sidebar top: {sb_rect['top']}px, bottom: {sb_rect['bottom']}px")
            print(f"  Overlap: {overlap} (False), In viewport: {in_viewport} (True)")
            
            assert not overlap, f"RTL {lang} sidebar overlapped header"
            assert in_viewport, f"RTL {lang} sidebar outside viewport"
            
            # Check horizontal overflow
            h_overflow = page.evaluate("() => document.documentElement.scrollWidth > window.innerWidth")
            print(f"  Horizontal overflow in {lang}: {h_overflow} (Must be False)")
            assert not h_overflow, f"Horizontal overflow in {lang}"
            
            context.close()
            
        browser.close()
        print("\n>>> ALL DESKTOP SIDEBAR STICKY & SCROLLING VERIFICATIONS PASSED CLEANLY! <<<")

if __name__ == '__main__':
    run_checks()
