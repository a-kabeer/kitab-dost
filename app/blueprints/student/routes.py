from flask import render_template, request, abort, url_for, redirect, flash, current_app, Response
from . import student_bp
from app.services import book_service, donation_service, request_service, rate_limiter, qr_service

@student_bp.route('/')
def index():
    """Homepage for students with real-time statistics and featured books from local SQLite database."""
    stats = book_service.get_live_catalogue_stats()
    featured_books = book_service.get_recent_and_featured_books(limit=6)
    return render_template('student/index.html', stats=stats, featured_books=featured_books)

@student_bp.route('/catalogue')
def catalogue():
    """Public book catalogue with search and multi-faceted filtering."""
    search_query = request.args.get('q', '').strip()
    class_grade = request.args.get('class_grade', '').strip()
    subject = request.args.get('subject', '').strip()
    language = request.args.get('language', '').strip()
    condition = request.args.get('condition', '').strip()
    sort_by = request.args.get('sort', 'title_asc').strip()

    books, total_count = book_service.get_available_books(
        search_query=search_query,
        class_grade=class_grade,
        subject=subject,
        language=language,
        condition=condition,
        sort_by=sort_by
    )

    filter_options = book_service.get_filter_options()

    selected_filters = {
        'q': search_query,
        'class_grade': class_grade,
        'subject': subject,
        'language': language,
        'condition': condition,
        'sort': sort_by
    }

    # Count active filters
    active_filters_count = sum(1 for k in ['class_grade', 'subject', 'language', 'condition'] if selected_filters[k])
    if search_query:
        active_filters_count += 1

    return render_template(
        'student/catalogue.html',
        books=books,
        total_count=total_count,
        filter_options=filter_options,
        selected_filters=selected_filters,
        active_filters_count=active_filters_count
    )

@student_bp.route('/book/<code_or_id>')
def book_detail(code_or_id):
    """Detailed view for an individual educational book."""
    book = book_service.get_book_by_code_or_id(code_or_id)
    if not book:
        abort(404)

    # Fetch up to 3 related books in the same class or subject
    related_books, _ = book_service.get_available_books(
        class_grade=book['class_grade'],
        limit=4
    )
    # Exclude current book from related
    related_books = [b for b in related_books if b['id'] != book['id']][:3]

    return render_template('student/book_detail.html', book=book, related_books=related_books)

@student_bp.route('/donate', methods=['GET', 'POST'])
def donate():
    """Student book donation submission form."""
    classes = ['Class 6', 'Class 7', 'Class 8']
    languages = ['Urdu', 'English', 'Sindhi']
    conditions = ['Like New', 'Good', 'Fair']
    subjects = ['Mathematics', 'General Science', 'English', 'Urdu', 'Sindhi', 'Computer Science', 'Islamiat', 'Social Studies']

    if request.method == 'POST':
        # Rate limit defense for shared school Wi-Fi
        limit = current_app.config.get('RATE_LIMIT_DONATE_PER_HOUR', 120)
        if rate_limiter.is_rate_limited('donate', limit, window_seconds=3600):
            flash("You have made multiple donation submissions. Please wait a short while before submitting more.", "warning")
            return render_template(
                'student/donate.html',
                form_data=request.form,
                classes=classes,
                languages=languages,
                conditions=conditions,
                subjects=subjects
            ), 429

        image_file = request.files.get('book_image')
        success, code, error_msg = donation_service.create_donation(request.form, image_file)
        if not success:
            flash(error_msg, "danger")
            return render_template(
                'student/donate.html',
                form_data=request.form,
                classes=classes,
                languages=languages,
                conditions=conditions,
                subjects=subjects
            ), 400

        flash("Book donation submitted successfully! Awaiting teacher review.", "success")
        return redirect(url_for('student.donation_success', donation_code=code))

    return render_template(
        'student/donate.html',
        form_data={},
        classes=classes,
        languages=languages,
        conditions=conditions,
        subjects=subjects
    )

@student_bp.route('/donate/success/<donation_code>')
def donation_success(donation_code):
    """Confirmation screen for a student's book donation."""
    donation = donation_service.get_donation_by_code(donation_code)
    if not donation:
        abort(404)
    return render_template('student/donation_success.html', donation=donation)

@student_bp.route('/request', methods=['GET', 'POST'])
@student_bp.route('/request/<code_or_id>', methods=['GET', 'POST'])
def request_book(code_or_id=None):
    """Student book request workflow with atomic reservation check."""
    book_param = code_or_id or request.args.get('book') or request.form.get('book_id') or request.form.get('book_code')
    book = None
    if book_param:
        book = book_service.get_book_by_code_or_id(book_param)

    if request.method == 'POST':
        # Rate limit defense for shared school Wi-Fi
        limit = current_app.config.get('RATE_LIMIT_REQUEST_PER_HOUR', 120)
        if rate_limiter.is_rate_limited('request', limit, window_seconds=3600):
            flash("You have submitted multiple book requests. Please wait a short while before requesting more.", "warning")
            return render_template(
                'student/request_book.html',
                book=book,
                form_data=request.form
            ), 429

        success, tracking_code, error_msg = request_service.create_book_request(request.form)
        if not success:
            flash(error_msg, "danger")
            return render_template(
                'student/request_book.html',
                book=book,
                form_data=request.form
            ), 400

        flash("Book request submitted successfully! Awaiting teacher review.", "success")
        return redirect(url_for('student.request_success', tracking_code=tracking_code))

    if not book:
        flash("Please select a book from the catalogue to request.", "info")
        return redirect(url_for('student.catalogue'))

    if book['status'] != 'available':
        flash(f"'{book['title']}' ({book['book_code']}) is currently {book['status']} and cannot be requested.", "warning")
        return redirect(url_for('student.book_detail', code_or_id=book['book_code']))

    return render_template(
        'student/request_book.html',
        book=book,
        form_data={}
    )

@student_bp.route('/request/success/<tracking_code>')
def request_success(tracking_code):
    """Confirmation screen displaying unique Tracking Code."""
    req = request_service.get_request_by_tracking_code(tracking_code)
    if not req:
        abort(404)
    return render_template('student/request_success.html', request_item=req)

@student_bp.route('/track', methods=['GET'])
def track():
    """Public tracking desk for checking live request status."""
    tracking_code = request.args.get('code', '').strip().upper()
    req = None
    error_msg = None
    masked_name = None

    if tracking_code:
        # Rate limit defense against brute-force token enumeration
        limit = current_app.config.get('RATE_LIMIT_TRACK_PER_MINUTE', 30)
        if rate_limiter.is_rate_limited('track', limit, window_seconds=60):
            flash("Too many tracking code queries. Please wait a minute before searching again.", "warning")
            return render_template('student/track.html', tracking_code=tracking_code, req=None), 429

        req = request_service.get_request_by_tracking_code(tracking_code)
        if not req:
            error_msg = f"No active request found for code '{tracking_code}'. Please check the 16-character code and try again."
        else:
            # Mask student name for privacy protection
            masked_name = request_service.mask_student_name(req['requester_name'])
            # Strict defense-in-depth: purge private PII from dict before template rendering
            safe_req = dict(req)
            safe_req.pop('requester_roll_no', None)
            safe_req.pop('requester_contact', None)
            safe_req.pop('requester_name', None)
            safe_req.pop('notes', None)
            req = safe_req

    return render_template(
        'student/track.html',
        tracking_code=tracking_code,
        req=req,
        masked_name=masked_name,
        error_msg=error_msg
    )

@student_bp.route('/scan', methods=['GET', 'POST'])
def scan():
    """
    QR Code & Book Code Scanner View.
    Supports camera decoding and prominent manual 6-digit Book Code lookup.
    """
    raw_code = request.args.get('code') or (request.form.get('code') if request.method == 'POST' else None)
    error_msg = None

    if raw_code:
        parsed = qr_service.parse_scanned_book_code(raw_code)

        if parsed['type'] == 'request':
            flash(f"Tracking code detected ({parsed['code']}). Redirected to Tracking Desk.", "info")
            return redirect(url_for('student.track', code=parsed['code']))

        if parsed['type'] == 'donation':
            flash(f"Donation reference detected ({parsed['code']}).", "info")
            return redirect(url_for('student.index'))

        # Look up book in SQLite
        book = book_service.get_book_by_code_or_id(parsed['code'])
        if book:
            return redirect(url_for('student.book_detail', code_or_id=book['book_code']))
        else:
            error_msg = f"No textbook found matching code '{raw_code.strip()}'. Please check the 6-digit code on the label."

    # Fetch recent books for quick sample chips
    sample_books = book_service.get_recent_and_featured_books(limit=6)

    return render_template(
        'student/scan.html',
        code_query=raw_code if error_msg else '',
        error_msg=error_msg,
        sample_books=sample_books
    )

@student_bp.route('/qr/<book_code>.png')
def book_qr_image(book_code):
    """
    Dynamic 100% offline PNG QR generator endpoint for a specific book code.
    Returns high-contrast, scalable PNG bytes with caching headers.
    """
    clean_code = str(book_code).strip().upper()
    book = book_service.get_book_by_code_or_id(clean_code)
    if not book:
        abort(404)

    payload = qr_service.get_book_qr_payload(book['book_code'])
    png_bytes = qr_service.generate_qr_png_bytes(payload, box_size=8, border=2)

    response = Response(png_bytes, mimetype='image/png')
    response.headers['Cache-Control'] = 'public, max-age=86400'
    return response

@student_bp.route('/about')
def about():
    """About Kitaab Bank."""
    return render_template(
        'student/placeholder.html',
        title="About Kitaab Bank (کتاب بینک)",
        icon="🏫",
        description="Kitaab Bank is a smart school textbook exchange platform designed to reduce educational expenses, promote the circular reuse of books, and foster a culture of reading."
    )
