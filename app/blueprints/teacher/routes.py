from flask import render_template, session, redirect, url_for, flash, request
from . import teacher_bp
from app.database import get_db

@teacher_bp.before_request
def require_teacher_login():
    """Ensure all teacher management and dashboard routes require authenticated session."""
    if not session.get('teacher_id'):
        flash("Please sign in with your teacher credentials to access the Teacher Desk.", "warning")
        return redirect(url_for('auth.login', next=request.path))

@teacher_bp.route('/')
@teacher_bp.route('/dashboard')
def dashboard():
    """Teacher administrative dashboard overview."""
    db = get_db()
    cur = db.cursor()

    cur.execute("SELECT COUNT(*) FROM books WHERE status = 'available' AND is_approved = 1")
    available_books = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM donations WHERE status = 'pending'")
    pending_donations = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM requests WHERE status = 'pending'")
    pending_requests = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM handovers")
    total_reused = cur.fetchone()[0]

    stats = {
        'available_books': available_books,
        'pending_donations': pending_donations,
        'pending_requests': pending_requests,
        'total_reused': total_reused
    }
    return render_template('teacher/dashboard.html', stats=stats)

@teacher_bp.route('/donations')
def donations():
    return render_template(
        'student/placeholder.html',
        title="Donation Review Desk",
        icon="📥",
        description="The teacher queue to inspect, approve, or reject student-donated textbooks will be implemented in Phase 3."
    )

@teacher_bp.route('/requests')
def requests():
    return render_template(
        'student/placeholder.html',
        title="Student Requests Desk",
        icon="📋",
        description="The request management desk with atomic reservation locking will be implemented in Phase 4."
    )

@teacher_bp.route('/handovers')
def handovers():
    return render_template(
        'student/placeholder.html',
        title="Book Handover Desk",
        icon="🤝",
        description="The physical distribution verification and exchange history ledger will be implemented in Phase 5."
    )

@teacher_bp.route('/inventory')
def inventory():
    return render_template(
        'student/placeholder.html',
        title="Book Inventory Management",
        icon="📚",
        description="Full catalog CRUD (adding school books, updating condition, retiring old books) will be implemented in Phase 7."
    )

@teacher_bp.route('/reports')
def reports():
    return render_template(
        'student/placeholder.html',
        title="Library Reports & Analytics",
        icon="📈",
        description="Subject-wise distribution, class reports, and CSV exports will be implemented in Phase 7."
    )

@teacher_bp.route('/settings')
def settings():
    return render_template(
        'student/placeholder.html',
        title="System Settings & Database Backup",
        icon="⚙️",
        description="School profile management and one-click SQLite live snapshot backup will be implemented in Phase 8."
    )
