from flask import render_template, session, redirect, url_for, flash, request, abort, current_app
from . import teacher_bp
from app.database import get_db
from app.services import donation_service, request_service, handover_service, book_service, qr_service

@teacher_bp.context_processor
def inject_teacher_globals():
    """Make pending counts available across all teacher templates for badges."""
    try:
        pending_donations = donation_service.get_pending_donations_count()
        pending_requests = request_service.get_pending_requests_count()
    except Exception:
        pending_donations = 0
        pending_requests = 0
    return dict(
        pending_donations_count=pending_donations,
        pending_requests_count=pending_requests
    )

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

    cur.execute("SELECT COUNT(*) FROM books WHERE status = 'available' AND is_approved = 1;")
    available_books = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM books WHERE status = 'handed_over';")
    reused_books = cur.fetchone()[0]

    pending_donations = donation_service.get_pending_donations_count()
    pending_requests = request_service.get_pending_requests_count()

    cur.execute("SELECT COUNT(*) FROM requests WHERE status = 'approved';")
    approved_requests = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM handovers;")
    completed_handovers = cur.fetchone()[0]

    stats = {
        'available_books': available_books,
        'pending_donations': pending_donations,
        'pending_requests': pending_requests,
        'approved_requests': approved_requests,
        'completed_handovers': completed_handovers,
        'reused_books': reused_books,
        'total_reused': completed_handovers
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
    """Teacher review queue for student book requests with atomic reservation."""
    status_filter = request.args.get('status', 'pending').strip()
    search_query = request.args.get('q', '').strip()
    class_filter = request.args.get('class_grade', '').strip()

    status_arg = None if status_filter == 'all' else (status_filter or 'pending')

    requests_list, total_count = request_service.get_requests_for_teacher(
        status=status_arg,
        search_query=search_query,
        class_grade=class_filter
    )

    counts = {
        'pending': request_service.get_pending_requests_count(),
        'all': request_service.get_requests_for_teacher(status=None)[1],
        'approved': request_service.get_requests_for_teacher(status='approved')[1],
        'rejected': request_service.get_requests_for_teacher(status='rejected')[1],
        'completed': request_service.get_requests_for_teacher(status='completed')[1]
    }

    return render_template(
        'teacher/requests.html',
        requests=requests_list,
        total_count=total_count,
        current_status=status_filter,
        search_query=search_query,
        class_filter=class_filter,
        counts=counts
    )

@teacher_bp.route('/requests/<int:request_id>')
def request_detail(request_id):
    """Detailed inspection modal/page for a single student request."""
    req = request_service.get_request_by_id(request_id)
    if not req:
        abort(404)
    return render_template('teacher/request_detail.html', request_item=req)

@teacher_bp.route('/requests/<int:request_id>/approve', methods=['POST'])
def approve_request(request_id):
    """Teacher approval action: atomically reserves the book for the student."""
    teacher_id = session.get('teacher_id')
    teacher_name = session.get('teacher_name') or 'Teacher'

    success, book_code, err = request_service.approve_request(request_id, teacher_id, teacher_name)
    if success:
        flash(f"Request approved! Book '{book_code}' is now reserved for pickup.", "success")
    else:
        flash(f"Approval failed: {err}", "danger")

    return redirect(url_for('teacher.requests', status=request.args.get('status', 'pending')))

@teacher_bp.route('/requests/<int:request_id>/reject', methods=['POST'])
def reject_request(request_id):
    """Teacher rejection action: releases book reservation and records reason."""
    teacher_id = session.get('teacher_id')
    teacher_name = session.get('teacher_name') or 'Teacher'
    reason = request.form.get('reason', '').strip()

    if not reason:
        reason = "Priority allocation or book no longer available for reservation."

    success, _, err = request_service.reject_request(request_id, teacher_id, teacher_name, reason=reason)
    if success:
        flash("Request rejected and archived with recorded reason.", "warning")
    else:
        flash(f"Rejection failed: {err}", "danger")

    return redirect(url_for('teacher.requests', status=request.args.get('status', 'pending')))

@teacher_bp.route('/requests/<int:request_id>/handover', methods=['GET'])
def handover_form(request_id):
    """Physical handover confirmation form."""
    req = request_service.get_request_by_id(request_id)
    if not req:
        abort(404)
    if req['status'] != 'approved':
        flash(f"Cannot perform handover: Request is '{req['status']}' (must be 'approved').", "warning")
        return redirect(url_for('teacher.requests', status=req['status']))

    return render_template('teacher/handover_confirm.html', req=req)

@teacher_bp.route('/requests/<int:request_id>/confirm-handover', methods=['POST'])
def confirm_handover(request_id):
    """Process physical handover confirmation with identity check and book handover."""
    teacher_id = session.get('teacher_id')
    teacher_name = session.get('teacher_name') or 'Teacher'

    id_verified = request.form.get('confirm_id') == '1'
    book_handed_over = request.form.get('confirm_physical') == '1'
    remarks = request.form.get('remarks', '').strip()

    success, handover_code, err = handover_service.confirm_physical_handover(
        request_id=request_id,
        teacher_id=teacher_id,
        teacher_name=teacher_name,
        id_verified=id_verified,
        book_handed_over=book_handed_over,
        remarks=remarks
    )

    if success:
        flash(f"Physical handover successfully recorded! Handover Reference: {handover_code}", "success")
        handover = handover_service.get_handover_by_code(handover_code)
        if handover:
            return redirect(url_for('teacher.handover_detail', handover_id=handover['id']))
        return redirect(url_for('teacher.handovers'))
    else:
        flash(f"Handover failed: {err}", "danger")
        req = request_service.get_request_by_id(request_id)
        if req and req['status'] == 'approved':
            return render_template('teacher/handover_confirm.html', req=req, form_data=request.form), 400
        return redirect(url_for('teacher.requests'))

@teacher_bp.route('/requests/<int:request_id>/cancel-reservation', methods=['POST'])
def cancel_reservation(request_id):
    """Teacher action to release an uncollected reservation back to the catalogue."""
    teacher_id = session.get('teacher_id')
    teacher_name = session.get('teacher_name') or 'Teacher'
    reason = request.form.get('reason', '').strip()

    if not reason:
        flash("Please provide a reason for cancelling this reservation.", "danger")
        return redirect(url_for('teacher.requests', status='approved'))

    success, book_code, err = handover_service.cancel_approved_reservation(
        request_id=request_id,
        teacher_id=teacher_id,
        teacher_name=teacher_name,
        reason=reason
    )

    if success:
        flash(f"Reservation cancelled. Book '{book_code}' has been restored to the catalogue as Available.", "warning")
    else:
        flash(f"Cancellation failed: {err}", "danger")

    return redirect(url_for('teacher.requests', status='approved'))

@teacher_bp.route('/handovers')
def handovers():
    """Dedicated Teacher Handover Ledger with search, class and date filtering."""
    search_query = request.args.get('q', '').strip()
    class_filter = request.args.get('class_grade', '').strip()
    date_from = request.args.get('date_from', '').strip()
    date_to = request.args.get('date_to', '').strip()

    handovers_list, total_count = handover_service.get_handovers_for_teacher(
        search_query=search_query,
        class_grade=class_filter,
        date_from=date_from,
        date_to=date_to
    )
    metrics = handover_service.get_handover_metrics()

    return render_template(
        'teacher/handovers.html',
        handovers=handovers_list,
        total_count=total_count,
        search_query=search_query,
        class_filter=class_filter,
        date_from=date_from,
        date_to=date_to,
        metrics=metrics
    )

@teacher_bp.route('/handovers/<int:handover_id>')
def handover_detail(handover_id):
    """Detailed inspection view for a completed physical handover."""
    handover = handover_service.get_handover_by_id(handover_id)
    if not handover:
        abort(404)
    return render_template('teacher/handover_detail.html', handover=handover)

@teacher_bp.route('/handovers/<int:handover_id>/receipt')
def handover_receipt(handover_id):
    """Printable physical handover receipt for official records."""
    handover = handover_service.get_handover_by_id(handover_id)
    if not handover:
        abort(404)

    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT value FROM system_settings WHERE key = 'school_name' LIMIT 1;")
    setting_row = cur.fetchone()
    school_name = setting_row['value'] if setting_row else current_app.config.get('SCHOOL_NAME', 'Government High School')

    return render_template('teacher/handover_receipt.html', handover=handover, school_name=school_name)

@teacher_bp.route('/books/<code_or_id>/qr')
def book_qr_label(code_or_id):
    """Printable single textbook sticker label with high-contrast QR code."""
    book = book_service.get_book_by_code_or_id(code_or_id)
    if not book:
        abort(404)

    payload = qr_service.get_book_qr_payload(book['book_code'])
    qr_data_uri = qr_service.generate_qr_data_uri(payload, box_size=8, border=2)

    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT value FROM system_settings WHERE key = 'school_name' LIMIT 1;")
    row = cur.fetchone()
    school_name = row['value'] if row else current_app.config.get('SCHOOL_NAME', 'Government High School')

    return render_template(
        'teacher/book_qr_label.html',
        book=book,
        qr_data_uri=qr_data_uri,
        school_name=school_name
    )

@teacher_bp.route('/qr-sheet')
def qr_sheet():
    """Bulk QR sticker printing center formatted for standard A4 sticker paper."""
    class_filter = request.args.get('class_grade', '').strip()
    subject_filter = request.args.get('subject', '').strip()
    status_filter = request.args.get('status', 'available').strip()
    search_query = request.args.get('q', '').strip()

    books = book_service.get_books_for_labels(
        class_grade=class_filter,
        subject=subject_filter,
        status=status_filter,
        search_query=search_query,
        limit=48
    )

    # Generate QR data URI for each book for offline zero-roundtrip printing
    label_items = []
    for b in books:
        payload = qr_service.get_book_qr_payload(b['book_code'])
        data_uri = qr_service.generate_qr_data_uri(payload, box_size=6, border=2)
        label_items.append({
            'book': b,
            'qr_data_uri': data_uri
        })

    filter_options = book_service.get_filter_options()

    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT value FROM system_settings WHERE key = 'school_name' LIMIT 1;")
    row = cur.fetchone()
    school_name = row['value'] if row else current_app.config.get('SCHOOL_NAME', 'Government High School')

    return render_template(
        'teacher/qr_sheet.html',
        books=books,
        label_items=label_items,
        filter_options=filter_options,
        selected_class=class_filter,
        selected_subject=subject_filter,
        selected_status=status_filter,
        search_query=search_query,
        school_name=school_name
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
