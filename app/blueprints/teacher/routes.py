from flask import render_template, session, redirect, url_for, flash, request, abort, current_app, Response, send_from_directory
from . import teacher_bp
from app.database import get_db
from app.services import donation_service, request_service, handover_service, book_service, qr_service, analytics_service, activity_service, backup_service, settings_service

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
    """Teacher administrative dashboard overview with live analytics."""
    analytics = analytics_service.get_dashboard_analytics()
    return render_template('teacher/dashboard.html', analytics=analytics)

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
    """Teacher inventory management with status filters, search, and pagination."""
    status_filter = request.args.get('status', 'all').strip()
    search_query = request.args.get('q', '').strip()
    class_filter = request.args.get('class_grade', '').strip()
    subject_filter = request.args.get('subject', '').strip()
    condition_filter = request.args.get('condition', '').strip()
    page = request.args.get('page', 1, type=int)
    if page < 1:
        page = 1

    per_page = 20
    offset = (page - 1) * per_page

    status_arg = None if status_filter == 'all' else status_filter

    books, total_count = book_service.get_inventory_books(
        search_query=search_query,
        class_grade=class_filter,
        subject=subject_filter,
        condition=condition_filter,
        status=status_arg,
        sort_by='newest',
        limit=per_page,
        offset=offset
    )

    counts = book_service.get_inventory_counts()
    filter_options = book_service.get_filter_options()
    total_pages = (total_count + per_page - 1) // per_page if total_count > 0 else 1

    return render_template(
        'teacher/inventory.html',
        books=books,
        total_count=total_count,
        counts=counts,
        current_status=status_filter,
        search_query=search_query,
        class_filter=class_filter,
        subject_filter=subject_filter,
        condition_filter=condition_filter,
        filter_options=filter_options,
        current_page=page,
        total_pages=total_pages
    )

@teacher_bp.route('/inventory/new', methods=['GET', 'POST'])
def new_book():
    """Add a new textbook directly into library inventory."""
    if request.method == 'POST':
        teacher_id = session.get('teacher_id')
        teacher_name = session.get('teacher_name') or 'Teacher'
        image_file = request.files.get('book_image')

        success, book_id, book_code, err = book_service.add_inventory_book(
            data=request.form,
            image_file=image_file,
            teacher_id=teacher_id,
            teacher_name=teacher_name
        )

        if success:
            flash(f"Textbook added successfully! Book Code assigned: '{book_code}'.", "success")
            return redirect(url_for('teacher.inventory'))
        else:
            flash(f"Failed to add textbook: {err}", "danger")
            return render_template(
                'teacher/book_form.html',
                is_edit=False,
                action_url=url_for('teacher.new_book'),
                form_data=request.form
            ), 400

    return render_template(
        'teacher/book_form.html',
        is_edit=False,
        action_url=url_for('teacher.new_book')
    )

@teacher_bp.route('/inventory/<int:book_id>/edit', methods=['GET', 'POST'])
def edit_book(book_id):
    """Edit metadata and syllabus information of an existing textbook."""
    book = book_service.get_book_by_code_or_id(book_id)
    if not book:
        abort(404)

    if request.method == 'POST':
        teacher_id = session.get('teacher_id')
        teacher_name = session.get('teacher_name') or 'Teacher'
        image_file = request.files.get('book_image')

        success, err = book_service.update_inventory_book(
            book_id=book_id,
            data=request.form,
            image_file=image_file,
            teacher_id=teacher_id,
            teacher_name=teacher_name
        )

        if success:
            flash(f"Textbook '{book['book_code']}' updated successfully.", "success")
            return redirect(url_for('teacher.inventory'))
        else:
            flash(f"Failed to update textbook: {err}", "danger")
            return render_template(
                'teacher/book_form.html',
                is_edit=True,
                book=book,
                action_url=url_for('teacher.edit_book', book_id=book_id),
                form_data=request.form
            ), 400

    return render_template(
        'teacher/book_form.html',
        is_edit=True,
        book=book,
        action_url=url_for('teacher.edit_book', book_id=book_id)
    )

@teacher_bp.route('/inventory/<int:book_id>/status', methods=['POST'])
def update_book_status(book_id):
    """Change textbook status (e.g. retire damaged copy or restore to available)."""
    teacher_id = session.get('teacher_id')
    teacher_name = session.get('teacher_name') or 'Teacher'
    new_status = request.form.get('new_status', '').strip()
    reason = request.form.get('reason', '').strip()

    success, err = book_service.retire_or_restore_book(
        book_id=book_id,
        new_status=new_status,
        reason=reason,
        teacher_id=teacher_id,
        teacher_name=teacher_name
    )

    if success:
        action_text = "retired" if new_status == 'retired' else "restored to circulation"
        flash(f"Textbook has been {action_text} successfully.", "success")
    else:
        flash(f"Status update failed: {err}", "danger")

    return redirect(url_for('teacher.inventory', status=request.args.get('status', 'all')))

@teacher_bp.route('/reports')
def reports():
    """Teacher administrative reports and statistical analytics desk."""
    report_data = analytics_service.get_detailed_reports()

    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT value FROM system_settings WHERE key = 'school_name' LIMIT 1;")
    setting_row = cur.fetchone()
    school_name = setting_row['value'] if setting_row else current_app.config.get('SCHOOL_NAME', 'Government High School')

    return render_template('teacher/reports.html', report=report_data, school_name=school_name)

@teacher_bp.route('/reports/export/inventory.csv')
def export_inventory_csv():
    """Download full book inventory as CSV for school spreadsheets."""
    csv_text = analytics_service.generate_inventory_csv()
    return Response(
        csv_text,
        mimetype='text/csv; charset=utf-8',
        headers={
            'Content-Disposition': 'attachment; filename="kitab_bank_inventory.csv"'
        }
    )

@teacher_bp.route('/reports/export/handovers.csv')
def export_handovers_csv():
    """Download complete handover ledger as CSV for school administration records."""
    csv_text = analytics_service.generate_handovers_csv()
    return Response(
        csv_text,
        mimetype='text/csv; charset=utf-8',
        headers={
            'Content-Disposition': 'attachment; filename="kitab_bank_handovers.csv"'
        }
    )

@teacher_bp.route('/logs')
def activity_logs():
    """System activity logs and audit trail."""
    action_filter = request.args.get('action', '').strip()
    actor_filter = request.args.get('actor_type', '').strip()
    search_query = request.args.get('q', '').strip()
    date_from = request.args.get('date_from', '').strip()
    date_to = request.args.get('date_to', '').strip()
    page = request.args.get('page', 1, type=int)
    if page < 1:
        page = 1

    per_page = 50
    offset = (page - 1) * per_page

    logs, total_count = activity_service.get_activity_logs(
        action=action_filter,
        actor_type=actor_filter,
        search_query=search_query,
        date_from=date_from,
        date_to=date_to,
        limit=per_page,
        offset=offset
    )

    distinct_actions = activity_service.get_distinct_actions()
    distinct_actors = activity_service.get_distinct_actor_types()
    total_pages = (total_count + per_page - 1) // per_page if total_count > 0 else 1

    return render_template(
        'teacher/logs.html',
        logs=logs,
        total_count=total_count,
        distinct_actions=distinct_actions,
        distinct_actors=distinct_actors,
        action_filter=action_filter,
        actor_filter=actor_filter,
        search_query=search_query,
        date_from=date_from,
        date_to=date_to,
        current_page=page,
        total_pages=total_pages
    )

@teacher_bp.route('/settings')
def settings():
    """System settings, account security, database live snapshot backups, and exhibition showcase."""
    active_tab = request.args.get('tab', 'profile').strip().lower()
    if active_tab not in ('profile', 'security', 'backup', 'demo'):
        active_tab = 'profile'

    system_settings = settings_service.get_system_settings()
    backups = backup_service.get_all_backups()

    return render_template(
        'teacher/settings.html',
        settings=system_settings,
        backups=backups,
        active_tab=active_tab
    )

@teacher_bp.route('/settings/profile', methods=['POST'])
def update_profile_settings():
    """Update school name, academic year, and default language."""
    school_name = request.form.get('school_name', '').strip()
    academic_year = request.form.get('academic_year', '').strip()
    default_language = request.form.get('default_language', 'en').strip()

    success, error = settings_service.update_school_profile(
        school_name=school_name,
        academic_year=academic_year,
        default_language=default_language,
        updated_by_id=session.get('teacher_id'),
        updated_by_name=session.get('teacher_name')
    )

    if success:
        flash("School profile and system preferences updated successfully.", "success")
    else:
        flash(f"Error updating settings: {error}", "danger")

    return redirect(url_for('teacher.settings', tab='profile'))

@teacher_bp.route('/settings/password', methods=['POST'])
def change_password():
    """Update teacher account password."""
    current_password = request.form.get('current_password', '')
    new_password = request.form.get('new_password', '')
    confirm_password = request.form.get('confirm_password', '')

    success, error = settings_service.change_teacher_password(
        teacher_id=session.get('teacher_id'),
        current_password=current_password,
        new_password=new_password,
        confirm_password=confirm_password,
        teacher_name=session.get('teacher_name')
    )

    if success:
        flash("Your password has been changed successfully. Please remember your new password.", "success")
    else:
        flash(f"Password change failed: {error}", "danger")

    return redirect(url_for('teacher.settings', tab='security'))

@teacher_bp.route('/settings/backup/create', methods=['POST'])
def create_backup():
    """Generate live snapshot database backup with SHA-256 and integrity check."""
    success, record, error = backup_service.create_database_backup(
        created_by_id=session.get('teacher_id'),
        teacher_name=session.get('teacher_name')
    )

    if success:
        flash(f"Live database backup created successfully: {record['filename']} ({record['file_size_bytes']} bytes, SHA-256 verified).", "success")
    else:
        flash(f"Backup creation failed: {error}", "danger")

    return redirect(url_for('teacher.settings', tab='backup'))

@teacher_bp.route('/settings/backup/<int:backup_id>/download')
def download_backup(backup_id):
    """Download database backup snapshot file."""
    record = backup_service.get_backup_by_id(backup_id)
    if not record:
        abort(404, description="Backup file not found.")

    bck_dir = backup_service.get_backups_dir()
    filepath = bck_dir / record['filename']
    if not filepath.exists():
        abort(404, description="Backup file is missing on server disk.")

    return send_from_directory(str(bck_dir), record['filename'], as_attachment=True)

@teacher_bp.route('/settings/backup/<int:backup_id>/delete', methods=['POST'])
def delete_backup(backup_id):
    """Delete a backup snapshot from disk and catalog."""
    success, error = backup_service.delete_backup(
        backup_id=backup_id,
        teacher_id=session.get('teacher_id'),
        teacher_name=session.get('teacher_name')
    )

    if success:
        flash("Backup deleted successfully.", "success")
    else:
        flash(f"Failed to delete backup: {error}", "danger")

    return redirect(url_for('teacher.settings', tab='backup'))

@teacher_bp.route('/settings/seed-demo', methods=['POST'])
def seed_demo():
    """Reset database and seed realistic exhibition showcase data."""
    try:
        from scripts.seed_demo import reset_and_seed_demo_data
        target_db = current_app.config.get('DATABASE_PATH')
        reset_and_seed_demo_data(target_db=target_db)

        # Audit log
        activity_service.record_activity(
            action='exhibition_demo_reset',
            entity_type='system',
            entity_id=None,
            actor_type='teacher',
            actor_name=session.get('teacher_name', 'Teacher'),
            details="Exhibition demo data reseeded successfully (18 textbooks, donations, requests & handovers)."
        )

        flash("Exhibition Demo Mode activated! 18 textbooks across Classes 6–8 and realistic circulation records populated.", "success")
    except Exception as e:
        flash(f"Exhibition reset failed: {str(e)}", "danger")

    return redirect(url_for('teacher.settings', tab='demo'))
