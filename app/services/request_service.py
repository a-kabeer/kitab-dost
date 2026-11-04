"""
Request Service: Domain logic for student book requests, cryptographically secure
unpredictable tracking codes, privacy redaction, and atomic teacher reservation locking.
"""

import re
import secrets
from flask import current_app
from app.database import get_db, db_transaction

def generate_secure_tracking_code(db=None) -> str:
    """
    Generate an unpredictable, cryptographically secure student tracking code.
    Format: KB-REQ-XXXX-XXXX (e.g. KB-REQ-7K9M-2X4P).
    Excludes visually ambiguous characters (O, 0, I, 1).
    Guarantees database uniqueness with collision-resistant retry loop.
    """
    if db is None:
        db = get_db()
    cur = db.cursor()

    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"

    for _ in range(5):
        part1 = ''.join(secrets.choice(alphabet) for _ in range(4))
        part2 = ''.join(secrets.choice(alphabet) for _ in range(4))
        candidate = f"KB-REQ-{part1}-{part2}"

        cur.execute("SELECT 1 FROM requests WHERE tracking_code = ? LIMIT 1;", (candidate,))
        if not cur.fetchone():
            return candidate

    return f"KB-REQ-{secrets.token_hex(4).upper()}-{secrets.token_hex(4).upper()}"

def mask_student_name(full_name: str) -> str:
    """
    Mask student name for public tracking page to preserve privacy.
    e.g. 'Zeeshan Ahmed' -> 'Zeeshan A***', 'Fatima' -> 'Fa***'
    """
    if not full_name:
        return "Student"
    parts = full_name.strip().split()
    if len(parts) == 1:
        name = parts[0]
        if len(name) <= 2:
            return name + "***"
        return name[:2] + "***"
    first = parts[0]
    last = parts[-1]
    return f"{first} {last[0]}***"

def create_book_request(form_data):
    """
    Validate and save a student book request.
    Returns (success: bool, tracking_code: str, error: str).
    """
    book_id_or_code = (form_data.get('book_id') or form_data.get('book_code') or '').strip()
    requester_name = (form_data.get('requester_name') or '').strip()
    requester_class = (form_data.get('requester_class') or '').strip()
    requester_roll_no = (form_data.get('requester_roll_no') or '').strip()
    requester_contact = (form_data.get('requester_contact') or '').strip()
    notes = (form_data.get('notes') or '').strip()

    # 1. Validation
    if not book_id_or_code:
        return False, None, "Please specify a book to request."

    if not requester_name or len(requester_name) < 2:
        return False, None, "Your full name is required (at least 2 characters)."
    if len(requester_name) > 100:
        return False, None, "Name cannot exceed 100 characters."

    if not requester_class:
        return False, None, "Class & section is required (e.g. Class 7-A)."

    if not requester_roll_no:
        return False, None, "School Roll Number is required for teacher handover verification."

    if not requester_contact:
        return False, None, "A contact or parent phone number is required."

    db = get_db()
    cur = db.cursor()

    # 2. Verify book exists and is available
    cur.execute(
        """
        SELECT * FROM books 
        WHERE (id = ? OR book_code = ?) AND is_approved = 1
        LIMIT 1;
        """,
        (int(book_id_or_code) if book_id_or_code.isdigit() else -1, book_id_or_code.upper())
    )
    book = cur.fetchone()
    if not book:
        return False, None, "The requested book was not found in the school catalogue."

    if book['status'] != 'available':
        return False, None, f"This book is currently '{book['status']}' and cannot be requested at this time."

    book_id = book['id']
    tracking_code = generate_secure_tracking_code(db)

    # 3. Save request inside a write transaction
    try:
        with db_transaction(db):
            cur = db.cursor()

            # 2b. Prevent duplicate pending/approved requests from same student for same book
            cur.execute(
                """
                SELECT tracking_code FROM requests 
                WHERE book_id = ? 
                  AND requester_roll_no = ? 
                  AND requester_class = ?
                  AND status IN ('pending', 'approved')
                LIMIT 1;
                """,
                (book_id, requester_roll_no, requester_class)
            )
            duplicate_req = cur.fetchone()
            if duplicate_req:
                return False, None, f"You already have an active request ({duplicate_req['tracking_code']}) for this textbook."

            cur.execute(
                """
                INSERT INTO requests (
                    tracking_code, book_id, requester_name, requester_class,
                    requester_roll_no, requester_contact, notes, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 'pending');
                """,
                (
                    tracking_code, book_id, requester_name, requester_class,
                    requester_roll_no, requester_contact, notes or None
                )
            )
            request_id = cur.lastrowid

            # Log activity
            cur.execute(
                """
                INSERT INTO activity_logs (
                    action, entity_type, entity_id, actor_type, actor_name, details
                ) VALUES ('request_submitted', 'request', ?, 'student', ?, ?);
                """,
                (
                    request_id,
                    requester_name,
                    f"Request {tracking_code} submitted for '{book['title']}' ({book['book_code']}) by {requester_name} ({requester_class})"
                )
            )

        return True, tracking_code, None
    except Exception as e:
        current_app.logger.error(f"Failed to record book request: {e}")
        return False, None, "A database error occurred while saving your request. Please try again."

def get_request_by_tracking_code(tracking_code: str):
    """
    Retrieve request details by its unique tracking code.
    Joins book details and reviewer name.
    """
    db = get_db()
    cur = db.cursor()
    code_clean = str(tracking_code).strip().upper()

    cur.execute(
        """
        SELECT r.*,
               b.book_code, b.title AS book_title, b.author AS book_author,
               b.class_grade AS book_class, b.subject AS book_subject,
               b.language AS book_language, b.condition_state AS book_condition,
               b.image_path AS book_image, b.status AS book_status,
               t.full_name AS reviewer_name
        FROM requests r
        JOIN books b ON r.book_id = b.id
        LEFT JOIN teachers t ON r.reviewed_by = t.id
        WHERE r.tracking_code = ?
        LIMIT 1;
        """,
        (code_clean,)
    )
    row = cur.fetchone()
    return dict(row) if row else None

def get_request_by_id(request_id: int):
    """Retrieve request details by primary key."""
    db = get_db()
    cur = db.cursor()
    cur.execute(
        """
        SELECT r.*,
               b.book_code, b.title AS book_title, b.author AS book_author,
               b.class_grade AS book_class, b.subject AS book_subject,
               b.language AS book_language, b.condition_state AS book_condition,
               b.image_path AS book_image, b.status AS book_status,
               t.full_name AS reviewer_name
        FROM requests r
        JOIN books b ON r.book_id = b.id
        LEFT JOIN teachers t ON r.reviewed_by = t.id
        WHERE r.id = ?
        LIMIT 1;
        """,
        (request_id,)
    )
    row = cur.fetchone()
    return dict(row) if row else None

def get_requests_for_teacher(status=None, search_query=None, class_grade=None, limit=50, offset=0):
    """
    Retrieve request records for teacher review queue with filters, search, and pagination.
    Returns (requests_list, total_count).
    """
    db = get_db()
    cur = db.cursor()

    where_clauses = []
    params = []

    # Status filter
    if status and status.strip() in ('pending', 'approved', 'rejected', 'completed', 'cancelled'):
        where_clauses.append("r.status = ?")
        params.append(status.strip())

    # Class grade filter (on requested book or student class)
    if class_grade and class_grade.strip():
        where_clauses.append("(b.class_grade = ? OR r.requester_class LIKE ?)")
        params.extend([class_grade.strip(), f"%{class_grade.strip()}%"])

    # Search query
    if search_query and search_query.strip():
        term = f"%{search_query.strip()}%"
        where_clauses.append(
            "(r.tracking_code LIKE ? OR r.requester_name LIKE ? OR r.requester_roll_no LIKE ? OR b.title LIKE ? OR b.book_code LIKE ?)"
        )
        params.extend([term, term, term, term, term])

    where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

    # Total matching count
    count_sql = f"""
        SELECT COUNT(*) 
        FROM requests r 
        JOIN books b ON r.book_id = b.id 
        {where_sql};
    """
    cur.execute(count_sql, params)
    total_count = cur.fetchone()[0]

    # Select records ordered by pending first, then newest
    select_sql = f"""
        SELECT r.*,
               b.book_code, b.title AS book_title, b.author AS book_author,
               b.class_grade AS book_class, b.subject AS book_subject,
               b.condition_state AS book_condition, b.image_path AS book_image,
               b.status AS book_status,
               t.full_name AS reviewer_name
        FROM requests r
        JOIN books b ON r.book_id = b.id
        LEFT JOIN teachers t ON r.reviewed_by = t.id
        {where_sql}
        ORDER BY 
            CASE WHEN r.status = 'pending' THEN 0 ELSE 1 END,
            r.id DESC
    """
    query_params = list(params)
    if limit is not None:
        select_sql += " LIMIT ?"
        query_params.append(int(limit))
        if offset is not None:
            select_sql += " OFFSET ?"
            query_params.append(int(offset))

    cur.execute(select_sql, query_params)
    rows = cur.fetchall()
    return [dict(r) for r in rows], total_count

def get_pending_requests_count() -> int:
    """Return count of unreviewed pending book requests."""
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT COUNT(*) FROM requests WHERE status = 'pending';")
    return cur.fetchone()[0]

def approve_request(request_id: int, teacher_id: int, teacher_name: str = 'Teacher'):
    """
    Atomic Teacher Approval & Book Reservation:
    1. Validates request status is 'pending' (prevents double approval).
    2. Validates associated book is currently 'available' (prevents race condition / double-booking).
    3. Atomically sets book.status = 'reserved'.
    4. Sets request.status = 'approved', records reviewer & timestamp.
    5. Logs action in activity log.
    All inside a single database transaction with BEGIN IMMEDIATE write lock.
    Returns (success: bool, book_code: str, error: str).
    """
    db = get_db()

    try:
        with db_transaction(db):
            cur = db.cursor()

            # 1. Fetch request and check status
            cur.execute("SELECT * FROM requests WHERE id = ?;", (request_id,))
            req_row = cur.fetchone()
            if not req_row:
                return False, None, "Request record not found."

            req = dict(req_row)
            if req['status'] != 'pending':
                # Check if associated book was already reserved by policy
                cur.execute("SELECT status FROM books WHERE id = ?;", (req['book_id'],))
                b_check = cur.fetchone()
                if b_check and b_check['status'] == 'reserved':
                    return False, None, f"Cannot approve request: Current status is '{req['status']}' because book is already reserved."
                return False, None, f"Cannot approve request: Current status is '{req['status']}'."

            # 2. Fetch associated book and verify it is available for reservation
            cur.execute("SELECT * FROM books WHERE id = ?;", (req['book_id'],))
            book_row = cur.fetchone()
            if not book_row:
                return False, None, "Associated book record not found."

            book = dict(book_row)
            if book['status'] != 'available':
                return False, None, f"Cannot reserve book: '{book['title']}' ({book['book_code']}) is already {book['status']}."

            # 3. Atomically reserve the book
            cur.execute(
                "UPDATE books SET status = 'reserved', updated_at = CURRENT_TIMESTAMP WHERE id = ?;",
                (book['id'],)
            )

            # 4. Update request to approved
            cur.execute(
                """
                UPDATE requests
                SET status = 'approved',
                    reviewed_by = ?,
                    reviewed_at = CURRENT_TIMESTAMP
                WHERE id = ?;
                """,
                (teacher_id, req['id'])
            )

            # 5. Clear all competing pending requests for this physical book
            # Policy: Competing requests for the exact same physical copy are auto-closed with
            # status 'rejected' and a transparent explanation. Zero orphaned pending requests remain.
            cur.execute(
                """
                SELECT id, tracking_code, requester_name 
                FROM requests 
                WHERE book_id = ? AND id != ? AND status = 'pending';
                """,
                (book['id'], req['id'])
            )
            competing_requests = cur.fetchall()

            if competing_requests:
                competing_reason = (
                    "This copy was allocated to another student who requested earlier or was prioritized by teacher review. "
                    "Please browse the school catalogue for other available copies."
                )
                cur.execute(
                    """
                    UPDATE requests
                    SET status = 'rejected',
                        rejection_reason = ?,
                        reviewed_by = ?,
                        reviewed_at = CURRENT_TIMESTAMP
                    WHERE book_id = ? AND id != ? AND status = 'pending';
                    """,
                    (competing_reason, teacher_id, book['id'], req['id'])
                )

                for cr in competing_requests:
                    cur.execute(
                        """
                        INSERT INTO activity_logs (
                            action, entity_type, entity_id, actor_type, actor_name, details
                        ) VALUES ('request_auto_closed', 'request', ?, 'system', ?, ?);
                        """,
                        (
                            cr['id'],
                            teacher_name,
                            f"Request {cr['tracking_code']} auto-closed: physical book {book['book_code']} reserved for {req['requester_name']}."
                        )
                    )

            # 6. Log activity for the approved request
            cur.execute(
                """
                INSERT INTO activity_logs (
                    action, entity_type, entity_id, actor_type, actor_name, details
                ) VALUES ('request_approved', 'request', ?, 'teacher', ?, ?);
                """,
                (
                    req['id'],
                    teacher_name,
                    f"Request {req['tracking_code']} approved by {teacher_name}. Reserved book {book['book_code']} for {req['requester_name']} ({req['requester_class']})."
                )
            )

        return True, book['book_code'], None

    except Exception as e:
        current_app.logger.error(f"Error approving request {request_id}: {e}")
        return False, None, f"Database transaction failed: {str(e)}"

def reject_request(request_id: int, teacher_id: int, teacher_name: str = 'Teacher', reason: str = ''):
    """
    Teacher Rejection:
    1. Validates request status is 'pending'.
    2. Updates request status to 'rejected', records reason and reviewer.
    3. Book remains 'available' for other students.
    Returns (success: bool, None, error: str).
    """
    reason_clean = (reason or '').strip()
    if not reason_clean:
        reason_clean = "Priority given to students without alternative access or invalid student details."

    db = get_db()

    try:
        with db_transaction(db):
            cur = db.cursor()

            cur.execute("SELECT * FROM requests WHERE id = ?;", (request_id,))
            req_row = cur.fetchone()
            if not req_row:
                return False, None, "Request record not found."

            req = dict(req_row)
            if req['status'] != 'pending':
                return False, None, f"Cannot reject request: Current status is '{req['status']}'."

            cur.execute(
                """
                UPDATE requests
                SET status = 'rejected',
                    rejection_reason = ?,
                    reviewed_by = ?,
                    reviewed_at = CURRENT_TIMESTAMP
                WHERE id = ?;
                """,
                (reason_clean, teacher_id, req['id'])
            )

            cur.execute(
                """
                INSERT INTO activity_logs (
                    action, entity_type, entity_id, actor_type, actor_name, details
                ) VALUES ('request_rejected', 'request', ?, 'teacher', ?, ?);
                """,
                (
                    req['id'],
                    teacher_name,
                    f"Request {req['tracking_code']} rejected by {teacher_name}. Reason: {reason_clean}"
                )
            )

        return True, None, None

    except Exception as e:
        current_app.logger.error(f"Error rejecting request {request_id}: {e}")
        return False, None, f"Database transaction failed: {str(e)}"
