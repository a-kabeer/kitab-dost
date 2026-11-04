from flask import render_template
from . import student_bp
from app.database import get_db

@student_bp.route('/')
def index():
    """Homepage for students with real-time statistics from local SQLite database."""
    db = get_db()
    
    # Real metrics queried directly from database records
    cur = db.cursor()
    cur.execute("SELECT COUNT(*) FROM donations WHERE status = 'approved'")
    total_donated = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM books WHERE status = 'available' AND is_approved = 1")
    available_books = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM handovers")
    total_reused = cur.fetchone()[0]

    cur.execute("SELECT COUNT(DISTINCT recipient_roll_no) FROM handovers")
    active_students = cur.fetchone()[0]

    stats = {
        'total_donated': total_donated,
        'available_books': available_books,
        'total_reused': total_reused,
        'active_students': active_students
    }
    return render_template('student/index.html', stats=stats)

@student_bp.route('/catalogue')
def catalogue():
    """Book catalogue view (Phase 2 foundation)."""
    return render_template(
        'student/placeholder.html',
        title="Public Book Catalogue",
        icon="📚",
        description="The full book discovery catalogue with class (6–8) and subject filters will be implemented in Phase 2."
    )

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
