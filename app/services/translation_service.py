"""
Translation Service: Multilingual & RTL Localization Engine (English, Urdu اردو, Sindhi سنڌي)
Provides fast, in-memory dictionary lookup with language fallback.
Guarantees preservation of Latin digits in all school codes (KB-BK-, KB-REQ-, KB-HO-).
"""

import json
from pathlib import Path

SUPPORTED_LANGUAGES = {
    'en': {'code': 'en', 'name': 'English', 'native': 'English', 'native_name': 'English', 'dir': 'ltr'},
    'ur': {'code': 'ur', 'name': 'Urdu', 'native': 'اردو', 'native_name': 'اردو', 'dir': 'rtl'},
    'sd': {'code': 'sd', 'name': 'Sindhi', 'native': 'سنڌي', 'native_name': 'سنڌي', 'dir': 'rtl'}
}

_TRANSLATION_CACHE = {}

def _load_translations(lang_code):
    """Load JSON translation dictionary from app/translations/."""
    if lang_code in _TRANSLATION_CACHE:
        return _TRANSLATION_CACHE[lang_code]

    trans_dir = Path(__file__).resolve().parent.parent / 'translations'
    filepath = trans_dir / f"{lang_code}.json"

    if filepath.exists():
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                _TRANSLATION_CACHE[lang_code] = data
                return data
        except Exception:
            pass

    _TRANSLATION_CACHE[lang_code] = {}
    return _TRANSLATION_CACHE[lang_code]

def translate(key, lang='en', default=None, **kwargs):
    """
    Translate a key string into the target language.
    Fallback hierarchy: Target Language -> English -> Default -> Key itself.
    """
    if not lang or lang not in SUPPORTED_LANGUAGES:
        lang = 'en'

    # 1. Target language
    dict_target = _load_translations(lang)
    val = dict_target.get(key)

    # 2. English fallback
    if val is None and lang != 'en':
        dict_en = _load_translations('en')
        val = dict_en.get(key)

    # 3. Default or Key fallback
    if val is None:
        val = default if default is not None else key

    # Interpolate optional arguments if provided
    if kwargs and isinstance(val, str):
        try:
            val = val.format(**kwargs)
        except Exception:
            pass

    return val

def get_language_meta(lang_code):
    """Return direction ('ltr' or 'rtl') and language metadata."""
    return SUPPORTED_LANGUAGES.get(lang_code, SUPPORTED_LANGUAGES['en'])

import re

_ACTIVITY_PATTERNS = [
    (
        r"^Handover '([^']+)' confirmed: '([^']+)' issued to ([^(]+) \(([^)]+)\)$",
        "کتاب کی ترسیل <bdi class='kb-code'>'\\1'</bdi> مکمل: '\\2' طالب علم \\3 (\\4) کو جاری ہوئی",
        "ڪتاب جي حوالگي <bdi class='kb-code'>'\\1'</bdi> مڪمل: '\\2' شاگرد \\3 (\\4) کي جاري ڪئي وئي"
    ),
    (
        r"^Physical handover ([^ ]+) confirmed by ([^.]+)\. Book '([^']+)' \(([^)]+)\) handed over to ([^(]+) \(([^,]+), Roll ([^)]+)\)\.?$",
        "کتاب کی ترسیل <bdi class='kb-code'>\\1</bdi> تصدیق شدہ از \\2۔ کتاب '\\3' (<bdi class='kb-code'>\\4</bdi>) طالب علم \\5 (\\6، رول \\7) کے حوالے کی گئی",
        "ڪتاب جي حوالگي <bdi class='kb-code'>\\1</bdi> تصديق ٿيل پاران \\2۔ ڪتاب '\\3' (<bdi class='kb-code'>\\4</bdi>) شاگرد \\5 (\\6، رول \\7) جي حوالي ڪيو ويو"
    ),
    (
        r"^Donation '([^']+)' approved into catalogue as '([^']+)'$",
        "عطیہ <bdi class='kb-code'>'\\1'</bdi> منظور ہو کر بطور <bdi class='kb-code'>'\\2'</bdi> کیٹلاگ میں شامل کیا گیا",
        "عطيو <bdi class='kb-code'>'\\1'</bdi> منظور ٿي بطور <bdi class='kb-code'>'\\2'</bdi> ڪيٽلاگ ۾ شامل ڪيو ويو"
    ),
    (
        r"^Donation '([^']+)' submitted by ([^(]+) \(([^)]+)\)$",
        "عطیہ <bdi class='kb-code'>'\\1'</bdi> بذریعہ \\2 (\\3) جمع کرایا گیا",
        "عطيو <bdi class='kb-code'>'\\1'</bdi> پاران \\2 (\\3) جمع ڪرايو ويو"
    ),
    (
        r"^New textbook '([^']+)' \(([^)]+)\) added to inventory$",
        "نیا درسی نصاب '\\1' (<bdi class='kb-code'>\\2</bdi>) ذخیرے میں شامل کیا گیا",
        "نئون درسي ڪتاب '\\1' (<bdi class='kb-code'>\\2</bdi>) ذخيري ۾ شامل ڪيو ويو"
    ),
    (
        r"^Book '([^']+)' \(([^)]+)\) added to inventory by ([^.]+)\.?$",
        "کتاب '\\1' (<bdi class='kb-code'>\\2</bdi>) بذریعہ \\3 ذخیرے میں شامل کی گئی",
        "ڪتاب '\\1' (<bdi class='kb-code'>\\2</bdi>) پاران \\3 ذخيري ۾ شامل ڪيو ويو"
    ),
    (
        r"^Book '([^']+)' \(([^)]+)\) updated by ([^.]+)\.?$",
        "کتاب '\\1' (<bdi class='kb-code'>\\2</bdi>) کی تفصیلات از \\3 تبدیل ہوئیں",
        "ڪتاب '\\1' (<bdi class='kb-code'>\\2</bdi>) جا تفصيل پاران \\3 تبديل ٿيا"
    ),
    (
        r"^Book '([^']+)' \(([^)]+)\) status changed from '([^']+)' to '([^']+)' by ([^.]+)\. Reason: (.*)$",
        "کتاب '\\1' (<bdi class='kb-code'>\\2</bdi>) کی حالت از \\5 تبدیل: \\3 تا \\4۔ وجہ: \\6",
        "ڪتاب '\\1' (<bdi class='kb-code'>\\2</bdi>) جي حالت پاران \\5 تبديل: \\3 کان \\4۔ سبب: \\6"
    ),
    (
        r"^Book '([^']+)' \(([^)]+)\) status changed from '([^']+)' to '([^']+)' by ([^.]+)\.?$",
        "کتاب '\\1' (<bdi class='kb-code'>\\2</bdi>) کی حالت از \\5 تبدیل: \\3 تا \\4",
        "ڪتاب '\\1' (<bdi class='kb-code'>\\2</bdi>) جي حالت پاران \\5 تبديل: \\3 کان \\4"
    ),
    (
        r"^Request '([^']+)' approved: Book '([^']+)' reserved for (.*)$",
        "درخواست <bdi class='kb-code'>'\\1'</bdi> منظور: کتاب <bdi class='kb-code'>'\\2'</bdi> برائے \\3 محفوظ کر دی گئی",
        "درخواست <bdi class='kb-code'>'\\1'</bdi> منظور: ڪتاب <bdi class='kb-code'>'\\2'</bdi> شاگرد \\3 لاءِ محفوظ ڪيو ويو"
    ),
    (
        r"^Request ([^ ]+) approved by ([^.]+)\. Reserved book ([^ ]+) for ([^(]+) \(([^)]+)\)\.?$",
        "درخواست <bdi class='kb-code'>\\1</bdi> منظور از \\2۔ کتاب <bdi class='kb-code'>\\3</bdi> برائے \\4 (\\5) محفوظ کی گئی",
        "درخواست <bdi class='kb-code'>\\1</bdi> منظور پاران \\2۔ ڪتاب <bdi class='kb-code'>\\3</bdi> شاگرد \\4 (\\5) لاءِ محفوظ ڪيو ويو"
    ),
    (
        r"^Book request '([^']+)' submitted for '([^']+)'$",
        "کتاب کی درخواست <bdi class='kb-code'>'\\1'</bdi> برائے '\\2' موصول ہوئی",
        "ڪتاب جي درخواست <bdi class='kb-code'>'\\1'</bdi> درسي ڪتاب '\\2' لاءِ موصول ٿي"
    ),
    (
        r"^Request ([^ ]+) submitted for '([^']+)' \(([^)]+)\) by ([^(]+) \(([^)]+)\)$",
        "درخواست <bdi class='kb-code'>\\1</bdi> برائے '\\2' (<bdi class='kb-code'>\\3</bdi>) از \\4 (\\5) ارسال ہوئی",
        "درخواست <bdi class='kb-code'>\\1</bdi> درسي ڪتاب '\\2' (<bdi class='kb-code'>\\3</bdi>) لاءِ پاران \\4 (\\5) موڪلي وئي"
    ),
    (
        r"^Reservation for book '([^']+)' cancelled by ([^.]+)\. Reason: ([^.]+)\. Book restored to catalogue as available\.?$",
        "کتاب <bdi class='kb-code'>'\\1'</bdi> کی بکنگ از \\2 منسوخ۔ وجہ: \\3۔ کتاب دوبارہ دستیاب کیٹلاگ میں شامل کر دی گئی",
        "ڪتاب <bdi class='kb-code'>'\\1'</bdi> جي بُڪنگ پاران \\2 رد۔ سبب: \\3۔ ڪتاب ٻيهر دستياب ڪيٽلاگ ۾ شامل ڪيو ويو"
    ),
    (
        r"^Teacher '([^']+)' (?:signed in from local workstation|logged in successfully\.?)$",
        "استاد '\\1' نے مقامی ورک اسٹیشن سے لاگ ان کیا",
        "استاد '\\1' مقامي ورڪ اسٽيشن مان لاگ ان ٿيو"
    ),
    (
        r"^Teacher '([^']+)' signed out\.?$",
        "استاد '\\1' نے لاگ آؤٹ کیا",
        "استاد '\\1' لاگ آئوٽ ٿيو"
    )
]

def localize_activity_details(details, lang='en'):
    """
    Localize activity log details into target language (Urdu or Sindhi)
    while preserving book titles, names, classes, and code identifiers.
    Falls back to original string for English or unmatched patterns.
    """
    if not details or lang not in ('ur', 'sd'):
        return details

    idx = 1 if lang == 'ur' else 2
    for item in _ACTIVITY_PATTERNS:
        pat = item[0]
        replacement = item[idx]
        if re.search(pat, details):
            details = re.sub(pat, replacement, details)
            break

    # Localize embedded class taxonomy and roll number labels
    if lang == 'ur':
        details = re.sub(r'\bClass (\d+)', r'جماعت \1', details)
        details = re.sub(r'\bRoll (\d+)', r'رول \1', details)
    elif lang == 'sd':
        details = re.sub(r'\bClass (\d+)', r'ڪلاس \1', details)
        details = re.sub(r'\bRoll (\d+)', r'رول \1', details)

    return details

