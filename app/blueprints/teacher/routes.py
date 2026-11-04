from flask import render_template, session, redirect, url_for, flash, request, abort
from . import teacher_bp
from app.database import get_db
from app.services import donation_service

@teacher_bp.context_processor
def inject_teacher_globals():
    """Make pending counts available across all teacher templates for badges."""
    try:
        pending_count = donation_service.get_pending_donations_count()
    except Exception:
        pending_count = 0
    return dict(pending_donations_count=pending_count)

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

    pending_donations = donation_service.get_pending_donations_count()

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
    """Teacher review queue for student book donations with filters, search, and status tabs."""
    status_filter = request.args.get('status', 'pending').strip()
    search_query = request.args.get('q', '').strip()
    class_filter = request.args.get('class_grade', '').strip()
    subject_filter = request.args.get('subject', '').strip()

    status_arg = None if status_filter == 'all' else (status_filter or 'pending')

    donations_list, total_count = donation_service.get_donations_for_teacher(
        status=status_arg,
        search_query=search_query,
        class_grade=class_filter,
        subject=subject_filter
    )

    counts = {
        'pending': donation_service.get_pending_donations_count(),
        'all': donation_service.get_donations_for_teacher(status=None)[1],
        'approved': donation_service.get_donations_for_teacher(status='approved')[1],
        'rejected': donation_service.get_donations_for_teacher(status='rejected')[1]
    }

    return render_template(
        'teacher/donations.html',
        donations=donations_list,
        total_count=total_count,
        current_status=status_filter,
        search_query=search_query,
        class_filter=class_filter,
        subject_filter=subject_filter,
        counts=counts
    )

@teacher_bp.route('/donations/<int:donation_id>')
def donation_detail(donation_id):
    """Detailed inspection modal/page for a single donation."""
    donation = donation_service.get_donation_by_id(donation_id)
    if not donation:
        abort(404)
    return render_template('teacher/donation_detail.html', donation=donation)

@teacher_bp.route('/donations/<int:donation_id>/approve', methods=['POST'])
def approve_donation(donation_id):
    """Teacher approval action: creates book record and publishes to catalogue."""
    teacher_id = session.get('teacher_id')
    teacher_name = session.get('teacher_name') or 'Teacher'

    success, book_code, err = donation_service.approve_donation(donation_id, teacher_id, teacher_name)
    if success:
        flash(f"Donation approved successfully! Created catalogue book with code '{book_code}'.", "success")
    else:
        flash(f"Approval failed: {err}", "danger")

    return redirect(url_for('teacher.donations', status=request.args.get('status', 'pending')))

@teacher_bp.route('/donations/<int:donation_id>/reject', methods=['POST'])
def reject_donation(donation_id):
    """Teacher rejection action: records reason and retains historical record."""
    teacher_id = session.get('teacher_id')
    teacher_name = session.get('teacher_name') or 'Teacher'
    reason = request.form.get('reason', '').strip()

    if not reason:
        reason = "Does not meet school curriculum or physical condition criteria."

    success, _, err = donation_service.reject_donation(donation_id, teacher_id, teacher_name, reason=reason)
    if success:
        flash("Donation rejected and archived with recorded reason.", "warning")
    else:
        flash(f"Rejection failed: {err}", "danger")

    return redirect(url_for('teacher.donations', status=request.args.get('status', 'pending')))

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
