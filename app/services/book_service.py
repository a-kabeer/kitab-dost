"""
Book Service: Domain Logic for Book Discovery, Catalogue, Search & Filtering
"""

import re
import uuid
from pathlib import Path
from PIL import Image
from flask import current_app
from app.database import get_db, db_transaction
from app.services import activity_service

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

def get_books_for_labels(
    class_grade=None,
    subject=None,
    status=None,
    search_query=None,
    limit=None,
    offset=None
):
    """
    Retrieve books for QR sticker label generation.
    Supports filtering by class level, subject, status (available/reserved/handed_over/all),
    and keyword search.
    """
    db = get_db()
    cur = db.cursor()

    sql = ["SELECT * FROM books WHERE 1=1"]
    params = []

    if class_grade and class_grade.strip():
        sql.append("AND class_grade = ?")
        params.append(class_grade.strip())

    if subject and subject.strip():
        sql.append("AND subject = ?")
        params.append(subject.strip())

    if status and status.strip() and status != 'all':
        sql.append("AND status = ?")
        params.append(status.strip())

    if search_query and search_query.strip():
        term = f"%{search_query.strip()}%"
        sql.append("AND (title LIKE ? OR author LIKE ? OR book_code LIKE ?)")
        params.extend([term, term, term])

    sql.append("ORDER BY id ASC")

    if limit is not None:
        sql.append("LIMIT ?")
        params.append(int(limit))
    if offset is not None:
        sql.append("OFFSET ?")
        params.append(int(offset))

    cur.execute(" ".join(sql), params)
    rows = cur.fetchall()
    return [dict(r) for r in rows]

def generate_next_book_code():
    """Generate next sequential 6-digit Book Code (KB-BK-000001)."""
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT book_code FROM books WHERE book_code LIKE 'KB-BK-%';")
    codes = [r[0] for r in cur.fetchall()]
    max_num = 0
    for code in codes:
        match = re.search(r'KB-BK-(\d+)', str(code))
        if match:
            num = int(match.group(1))
            if num > max_num:
                max_num = num
    return f"KB-BK-{max_num + 1:06d}"

def get_inventory_counts():
    """Retrieve counts of books across all inventory statuses."""
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT COUNT(*) FROM books;")
    total = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM books WHERE status = 'available';")
    available = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM books WHERE status = 'reserved';")
    reserved = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM books WHERE status = 'handed_over';")
    handed_over = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM books WHERE status = 'retired';")
    retired = cur.fetchone()[0]

    return {
        'all': total,
        'available': available,
        'reserved': reserved,
        'handed_over': handed_over,
        'retired': retired
    }

def get_inventory_books(
    search_query=None,
    class_grade=None,
    subject=None,
    condition=None,
    status=None,
    sort_by='newest',
    limit=20,
    offset=0
):
    """
    Retrieve books for teacher inventory management with multi-faceted filtering.
    Returns (books_list, total_count).
    """
    db = get_db()
    cur = db.cursor()

    sql = ["SELECT * FROM books WHERE 1=1"]
    params = []

    if status and status.strip() and status != 'all':
        sql.append("AND status = ?")
        params.append(status.strip())

    if class_grade and class_grade.strip() and class_grade != 'all':
        sql.append("AND class_grade = ?")
        params.append(class_grade.strip())

    if subject and subject.strip() and subject != 'all':
        sql.append("AND subject = ?")
        params.append(subject.strip())

    if condition and condition.strip() and condition != 'all':
        sql.append("AND condition_state = ?")
        params.append(condition.strip())

    if search_query and search_query.strip():
        term = f"%{search_query.strip()}%"
        sql.append("AND (title LIKE ? OR author LIKE ? OR book_code LIKE ? OR publisher LIKE ? OR description LIKE ?)")
        params.extend([term, term, term, term, term])

    count_sql = "SELECT COUNT(*) " + " ".join(sql)[len("SELECT * "):]
    cur.execute(count_sql, params)
    total_count = cur.fetchone()[0]

    if sort_by == 'oldest':
        sql.append("ORDER BY id ASC")
    elif sort_by == 'code_asc':
        sql.append("ORDER BY book_code ASC")
    elif sort_by == 'title_asc':
        sql.append("ORDER BY title COLLATE NOCASE ASC")
    else:  # newest
        sql.append("ORDER BY id DESC")

    if limit is not None:
        sql.append("LIMIT ?")
        params.append(int(limit))
    if offset is not None:
        sql.append("OFFSET ?")
        params.append(int(offset))

    cur.execute(" ".join(sql), params)
    rows = cur.fetchall()
    return [dict(r) for r in rows], total_count

def save_book_cover_image(file_storage, upload_folder=None):
    """
    Validates, strips metadata, resizes, and saves an uploaded book cover.
    Returns relative path (e.g. 'uploads/books/<uuid>.webp').
    """
    if not file_storage or not getattr(file_storage, 'filename', None):
        return None

    filename = file_storage.filename.strip()
    if not filename:
        return None

    allowed_exts = {'.jpg', '.jpeg', '.png', '.webp'}
    ext = Path(filename).suffix.lower()
    if ext not in allowed_exts:
        raise ValueError("Invalid image extension. Only JPG, PNG, or WEBP allowed.")

    if upload_folder is None:
        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'app/static/uploads/books')
    upload_folder = Path(upload_folder)
    upload_folder.mkdir(parents=True, exist_ok=True)

    try:
        file_storage.stream.seek(0)
        img = Image.open(file_storage.stream)

        # Convert palette/transparency to RGB
        if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
            bg = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            bg.paste(img, mask=img.split()[3] if len(img.split()) == 4 else None)
            img = bg
        elif img.mode != 'RGB':
            img = img.convert('RGB')

        # Resize to max 800px preserving aspect ratio
        max_dim = 800
        if max(img.size) > max_dim:
            img.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)

        safe_filename = f"{uuid.uuid4().hex}.webp"
        destination = upload_folder / safe_filename
        img.save(destination, format='WEBP', quality=85, method=6)

        return f"uploads/books/{safe_filename}"
    except Exception as e:
        raise ValueError(f"Image processing failed: {str(e)}")

def add_inventory_book(data, image_file=None, teacher_id=None, teacher_name=None):
    """
    Add a new book directly to the inventory.
    Returns (success, book_id, book_code, error_msg).
    """
    title = (data.get('title') or '').strip()
    if not title:
        return False, None, None, "Book title is required."

    subject = (data.get('subject') or '').strip()
    if not subject:
        return False, None, None, "Subject is required."

    class_grade = (data.get('class_grade') or '').strip()
    if not class_grade:
        return False, None, None, "Class level is required."

    language = (data.get('language') or 'Urdu').strip()
    author = (data.get('author') or '').strip() or None
    publisher = (data.get('publisher') or '').strip() or None
    edition_year = data.get('edition_year')
    if edition_year:
        try:
            edition_year = int(edition_year)
        except ValueError:
            edition_year = None
    else:
        edition_year = None

    condition_state = (data.get('condition_state') or 'Good').strip()
    description = (data.get('description') or '').strip() or None

    image_path = None
    if image_file and getattr(image_file, 'filename', None):
        try:
            image_path = save_book_cover_image(image_file)
        except Exception as e:
            return False, None, None, str(e)

    if not image_path:
        image_path = "img/covers/placeholder.svg"

    db = get_db()
    try:
        with db_transaction(db):
            cur = db.cursor()
            book_code = generate_next_book_code()

            cur.execute(
                """
                INSERT INTO books (
                    book_code, title, author, subject, class_grade, language,
                    publisher, edition_year, condition_state, description,
                    image_path, status, is_approved
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'available', 1);
                """,
                (
                    book_code, title, author, subject, class_grade, language,
                    publisher, edition_year, condition_state, description,
                    image_path
                )
            )
            book_id = cur.lastrowid

            # Log audit activity
            activity_service.record_activity(
                action='book_added',
                entity_type='book',
                entity_id=book_id,
                actor_type='teacher',
                actor_name=teacher_name or 'Teacher',
                details=f"Book '{title}' ({book_code}) added to inventory by {teacher_name or 'Teacher'}."
            )

            return True, book_id, book_code, None
    except Exception as e:
        return False, None, None, f"Database error adding book: {str(e)}"

def update_inventory_book(book_id, data, image_file=None, teacher_id=None, teacher_name=None):
    """
    Update details of an existing book in inventory.
    Returns (success, error_msg).
    """
    book = get_book_by_code_or_id(book_id)
    if not book:
        return False, "Book not found."

    title = (data.get('title') or '').strip()
    if not title:
        return False, "Book title cannot be empty."

    subject = (data.get('subject') or '').strip()
    if not subject:
        return False, "Subject is required."

    class_grade = (data.get('class_grade') or '').strip()
    if not class_grade:
        return False, "Class level is required."

    language = (data.get('language') or book.get('language', 'Urdu')).strip()
    author = (data.get('author') or '').strip() or None
    publisher = (data.get('publisher') or '').strip() or None
    edition_year = data.get('edition_year')
    if edition_year:
        try:
            edition_year = int(edition_year)
        except ValueError:
            edition_year = None
    else:
        edition_year = None

    condition_state = (data.get('condition_state') or book.get('condition_state', 'Good')).strip()
    description = (data.get('description') or '').strip() or None

    image_path = book.get('image_path')
    if image_file and getattr(image_file, 'filename', None):
        try:
            new_image = save_book_cover_image(image_file)
            if new_image:
                image_path = new_image
        except Exception as e:
            return False, str(e)

    db = get_db()
    try:
        with db_transaction(db):
            cur = db.cursor()
            cur.execute(
                """
                UPDATE books SET
                    title = ?, author = ?, subject = ?, class_grade = ?,
                    language = ?, publisher = ?, edition_year = ?,
                    condition_state = ?, description = ?, image_path = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?;
                """,
                (
                    title, author, subject, class_grade,
                    language, publisher, edition_year,
                    condition_state, description, image_path,
                    book['id']
                )
            )

            # Log audit activity
            activity_service.record_activity(
                action='book_updated',
                entity_type='book',
                entity_id=book['id'],
                actor_type='teacher',
                actor_name=teacher_name or 'Teacher',
                details=f"Book '{title}' ({book['book_code']}) updated by {teacher_name or 'Teacher'}."
            )

            return True, None
    except Exception as e:
        return False, f"Database error updating book: {str(e)}"

def retire_or_restore_book(book_id, new_status, reason=None, teacher_id=None, teacher_name=None):
    """
    Retire an existing book or restore it to circulation.
    Enforces integrity guards:
    - Cannot retire a 'reserved' book (must cancel reservation first).
    - Cannot modify a 'handed_over' book.
    Returns (success, error_msg).
    """
    book = get_book_by_code_or_id(book_id)
    if not book:
        return False, "Book not found."

    current_status = book['status']
    if current_status == 'reserved':
        return False, "Cannot change status of a reserved book. Please cancel the pending reservation first."
    if current_status == 'handed_over':
        return False, "Cannot modify a book that has already been handed over to a student."

    if new_status not in ('retired', 'available'):
        return False, f"Invalid target status '{new_status}'."

    action_name = 'book_retired' if new_status == 'retired' else 'book_restored'
    details_reason = f" Reason: {reason}" if reason else ""

    db = get_db()
    try:
        with db_transaction(db):
            cur = db.cursor()
            cur.execute(
                "UPDATE books SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?;",
                (new_status, book['id'])
            )

            activity_service.record_activity(
                action=action_name,
                entity_type='book',
                entity_id=book['id'],
                actor_type='teacher',
                actor_name=teacher_name or 'Teacher',
                details=f"Book '{book['title']}' ({book['book_code']}) status changed from '{current_status}' to '{new_status}' by {teacher_name or 'Teacher'}.{details_reason}"
            )

            return True, None
    except Exception as e:
        return False, f"Database error updating status: {str(e)}"


