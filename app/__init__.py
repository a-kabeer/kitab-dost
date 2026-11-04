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

    # CSRF Protection on POST requests
    @app.before_request
    def validate_csrf():
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
