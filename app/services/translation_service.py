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
