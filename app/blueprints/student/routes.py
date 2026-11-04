from flask import render_template, request, abort, url_for
from . import student_bp
from app.services import book_service

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

@student_bp.route('/donate')
def donate():
    """Book donation view (Phase 3 foundation)."""
    return render_template(
        'student/placeholder.html',
        title="Donate a Textbook",
        icon="📖",
        description="The student book donation form with condition photo upload and teacher review queue will be implemented in Phase 3."
    )

@student_bp.route('/track')
def track():
    """Request tracker view (Phase 4 foundation)."""
    return render_template(
        'student/placeholder.html',
        title="Track Your Book Request",
        icon="🔍",
        description="The private request tracking desk using your unique Reference Code will be implemented in Phase 4."
    )

@student_bp.route('/scan')
def scan():
    """QR Code scanner view (Phase 6 foundation)."""
    return render_template(
        'student/placeholder.html',
        title="QR Code & Book Scanner",
        icon="📷",
        description="The offline camera scanner and direct 6-digit Book Code lookup will be implemented in Phase 6."
    )

@student_bp.route('/about')
def about():
    """About Kitaab Bank."""
    return render_template(
        'student/placeholder.html',
        title="About Kitaab Bank (کتاب بینک)",
        icon="🏫",
        description="Kitaab Bank is a smart school textbook exchange platform designed to reduce educational expenses, promote the circular reuse of books, and foster a culture of reading."
    )
