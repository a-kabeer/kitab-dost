"""
Book Service: Domain Logic for Book Discovery, Catalogue, Search & Filtering
"""

from app.database import get_db

def get_available_books(
    search_query=None,
    class_grade=None,
    subject=None,
    language=None,
    condition=None,
    sort_by='title_asc',
    limit=None,
    offset=None
):
    """
    Query teacher-approved available books with multi-faceted filtering and search.
    Returns (books_list, total_count).
    """
    db = get_db()
    cur = db.cursor()

    sql = ["SELECT * FROM books WHERE is_approved = 1 AND status = 'available'"]
    params = []

    # 1. Search Query (Title, Author, Subject, Code, Publisher, Description)
    if search_query and search_query.strip():
        term = f"%{search_query.strip()}%"
        sql.append(
            "AND (title LIKE ? OR author LIKE ? OR subject LIKE ? OR book_code LIKE ? OR publisher LIKE ? OR description LIKE ?)"
        )
        params.extend([term, term, term, term, term, term])

    # 2. Class Filter (Class 6, Class 7, Class 8)
    if class_grade and class_grade.strip():
        sql.append("AND class_grade = ?")
        params.append(class_grade.strip())

    # 3. Subject Filter
    if subject and subject.strip():
        sql.append("AND subject = ?")
        params.append(subject.strip())

    # 4. Language Filter (English, Urdu, Sindhi)
    if language and language.strip():
        sql.append("AND language = ?")
        params.append(language.strip())

    # 5. Condition Filter (Like New, Good, Fair)
    if condition and condition.strip():
        sql.append("AND condition_state = ?")
        params.append(condition.strip())

    # Count total matching query before pagination
    count_sql = "SELECT COUNT(*) " + " ".join(sql)[len("SELECT * "):]
    cur.execute(count_sql, params)
    total_count = cur.fetchone()[0]

    # 6. Sorting Order
    if sort_by == 'newest':
        sql.append("ORDER BY id DESC")
    elif sort_by == 'class_asc':
        sql.append("ORDER BY class_grade ASC, title ASC")
    else:  # Default title_asc
        sql.append("ORDER BY title COLLATE NOCASE ASC")

    # 7. Pagination
    if limit is not None:
        sql.append("LIMIT ?")
        params.append(int(limit))
        if offset is not None:
            sql.append("OFFSET ?")
            params.append(int(offset))

    full_query = " ".join(sql)
    cur.execute(full_query, params)
    rows = cur.fetchall()
    return [dict(r) for r in rows], total_count

def get_book_by_code_or_id(identifier):
    """Fetch an approved book by its 6-digit code (KB-BK-000001) or primary key id."""
    db = get_db()
    cur = db.cursor()

    ident_str = str(identifier).strip().upper()
    cur.execute(
        "SELECT * FROM books WHERE book_code = ? OR id = ? LIMIT 1;",
        (ident_str, identifier if str(identifier).isdigit() else -1)
    )
    row = cur.fetchone()
    return dict(row) if row else None

def get_filter_options():
    """Retrieve distinct available values for filter dropdowns."""
    db = get_db()
    cur = db.cursor()

    # Classes
    cur.execute(
        "SELECT DISTINCT class_grade FROM books WHERE is_approved = 1 AND status = 'available' ORDER BY class_grade ASC;"
    )
    classes = [r[0] for r in cur.fetchall() if r[0]]

    # Subjects
    cur.execute(
        "SELECT DISTINCT subject FROM books WHERE is_approved = 1 AND status = 'available' ORDER BY subject ASC;"
    )
    subjects = [r[0] for r in cur.fetchall() if r[0]]

    # Languages
    cur.execute(
        "SELECT DISTINCT language FROM books WHERE is_approved = 1 AND status = 'available' ORDER BY language ASC;"
    )
    languages = [r[0] for r in cur.fetchall() if r[0]]

    # Conditions
    cur.execute(
        "SELECT DISTINCT condition_state FROM books WHERE is_approved = 1 AND status = 'available' ORDER BY condition_state ASC;"
    )
    conditions = [r[0] for r in cur.fetchall() if r[0]]

    return {
        'classes': classes,
        'subjects': subjects,
        'languages': languages,
        'conditions': conditions
    }

def get_recent_and_featured_books(limit=6):
    """Retrieve recently added approved books for the homepage showcase."""
    db = get_db()
    cur = db.cursor()
    cur.execute(
        "SELECT * FROM books WHERE is_approved = 1 AND status = 'available' ORDER BY id DESC LIMIT ?;",
        (limit,)
    )
    return [dict(r) for r in cur.fetchall()]

def get_live_catalogue_stats():
    """Calculate actual metrics from the SQLite database."""
    db = get_db()
    cur = db.cursor()

    cur.execute("SELECT COUNT(*) FROM donations WHERE status = 'approved';")
    total_donated = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM books WHERE status = 'available' AND is_approved = 1;")
    available_books = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM handovers;")
    total_reused = cur.fetchone()[0]

    cur.execute("SELECT COUNT(DISTINCT recipient_roll_no) FROM handovers;")
    active_students = cur.fetchone()[0]

    return {
        'total_donated': total_donated,
        'available_books': available_books,
        'total_reused': total_reused,
        'active_students': active_students
    }
