import os
import secrets
import logging
from flask import Flask, render_template, session, request
from config import config_by_name
from app.database import close_db, init_db

def create_app(config_name='default'):
    """Application Factory for Kitaab Bank."""
    app = Flask(__name__)
    config_cls = config_by_name.get(config_name, config_by_name['default'])
    app.config.from_object(config_cls)

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

    # Initialize SQLite database with WAL mode if not existing
    db_file = app.config['DATABASE_PATH']
    if not db_file.exists():
        app.logger.info("Initializing new database...")
        init_db(app)
    else:
        # Ensure default teacher & sample books exist in established database
        with app.app_context():
            from app.database import get_db
            from app.seed_data import seed_sample_books
            try:
                db = get_db()
                cur = db.cursor()
                cur.execute("SELECT COUNT(*) FROM teachers;")
                if cur.fetchone()[0] == 0:
                    from werkzeug.security import generate_password_hash
                    pwd_hash = generate_password_hash("Teacher@123")
                    cur.execute(
                        "INSERT INTO teachers (username, password_hash, full_name, email, role, is_active) "
                        "VALUES (?, ?, ?, ?, ?, 1);",
                        ('teacher', pwd_hash, 'School Teacher / Incharge', 'teacher@school.edu.pk', 'admin')
                    )
                    db.commit()
                
                # Seed sample books if catalog empty
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
        target = request.referrer or url_for('student.index')
        resp = redirect(target)
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
            # Allow static files and the active restore / exit-demo routes to complete
            if path.startswith('/static/') or path == '/favicon.ico':
                return
            if path in ('/teacher/settings/seed-demo', '/teacher/settings/exit-demo', '/teacher/settings'):
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
