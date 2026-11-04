"""
Local SVG Book Cover Generator
Generates clean, attractive, 100% offline educational SVG book covers.
"""

import sys
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

COVERS_DIR = Path("app/static/img/covers")
COVERS_DIR.mkdir(parents=True, exist_ok=True)

SUBJECT_PALETTES = {
    'math': {
        'bg1': '#1e3a8a', 'bg2': '#0284c7', 'accent': '#38bdf8',
        'icon': '📐', 'sub': 'MATHEMATICS', 'urdu_sub': 'ریاضی'
    },
    'science': {
        'bg1': '#064e3b', 'bg2': '#0d9488', 'accent': '#34d399',
        'icon': '🔬', 'sub': 'GENERAL SCIENCE', 'urdu_sub': 'جنرل سائنس'
    },
    'english': {
        'bg1': '#312e81', 'bg2': '#6366f1', 'accent': '#a5b4fc',
        'icon': '📖', 'sub': 'ENGLISH', 'urdu_sub': 'انگریزی'
    },
    'urdu': {
        'bg1': '#7c2d12', 'bg2': '#ea580c', 'accent': '#fdba74',
        'icon': '✒️', 'sub': 'URDU LITERATURE', 'urdu_sub': 'اردو لازمی'
    },
    'sindhi': {
        'bg1': '#831843', 'bg2': '#e11d48', 'accent': '#f472b6',
        'icon': '📜', 'sub': 'SINDHI LANGUAGE', 'urdu_sub': 'سنڌي ٻولي'
    },
    'computer': {
        'bg1': '#0f172a', 'bg2': '#0284c7', 'accent': '#38bdf8',
        'icon': '💻', 'sub': 'COMPUTER SCIENCE', 'urdu_sub': 'کمپیوٹر ایجوکیشن'
    },
    'islamiat': {
        'bg1': '#14532d', 'bg2': '#16a34a', 'accent': '#86efac',
        'icon': '🕌', 'sub': 'ISLAMIC STUDIES', 'urdu_sub': 'اسلامیات'
    },
    'social': {
        'bg1': '#713f12', 'bg2': '#ca8a04', 'accent': '#fde047',
        'icon': '🌍', 'sub': 'SOCIAL STUDIES', 'urdu_sub': 'معاشرتی علوم'
    }
}

BOOKS_METADATA = [
    ('math_class6.svg', 'math', 'Mathematics', 'Class 6', 'Sindh Textbook Board'),
    ('science_class6.svg', 'science', 'General Science', 'Class 6', 'Sindh Textbook Board'),
    ('urdu_class6.svg', 'urdu', 'اردو لازمی', 'جماعت ششم (Class 6)', 'قومی نصاب پبلشرز'),
    ('sindhi_class6.svg', 'sindhi', 'سنڌي سليس', 'درجو ڇھون (Class 6)', 'سنڌ ٽيڪسٽ بڪ بورڊ'),
    ('islamiat_class6.svg', 'islamiat', 'اسلامیات لازمی', 'جماعت ششم (Class 6)', 'پنجاب کریکولم بورڈ'),
    ('social_class6.svg', 'social', 'Social Studies', 'Class 6', 'PTB & STBB'),
    ('math_class7.svg', 'math', 'ریاضی برائے جماعت ہفتم', 'جماعت ہفتم (Class 7)', 'سندھ ٹیکسٹ بک بورڈ'),
    ('science_class7.svg', 'science', 'General Science', 'Class 7', 'Sindh Textbook Board'),
    ('english_class7.svg', 'english', 'English Grammar', 'Class 7', 'Oxford Progressive Curriculum'),
    ('sindhi_class7.svg', 'sindhi', 'سنڌي لازمي', 'درجو ستون (Class 7)', 'سنڌ ٽيڪسٽ بڪ بورڊ'),
    ('computer_class7.svg', 'computer', 'Computer Education', 'Class 7', 'National Curriculum'),
    ('math_class8.svg', 'math', 'Mathematics 8', 'Class 8', 'Sindh Textbook Board'),
    ('science_class8.svg', 'science', 'جنرل سائنس', 'جماعت ہشتم (Class 8)', 'سندھ ٹیکسٹ بک بورڈ'),
    ('urdu_class8.svg', 'urdu', 'اردو قواعد و انشاء', 'جماعت ہشتم (Class 8)', 'پنجاب ٹیکسٹ بک بورڈ'),
    ('computer_class8.svg', 'computer', 'Computer Science', 'Class 8', 'Tech School Series'),
    ('sindhi_class8.svg', 'sindhi', 'سنڌي ٻولي ۽ ادب', 'درجو اٺون (Class 8)', 'سنڌ ٽيڪسٽ بڪ بورڊ')
]

def generate_svg(filename, subj_key, title, grade, publisher):
    pal = SUBJECT_PALETTES.get(subj_key, SUBJECT_PALETTES['english'])
    svg_content = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 420" width="300" height="420">
  <defs>
    <linearGradient id="grad_{subj_key}" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="{pal['bg1']}"/>
      <stop offset="100%" stop-color="{pal['bg2']}"/>
    </linearGradient>
    <linearGradient id="spine" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="rgba(0,0,0,0.4)"/>
      <stop offset="100%" stop-color="rgba(255,255,255,0.05)"/>
    </linearGradient>
  </defs>

  <!-- Book Base Background -->
  <rect width="300" height="420" rx="8" fill="url(#grad_{subj_key})"/>

  <!-- Left Spine Shadow -->
  <rect width="22" height="420" rx="4" fill="url(#spine)"/>
  <line x1="22" y1="0" x2="22" y2="420" stroke="rgba(255,255,255,0.15)" stroke-width="1"/>

  <!-- Top Educational Tag -->
  <rect x="36" y="32" width="130" height="24" rx="12" fill="rgba(255,255,255,0.18)"/>
  <text x="101" y="48" fill="#ffffff" font-family="system-ui, sans-serif" font-size="11" font-weight="700" text-anchor="middle" letter-spacing="1">KITAAB BANK</text>

  <!-- Subject Category -->
  <text x="36" y="88" fill="{pal['accent']}" font-family="system-ui, sans-serif" font-size="12" font-weight="700" letter-spacing="1.5">{pal['sub']}</text>

  <!-- Subject Icon Graphic -->
  <circle cx="230" cy="80" r="32" fill="rgba(255,255,255,0.1)"/>
  <text x="230" y="90" font-size="30" text-anchor="middle">{pal['icon']}</text>

  <!-- Book Title -->
  <text x="36" y="160" fill="#ffffff" font-family="system-ui, 'Noto Nastaliq Urdu', sans-serif" font-size="22" font-weight="800">
    {title[:20]}
  </text>
  <text x="36" y="190" fill="#ffffff" font-family="system-ui, 'Noto Nastaliq Urdu', sans-serif" font-size="18" font-weight="700">
    {title[20:45]}
  </text>

  <!-- Decorative Divider -->
  <line x1="36" y1="215" x2="264" y2="215" stroke="{pal['accent']}" stroke-width="2" opacity="0.6"/>

  <!-- Grade Badge -->
  <rect x="36" y="240" width="160" height="34" rx="6" fill="#ffffff"/>
  <text x="116" y="263" fill="{pal['bg1']}" font-family="system-ui, sans-serif" font-size="14" font-weight="800" text-anchor="middle">
    {grade}
  </text>

  <!-- Syllabus / Board Badge -->
  <text x="36" y="315" fill="rgba(255,255,255,0.85)" font-family="system-ui, sans-serif" font-size="11" font-weight="600">
    CURRICULUM SPECIFICATION:
  </text>
  <text x="36" y="335" fill="#ffffff" font-family="system-ui, 'Noto Nastaliq Urdu', sans-serif" font-size="13" font-weight="600">
    {publisher}
  </text>

  <!-- Bottom Bar with Book Identifier -->
  <rect x="0" y="385" width="300" height="35" rx="0" fill="rgba(0,0,0,0.25)"/>
  <text x="36" y="407" fill="rgba(255,255,255,0.9)" font-family="monospace" font-size="11" font-weight="700">REUSABLE TEXTBOOK</text>
  <text x="264" y="407" fill="{pal['accent']}" font-family="system-ui, sans-serif" font-size="11" font-weight="700" text-anchor="end">GOVT SCHOOLS</text>
</svg>'''
    
    file_path = COVERS_DIR / filename
    file_path.write_text(svg_content, encoding='utf-8')
    print(f"  ✓ Generated: {filename}")

def main():
    print("Generating local SVG book covers...")
    for filename, subj_key, title, grade, publisher in BOOKS_METADATA:
        generate_svg(filename, subj_key, title, grade, publisher)
    
    # Generate generic placeholder
    generate_svg('placeholder.svg', 'english', 'Educational Book', 'Class 6-8', 'Kitaab Bank Resource')
    print(f"Generated {len(BOOKS_METADATA) + 1} SVG covers successfully.")

if __name__ == '__main__':
    main()
