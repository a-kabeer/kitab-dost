"""Isolated WSGI app used by the Windows Playwright regression suite.

Run with:
    python -m waitress --listen=127.0.0.1:5000 scripts.browser_test_server:app

This module deliberately uses TestingConfig storage and never opens the school DB.
"""

from app import create_app
from app.seed_data import seed_sample_books

app = create_app("testing")
with app.app_context():
    seed_sample_books()
