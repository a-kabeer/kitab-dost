import os
import secrets
import logging
import tempfile
from pathlib import Path
from flask import Flask, render_template, session, request
from config import config_by_name
from app.database import close_db, get_db, init_db, check_and_recover_interrupted_restore

def create_app(config_name='default'):
    """Application Factory for Kitaab Bank."""
    app = Flask(__name__)
    config_cls = config_by_name.get(config_name, config_by_name['default'])
    app.config.from_object(config_cls)

    # A testing app must never initialize or mutate the developer's real
    # school database, uploads, QR files, or backup directory.
    if config_name == 'testing':
        test_storage = tempfile.TemporaryDirectory(prefix='kitaab-bank-test-')
        app.extensions['kitaab_bank_test_storage'] = test_storage
        test_root = Path(test_storage.name)
        app.config.update({
            'DATABASE_PATH': test_root / 'kitaab_bank_test.db',
            'UPLOAD_FOLDER': test_root / 'uploads' / 'books',
            'QR_FOLDER': test_root / 'uploads' / 'qr',
            'BACKUP_FOLDER': test_root / 'backups'
        })

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
    )

    # Ensure required directories exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['QR_FOLDER'], exist_ok=True)
    os.makedirs(app.config['BACKUP_FOLDER'], exist_ok=True)

    # Database lifecycle hooks
    app.teardown_appcontext(close_db)

    # Always inspect the restore marker before opening the live database.
    # This also covers restarts where the database file already exists.
    with app.app_context():
        if not check_and_recover_interrupted_restore(app):
            raise RuntimeError(
                "Interrupted database restore could not be recovered. "
                "Startup aborted to protect school data; inspect the restore marker and rollback snapshot."
            )

    # Run idempotent schema setup and additive migrations on every startup.
    # Existing databases need migrations too; initializing only newly-created
    # files silently leaves deployed school databases on old schemas.
    db_file = app.config['DATABASE_PATH']
    database_already_existed = db_file.exists()
    if not database_already_existed:
        app.logger.info("Initializing new database...")
    init_db(app)

    # Preserve the existing behavior of ensuring the sample catalogue exists
    # for an already-established database, without seeding a new empty school DB.
    if database_already_existed:
        with app.app_context():
            from app.seed_data import seed_sample_books
            try:
                seed_sample_books()
            except Exception as e:
                app.logger.warning(f"Database seed check error: {e}")

    # Simple session-based CSRF token generator
    @app.context_processor
    def inject_csrf_token():
        if 'csrf_token' not in session:
            session['csrf_token'] = secrets.token_hex(24)
        return dict(csrf_token=lambda: session['csrf_token'])

    # Multilingual & RTL Localization Context Processor
    from app.services import translation_service

    @app.context_processor
    def inject_localization():
        lang = session.get('lang') or request.cookies.get('kb_lang') or request.args.get('lang', 'en')
        if lang not in translation_service.SUPPORTED_LANGUAGES:
            lang = 'en'
        meta = translation_service.get_language_meta(lang)

        is_demo = False
        try:
            db = get_db()
            cur = db.cursor()
            cur.execute("SELECT value FROM system_settings WHERE key = 'is_demo_mode' LIMIT 1;")
            row = cur.fetchone()
            is_demo = bool(row and row[0] == '1')
        except Exception:
            pass

        return {
            'current_lang': lang,
            'is_rtl': meta['dir'] == 'rtl',
            'lang_dir': meta['dir'],
            'supported_languages': translation_service.SUPPORTED_LANGUAGES,
            '_t': lambda key, default=None, **kwargs: translation_service.translate(key, lang=lang, default=default, **kwargs),
            'format_activity_detail': lambda details: translation_service.localize_activity_details(details, lang=lang),
            'is_demo_mode': is_demo
        }

    @app.template_filter('format_activity_detail')
    def filter_format_activity_detail(details):
        lang = session.get('lang') or request.cookies.get('kb_lang') or 'en'
        return translation_service.localize_activity_details(details, lang=lang)


    @app.route('/set-language/<lang_code>')
    def set_language(lang_code):
        from flask import redirect, url_for
        if lang_code not in translation_service.SUPPORTED_LANGUAGES:
            lang_code = 'en'
        session['lang'] = lang_code
        target = request.referrer
        if target:
            from urllib.parse import urlparse
            ref_url = urlparse(request.host_url)
            target_url = urlparse(target)
            safe_target = (
                target_url.scheme in ('', 'http', 'https')
                and (not target_url.netloc or target_url.netloc == ref_url.netloc)
            )
            if not safe_target:
                target = None
        resp = redirect(target or url_for('student.index'))
        resp.set_cookie('kb_lang', lang_code, max_age=30*24*3600, samesite='Lax')
        return resp

    # Track in-flight requests for deterministic connection draining
    @app.before_request
    def track_in_flight_request():
        from app.services import maintenance_service
        from flask import g
        import uuid
        g.request_id = str(uuid.uuid4())
        maintenance_service.register_request(g.request_id)

    @app.teardown_request
    def untrack_in_flight_request(exception=None):
        from app.services import maintenance_service
        from flask import g
        req_id = getattr(g, 'request_id', None)
        if req_id:
            maintenance_service.unregister_request(req_id)

    # Database Maintenance Concurrency Protection
    @app.before_request
    def check_maintenance():
        from app.services import maintenance_service
        if maintenance_service.is_maintenance_active():
            path = request.path
            # The restore controller has already passed before_request before
            # entering maintenance_context. All later dynamic requests must stop.
            if path.startswith('/static/') or path == '/favicon.ico':
                return
            return render_template('errors/503_maintenance.html'), 503

    # CSRF Protection on POST requests
    @app.before_request
    def validate_csrf():
        if app.config.get('TESTING') and app.config.get('WTF_CSRF_ENABLED') is False:
            return
        if request.method in ('POST', 'PUT', 'DELETE', 'PATCH'):
            token = request.form.get('csrf_token')
            expected = session.get('csrf_token')
            if not token or not expected or token != expected:
                app.logger.warning(f"CSRF token mismatch on {request.path}")
                from flask import abort
                abort(400, description="Invalid or missing CSRF token.")

    # Security Headers
    @app.after_request
    def set_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        return response

    # Register Blueprints
    from app.blueprints.student import student_bp
    from app.blueprints.teacher import teacher_bp
    from app.blueprints.auth import auth_bp

    app.register_blueprint(student_bp)
    app.register_blueprint(teacher_bp)
    app.register_blueprint(auth_bp)

    @app.route('/favicon.ico')
    def favicon():
        return app.send_static_file('img/favicon.svg')

    # Error Handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(429)
    def too_many_requests(e):
        return render_template('errors/429.html'), 429

    @app.errorhandler(500)
    def server_error(e):
        return render_template('errors/500.html'), 500

    return app
