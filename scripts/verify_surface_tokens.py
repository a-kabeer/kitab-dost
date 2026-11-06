import sys
from playwright.sync_api import sync_playwright

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

EDGE_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

def rgb_to_hex(rgb_str):
    if not rgb_str or 'rgb' not in rgb_str:
        return rgb_str
    nums = [int(x.strip()) for x in rgb_str.replace('rgba(', '').replace('rgb(', '').replace(')', '').split(',')[:3]]
    return f"#{nums[0]:02X}{nums[1]:02X}{nums[2]:02X}"

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=EDGE_PATH, headless=True)
    page = browser.new_page(viewport={"width": 1440, "height": 900})

    # 1. Student Portal Check
    page.goto('http://127.0.0.1:5000/catalogue')
    page.evaluate("() => { localStorage.setItem('kb_theme', 'light'); }")
    page.reload()
    page.wait_for_timeout(300)
    
    body_bg_l = rgb_to_hex(page.evaluate("() => window.getComputedStyle(document.body).backgroundColor"))
    body_color_l = rgb_to_hex(page.evaluate("() => window.getComputedStyle(document.body).color"))
    nav_bg_l = rgb_to_hex(page.evaluate("() => window.getComputedStyle(document.querySelector('header.sticky-top')).backgroundColor"))
    card_bg_l = rgb_to_hex(page.evaluate("() => window.getComputedStyle(document.querySelector('.card')).backgroundColor"))
    card_border_l = rgb_to_hex(page.evaluate("() => window.getComputedStyle(document.querySelector('.card')).borderColor"))
    footer_bg_l = rgb_to_hex(page.evaluate("() => window.getComputedStyle(document.querySelector('footer')).backgroundColor"))
    card_footer_bg_l = rgb_to_hex(page.evaluate("() => window.getComputedStyle(document.querySelector('.card-footer')).backgroundColor"))
    btn_bg_l = rgb_to_hex(page.evaluate("() => window.getComputedStyle(document.querySelector('.btn-primary')).backgroundColor"))
    btn_color_l = rgb_to_hex(page.evaluate("() => window.getComputedStyle(document.querySelector('.btn-primary')).color"))
    muted_color_l = rgb_to_hex(page.evaluate("() => window.getComputedStyle(document.querySelector('.text-muted, .text-body-secondary')).color"))
    
    print("=== STUDENT PORTAL LIGHT THEME ===")
    print(f"  Body BG:        {body_bg_l} (Expected #F1F4F8)")
    print(f"  Body Color:     {body_color_l} (Expected #172033)")
    print(f"  Navbar BG:      {nav_bg_l} (Expected #FFFFFF)")
    print(f"  Card BG:        {card_bg_l} (Expected #FFFFFF)")
    print(f"  Card Footer BG: {card_footer_bg_l} (Expected #E8EDF4)")
    print(f"  Card Border:    {card_border_l} (Expected #DFE5ED)")
    print(f"  Footer BG:      {footer_bg_l} (Expected #FFFFFF)")
    print(f"  Btn Primary BG: {btn_bg_l} (Expected #0369A1)")
    print(f"  Btn Text Color: {btn_color_l} (Expected #FFFFFF)")
    print(f"  Text Muted:     {muted_color_l} (Expected #5F6B7A)")

    # Dark Mode
    page.evaluate("() => { localStorage.setItem('kb_theme', 'dark'); }")
    page.reload()
    page.wait_for_timeout(300)

    body_bg_d = rgb_to_hex(page.evaluate("() => window.getComputedStyle(document.body).backgroundColor"))
    body_color_d = rgb_to_hex(page.evaluate("() => window.getComputedStyle(document.body).color"))
    nav_bg_d = rgb_to_hex(page.evaluate("() => window.getComputedStyle(document.querySelector('header.sticky-top')).backgroundColor"))
    card_bg_d = rgb_to_hex(page.evaluate("() => window.getComputedStyle(document.querySelector('.card')).backgroundColor"))
    card_border_d = rgb_to_hex(page.evaluate("() => window.getComputedStyle(document.querySelector('.card')).borderColor"))
    footer_bg_d = rgb_to_hex(page.evaluate("() => window.getComputedStyle(document.querySelector('footer')).backgroundColor"))
    card_footer_bg_d = rgb_to_hex(page.evaluate("() => window.getComputedStyle(document.querySelector('.card-footer')).backgroundColor"))

    print("\n=== STUDENT PORTAL DARK THEME ===")
    print(f"  Body BG:        {body_bg_d} (Expected #111827)")
    print(f"  Body Color:     {body_color_d} (Expected #F1F5F9)")
    print(f"  Navbar BG:      {nav_bg_d} (Expected #17212F)")
    print(f"  Card BG:        {card_bg_d} (Expected #1E293B)")
    print(f"  Card Footer BG: {card_footer_bg_d} (Expected #263449)")
    print(f"  Card Border:    {card_border_d} (Expected #334155)")
    print(f"  Footer BG:      {footer_bg_d} (Expected #17212F)")

    # 2. Teacher Portal Check (login first)
    page.goto('http://127.0.0.1:5000/auth/login')
    page.fill('input[name="username"]', 'teacher')
    page.fill('input[name="password"]', 'Teacher@123')
    page.click('button[type="submit"]')
    page.wait_for_url('http://127.0.0.1:5000/teacher/dashboard')

    # Teacher Light Mode
    page.evaluate("() => { localStorage.setItem('kb_theme', 'light'); }")
    page.reload()
    page.wait_for_timeout(300)

    t_main_bg_l = rgb_to_hex(page.evaluate("() => window.getComputedStyle(document.querySelector('.teacher-main')).backgroundColor"))
    t_sidebar_bg_l = rgb_to_hex(page.evaluate("() => window.getComputedStyle(document.querySelector('.teacher-sidebar')).backgroundColor"))
    t_sidebar_border_l = rgb_to_hex(page.evaluate("() => window.getComputedStyle(document.querySelector('.teacher-sidebar')).borderColor"))
    t_card_bg_l = rgb_to_hex(page.evaluate("() => window.getComputedStyle(document.querySelector('.card')).backgroundColor"))
    t_card_border_l = rgb_to_hex(page.evaluate("() => window.getComputedStyle(document.querySelector('.card')).borderColor"))

    print("\n=== TEACHER PORTAL LIGHT THEME ===")
    print(f"  Main BG:        {t_main_bg_l} (Expected #F1F4F8)")
    print(f"  Sidebar BG:     {t_sidebar_bg_l} (Expected #FFFFFF)")
    print(f"  Sidebar Border: {t_sidebar_border_l} (Expected #DFE5ED)")
    print(f"  Card BG:        {t_card_bg_l} (Expected #FFFFFF)")
    print(f"  Card Border:    {t_card_border_l} (Expected #DFE5ED)")

    # Teacher Dark Mode
    page.evaluate("() => { localStorage.setItem('kb_theme', 'dark'); }")
    page.reload()
    page.wait_for_timeout(300)

    t_main_bg_d = rgb_to_hex(page.evaluate("() => window.getComputedStyle(document.querySelector('.teacher-main')).backgroundColor"))
    t_sidebar_bg_d = rgb_to_hex(page.evaluate("() => window.getComputedStyle(document.querySelector('.teacher-sidebar')).backgroundColor"))
    t_sidebar_border_d = rgb_to_hex(page.evaluate("() => window.getComputedStyle(document.querySelector('.teacher-sidebar')).borderColor"))
    t_card_bg_d = rgb_to_hex(page.evaluate("() => window.getComputedStyle(document.querySelector('.card')).backgroundColor"))
    t_card_border_d = rgb_to_hex(page.evaluate("() => window.getComputedStyle(document.querySelector('.card')).borderColor"))

    print("\n=== TEACHER PORTAL DARK THEME ===")
    print("  Raw sidebar style:", page.evaluate("() => { const s = window.getComputedStyle(document.querySelector('.teacher-sidebar')); return [s.backgroundColor, s.getPropertyValue('--kb-sidebar-bg')]; }"))
    print(f"  Main BG:        {t_main_bg_d} (Expected #111827)")
    print(f"  Sidebar BG:     {t_sidebar_bg_d} (Expected #17212F)")
    print(f"  Sidebar Border: {t_sidebar_border_d} (Expected #334155)")
    print(f"  Card BG:        {t_card_bg_d} (Expected #1E293B)")
    print(f"  Card Border:    {t_card_border_d} (Expected #334155)")

    # 3. Form Controls Check
    page.goto('http://127.0.0.1:5000/donate')
    page.evaluate("() => { localStorage.setItem('kb_theme', 'light'); }")
    page.reload()
    page.wait_for_timeout(200)

    input_bg_l = rgb_to_hex(page.evaluate("() => window.getComputedStyle(document.querySelector('.form-control')).backgroundColor"))
    input_border_l = rgb_to_hex(page.evaluate("() => window.getComputedStyle(document.querySelector('.form-control')).borderColor"))
    input_color_l = rgb_to_hex(page.evaluate("() => window.getComputedStyle(document.querySelector('.form-control')).color"))

    page.evaluate("() => { localStorage.setItem('kb_theme', 'dark'); }")
    page.reload()
    page.wait_for_timeout(200)

    input_bg_d = rgb_to_hex(page.evaluate("() => window.getComputedStyle(document.querySelector('.form-control')).backgroundColor"))
    input_border_d = rgb_to_hex(page.evaluate("() => window.getComputedStyle(document.querySelector('.form-control')).borderColor"))
    input_color_d = rgb_to_hex(page.evaluate("() => window.getComputedStyle(document.querySelector('.form-control')).color"))

    print("\n=== FORM CONTROLS ===")
    print(f"  Light Input BG:     {input_bg_l} (Expected #FFFFFF)")
    print(f"  Light Input Border: {input_border_l} (Expected #DFE5ED)")
    print(f"  Light Input Text:   {input_color_l} (Expected #172033)")
    print(f"  Dark Input BG:      {input_bg_d} (Expected #1E293B)")
    print(f"  Dark Input Border:  {input_border_d} (Expected #334155)")
    print(f"  Dark Input Text:    {input_color_d} (Expected #F1F5F9)")

    browser.close()
