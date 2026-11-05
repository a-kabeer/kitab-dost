"""
Handover Service: Domain Logic for Physical Book Distribution & Ledger
Handles:
- Sequential unique handover code generation (KB-HO-000001)
- Identity verification & physical distribution confirmation
- Atomic transaction processing (BEGIN IMMEDIATE)
- Book status transition to 'handed_over' and request status to 'completed'
- Reservation cancellation & catalogue restoration before physical handover
- Handover Ledger search, filtering, and inspection
"""

import re
from flask import current_app
from app.database import get_db, db_transaction

def generate_next_handover_code(db) -> str:
    """
    Generate the next sequential 6-digit Handover Code (KB-HO-000001 format).
    Collision-resistant and gap-tolerant.
    """
    cur = db.cursor()
    cur.execute("SELECT handover_code FROM handovers WHERE handover_code LIKE 'KB-HO-%';")
    existing_codes = cur.fetchall()
    max_num = 0
    for r in existing_codes:
        code_str = r[0]
        match = re.search(r'KB-HO-(\d+)', code_str)
        if match:
            try:
                num = int(match.group(1))
                if num > max_num:
                    max_num = num
            except ValueError:
                pass

    return f"KB-HO-{max_num + 1:06d}"

def confirm_physical_handover(
    request_id: int,
    teacher_id: int,
    teacher_name: str = 'Teacher',
    id_verified: bool = False,
    book_handed_over: bool = False,
    remarks: str = ''
):
    """
    Execute atomic physical book handover to requesting student:
    1. Validates teacher identity and physical distribution confirmation checkboxes.
    2. Validates request status is 'approved' (cannot handover pending/rejected/cancelled/completed).
    3. Validates associated book status is 'reserved' (cannot handover available/handed_over books).
    4. Validates no handover record already exists for this request or book.
    5. Generates next unique sequential handover code (KB-HO-000001).
    6. Creates immutable handover record in handovers table.
    7. Atomically transitions request.status = 'completed'.
    8. Atomically transitions book.status = 'handed_over'.
    9. Logs audit record in activity_logs.
    All inside a single database transaction with BEGIN IMMEDIATE write lock.
    Returns (success: bool, handover_code: str, error_msg: str).
    """
    if not id_verified:
        return False, None, "You must confirm that the student's identity was checked against school records."

    if not book_handed_over:
        return False, None, "You must confirm that the physical textbook was handed over to the student."

    db = get_db()

    try:
        with db_transaction(db):
            cur = db.cursor()

            # 1. Fetch request record
            cur.execute("SELECT * FROM requests WHERE id = ?;", (request_id,))
            req_row = cur.fetchone()
            if not req_row:
                return False, None, "Request record not found."

            req = dict(req_row)
            if req['status'] == 'completed':
                return False, None, "Cannot complete handover: This request has already been handed over."
            elif req['status'] == 'pending':
                return False, None, "Cannot complete handover: Request is still pending teacher approval."
            elif req['status'] == 'rejected':
                return False, None, "Cannot complete handover: Request has been rejected."
            elif req['status'] == 'cancelled':
                return False, None, "Cannot complete handover: Request reservation has been cancelled."
            elif req['status'] != 'approved':
                return False, None, f"Cannot complete handover: Current request status is '{req['status']}' (must be 'approved')."

            # 2. Fetch associated book
            cur.execute("SELECT * FROM books WHERE id = ?;", (req['book_id'],))
            book_row = cur.fetchone()
            if not book_row:
                return False, None, "Associated book record not found."

            book = dict(book_row)
            if book['status'] == 'handed_over':
                return False, None, f"Cannot complete handover: Book '{book['book_code']}' is already handed over."
            elif book['status'] != 'reserved':
                return False, None, f"Cannot complete handover: Book '{book['book_code']}' status is '{book['status']}' (must be 'reserved')."

            # 3. Check for existing handover on this request
            cur.execute("SELECT id, handover_code FROM handovers WHERE request_id = ?;", (req['id'],))
            existing_handover = cur.fetchone()
            if existing_handover:
                return False, None, f"A handover has already been recorded for this request ({existing_handover['handover_code']})."

            # 4. Generate unique handover reference (KB-HO-000001)
            handover_code = generate_next_handover_code(db)

            # 5. Insert immutable handover ledger record
            cur.execute(
                """
                INSERT INTO handovers (
                    handover_code, request_id, tracking_code, book_id, book_code,
                    recipient_name, recipient_class, recipient_roll_no, recipient_contact,
                    handed_over_by, teacher_name, remarks, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'completed');
                """,
                (
                    handover_code,
                    req['id'],
                    req['tracking_code'],
                    book['id'],
                    book['book_code'],
                    req['requester_name'],
                    req['requester_class'],
                    req['requester_roll_no'],
                    req.get('requester_contact') or '',
                    teacher_id,
                    teacher_name,
                    remarks.strip() if remarks else None
                )
            )
            handover_id = cur.lastrowid

            # 6. Update request status to 'completed'
            cur.execute(
                "UPDATE requests SET status = 'completed' WHERE id = ?;",
                (req['id'],)
            )

            # 7. Update book status to 'handed_over'
            cur.execute(
                "UPDATE books SET status = 'handed_over', updated_at = CURRENT_TIMESTAMP WHERE id = ?;",
                (book['id'],)
            )

            # 8. Record audit log
            cur.execute(
                """
                INSERT INTO activity_logs (
                    action, entity_type, entity_id, actor_type, actor_name, details
                ) VALUES ('book_handed_over', 'handover', ?, 'teacher', ?, ?);
                """,
                (
                    handover_id,
                    teacher_name,
                    f"Physical handover {handover_code} confirmed by {teacher_name}. Book '{book['title']}' ({book['book_code']}) handed over to {req['requester_name']} ({req['requester_class']}, Roll {req['requester_roll_no']})."
                )
            )

        return True, handover_code, None

    except Exception as e:
        current_app.logger.error(f"Error confirming handover for request {request_id}: {e}")
        return False, None, f"Database transaction failed: {str(e)}"

def cancel_approved_reservation(
    request_id: int,
    teacher_id: int,
    teacher_name: str = 'Teacher',
    reason: str = ''
):
    """
    Cancel an approved reservation before physical distribution:
    1. Validates reason is non-empty.
    2. Validates request status is 'approved' (never allow cancelling completed handovers).
    3. Validates book status is currently 'reserved'.
    4. Restores book.status = 'available' (re-published to catalogue).
    5. Updates request.status = 'cancelled' with recorded reason and teacher ID.
    6. Logs audit trail in activity_logs.
    All inside a single database transaction with BEGIN IMMEDIATE write lock.
    Returns (success: bool, book_code: str, error_msg: str).
    """
    clean_reason = (reason or '').strip()
    if not clean_reason:
        return False, None, "A valid reason is required to cancel an approved reservation."

    db = get_db()

    try:
        with db_transaction(db):
            cur = db.cursor()

            # 1. Fetch request record
            cur.execute("SELECT * FROM requests WHERE id = ?;", (request_id,))
            req_row = cur.fetchone()
            if not req_row:
                return False, None, "Request record not found."

            req = dict(req_row)
            if req['status'] == 'completed':
                return False, None, "Cannot cancel reservation: The book has already been physically handed over."
            elif req['status'] != 'approved':
                return False, None, f"Cannot cancel reservation: Current status is '{req['status']}' (must be 'approved')."

            # 2. Check no completed handover exists
            cur.execute("SELECT id FROM handovers WHERE request_id = ?;", (req['id'],))
            if cur.fetchone():
                return False, None, "Cannot cancel reservation: A completed handover record exists."

            # 3. Fetch associated book
            cur.execute("SELECT * FROM books WHERE id = ?;", (req['book_id'],))
            book_row = cur.fetchone()
            if not book_row:
                return False, None, "Associated book record not found."

            book = dict(book_row)
            if book['status'] != 'reserved':
                return False, None, f"Cannot cancel reservation: Book status is '{book['status']}', expected 'reserved'."

            # 4. Restore book to available in catalogue
            cur.execute(
                "UPDATE books SET status = 'available', updated_at = CURRENT_TIMESTAMP WHERE id = ?;",
                (book['id'],)
            )

            # 5. Transition request to cancelled
            cur.execute(
                """
                UPDATE requests 
                SET status = 'cancelled',
                    rejection_reason = ?,
                    reviewed_by = ?,
                    reviewed_at = CURRENT_TIMESTAMP
                WHERE id = ?;
                """,
                (clean_reason, teacher_id, req['id'])
            )

            # 6. Log audit activity
            cur.execute(
                """
                INSERT INTO activity_logs (
                    action, entity_type, entity_id, actor_type, actor_name, details
                ) VALUES ('reservation_cancelled', 'request', ?, 'teacher', ?, ?);
                """,
                (
                    req['id'],
                    teacher_name,
                    f"Reservation for book '{book['book_code']}' cancelled by {teacher_name}. Reason: {clean_reason}. Book restored to catalogue as available."
                )
            )

        return True, book['book_code'], None

    except Exception as e:
        current_app.logger.error(f"Error cancelling reservation for request {request_id}: {e}")
        return False, None, f"Database transaction failed: {str(e)}"

def get_handovers_for_teacher(
    search_query: str = None,
    class_grade: str = None,
    date_from: str = None,
    date_to: str = None,
    limit: int = 25,
    offset: int = 0
):
    """
    Query completed handover records with multi-faceted search and filters for Teacher Ledger.
    Returns (handovers_list, total_count).
    """
    db = get_db()
    cur = db.cursor()

    where_clauses = []
    params = []

    # Search Query (Handover code, tracking code, book code, title, student name, roll number)
    if search_query and search_query.strip():
        term = f"%{search_query.strip()}%"
        where_clauses.append(
            "(h.handover_code LIKE ? OR h.tracking_code LIKE ? OR h.book_code LIKE ? OR b.title LIKE ? OR h.recipient_name LIKE ? OR h.recipient_roll_no LIKE ?)"
        )
        params.extend([term, term, term, term, term, term])

    # Class filter
    if class_grade and class_grade.strip():
        where_clauses.append("(h.recipient_class LIKE ? OR b.class_grade = ?)")
        params.extend([f"%{class_grade.strip()}%", class_grade.strip()])

    # Date range filters
    if date_from and date_from.strip():
        where_clauses.append("DATE(h.handover_date) >= DATE(?)")
        params.append(date_from.strip())

    if date_to and date_to.strip():
        where_clauses.append("DATE(h.handover_date) <= DATE(?)")
        params.append(date_to.strip())

    where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

    # Count total matching records
    count_sql = f"""
        SELECT COUNT(*) 
        FROM handovers h
        JOIN books b ON h.book_id = b.id
        {where_sql};
    """
    cur.execute(count_sql, params)
    total_count = cur.fetchone()[0]

    # Select full handover details
    select_sql = f"""
        SELECT h.*,
               b.title AS book_title,
               b.author AS book_author,
               b.subject AS book_subject,
               b.class_grade AS book_class,
               b.condition_state AS book_condition,
               b.image_path AS book_image,
               t.full_name AS confirming_teacher_name
        FROM handovers h
        JOIN books b ON h.book_id = b.id
        LEFT JOIN teachers t ON h.handed_over_by = t.id
        {where_sql}
        ORDER BY h.id DESC
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

def get_handover_by_id(handover_id: int):
    """Retrieve full details of a specific handover by primary key."""
    db = get_db()
    cur = db.cursor()
    cur.execute(
        """
        SELECT h.*,
               b.title AS book_title,
               b.author AS book_author,
               b.subject AS book_subject,
               b.class_grade AS book_class,
               b.condition_state AS book_condition,
               b.image_path AS book_image,
               t.full_name AS confirming_teacher_name,
               r.notes AS request_notes
        FROM handovers h
        JOIN books b ON h.book_id = b.id
        LEFT JOIN teachers t ON h.handed_over_by = t.id
        LEFT JOIN requests r ON h.request_id = r.id
        WHERE h.id = ?
        LIMIT 1;
        """,
        (handover_id,)
    )
    row = cur.fetchone()
    return dict(row) if row else None

def get_handover_by_code(handover_code: str):
    """Retrieve handover record by unique code (e.g. KB-HO-000001)."""
    db = get_db()
    cur = db.cursor()
    cur.execute(
        """
        SELECT h.*,
               b.title AS book_title,
               b.author AS book_author,
               b.subject AS book_subject,
               b.class_grade AS book_class,
               b.condition_state AS book_condition,
               b.image_path AS book_image,
               t.full_name AS confirming_teacher_name
        FROM handovers h
        JOIN books b ON h.book_id = b.id
        LEFT JOIN teachers t ON h.handed_over_by = t.id
        WHERE h.handover_code = ?
        LIMIT 1;
        """,
        (handover_code.strip().upper(),)
    )
    row = cur.fetchone()
    return dict(row) if row else None

def get_handover_by_request_id(request_id: int):
    """Retrieve handover record by original request ID."""
    db = get_db()
    cur = db.cursor()
    cur.execute(
        """
        SELECT h.*,
               b.title AS book_title,
               b.author AS book_author,
               b.subject AS book_subject,
               b.class_grade AS book_class,
               t.full_name AS confirming_teacher_name
        FROM handovers h
        JOIN books b ON h.book_id = b.id
        LEFT JOIN teachers t ON h.handed_over_by = t.id
        WHERE h.request_id = ?
        LIMIT 1;
        """,
        (request_id,)
    )
    row = cur.fetchone()
    return dict(row) if row else None

def get_handover_metrics():
    """Retrieve dashboard aggregate statistics for Handover Ledger."""
    db = get_db()
    cur = db.cursor()

    cur.execute("SELECT COUNT(*) FROM handovers;")
    total_handovers = cur.fetchone()[0]

    cur.execute("SELECT COUNT(DISTINCT recipient_roll_no) FROM handovers;")
    unique_recipients = cur.fetchone()[0]

    cur.execute("SELECT COUNT(DISTINCT book_id) FROM handovers;")
    reused_books = cur.fetchone()[0]

    return {
        'total_handovers': total_handovers,
        'unique_recipients': unique_recipients,
        'reused_books': reused_books
    }
