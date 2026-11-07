"""Isolated WSGI app used by the Windows Playwright regression suite.

Run with:
    python -m waitress --listen=127.0.0.1:5000 scripts.browser_test_server:app

This module deliberately uses TestingConfig storage and never opens the school DB.
"""

from app import create_app
from scripts.seed_demo import reset_and_seed_demo_data
from app.services import backup_service

app = create_app("testing")
with app.app_context():
    # Browser regression tests assert against the full 18-book demo
    # workspace and populated circulation tables, all in the temp DB.
    reset_and_seed_demo_data(
        target_db=app.config['DATABASE_PATH'],
        create_safety_backup=False
    )
    # The backup-settings browser test expects the populated backups table;
    # create one verified snapshot in this disposable test workspace.
    ok, _record, error = backup_service.create_database_backup()
    if not ok:
        raise RuntimeError(f"Could not create browser-test backup fixture: {error}")
