from flask import render_template, request, redirect, url_for, session, flash
from werkzeug.security import check_password_hash
from urllib.parse import urlparse
from . import auth_bp
from app.database import get_db
from app.services import activity_service

def is_safe_url(target):
    """Ensure redirection target belongs to this application (open-redirect defense)."""
    if not target:
        return False
    ref_url = urlparse(request.host_url)
    test_url = urlparse(target)
    return test_url.scheme in ('', 'http', 'https') and (not test_url.netloc or test_url.netloc == ref_url.netloc)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Teacher authentication login route."""
    if session.get('teacher_id'):
        return redirect(url_for('teacher.dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        next_url = request.args.get('next') or request.form.get('next')

        if not username or not password:
            flash("Please enter both username and password.", "danger")
            return render_template('auth/login.html', username=username, next=next_url)

        db = get_db()
        cur = db.cursor()
        cur.execute(
            "SELECT id, username, password_hash, full_name, role, is_active FROM teachers WHERE username = ?;",
            (username,)
        )
        teacher = cur.fetchone()

        if teacher and teacher['is_active'] and check_password_hash(teacher['password_hash'], password):
            # Establish authenticated session
            session.clear()
            session['teacher_id'] = teacher['id']
            session['teacher_username'] = teacher['username']
            session['teacher_name'] = teacher['full_name']
            session['teacher_role'] = teacher['role']

            # Update last login timestamp
            db.execute("UPDATE teachers SET last_login_at = CURRENT_TIMESTAMP WHERE id = ?;", (teacher['id'],))
            db.commit()

            # Record login audit activity
            activity_service.record_activity(
                action='teacher_login',
                entity_type='teacher',
                entity_id=teacher['id'],
                actor_type='teacher',
                actor_name=teacher['full_name'],
                details=f"Teacher '{teacher['username']}' logged in successfully."
            )

            flash(f"Welcome back, {teacher['full_name']}!", "success")
            if next_url and is_safe_url(next_url):
                return redirect(next_url)
            return redirect(url_for('teacher.dashboard'))
        else:
            flash("Invalid teacher credentials. Please check your username and password.", "danger")

    return render_template('auth/login.html', next=request.args.get('next'))

@auth_bp.route('/logout', methods=['GET', 'POST'])
def logout():
    """Clear session and log teacher out."""
    teacher_name = session.get('teacher_name')
    teacher_id = session.get('teacher_id')
    if teacher_id:
        activity_service.record_activity(
            action='teacher_logout',
            entity_type='teacher',
            entity_id=teacher_id,
            actor_type='teacher',
            actor_name=teacher_name,
            details=f"Teacher '{session.get('teacher_username', 'teacher')}' signed out."
        )

    session.clear()
    flash("You have been signed out of the Teacher Desk.", "info")
    return redirect(url_for('student.index'))
