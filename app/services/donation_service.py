"""
Donation Service: Domain logic for student book donations, Pillow image processing,
and teacher approval/rejection workflows.
"""

import os
import re
import uuid
import secrets
import string
from pathlib import Path
from PIL import Image
from flask import current_app

from app.database import get_db, db_transaction

ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'webp'}
ALLOWED_IMAGE_FORMATS = {'JPEG', 'PNG', 'WEBP'}

def generate_secure_donation_code(db=None) -> str:
    """
    Generate an unpredictable, cryptographically secure donation reference code.
    Format: KB-DON-XXXX-XXXX (e.g. KB-DON-7K9M-2X4P).
    Enforces collision resistance via retry loop.
    """
    if db is None:
        db = get_db()
    cur = db.cursor()

    # Exclude ambiguous characters (O, 0, I, 1)
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"

    for _ in range(5):
        part1 = ''.join(secrets.choice(alphabet) for _ in range(4))
        part2 = ''.join(secrets.choice(alphabet) for _ in range(4))
        candidate = f"KB-DON-{part1}-{part2}"

        cur.execute("SELECT 1 FROM donations WHERE donation_code = ? LIMIT 1;", (candidate,))
        if not cur.fetchone():
            return candidate

    # Fallback to high-entropy hex if 5 attempts collided (astronomically unlikely)
    return f"KB-DON-{secrets.token_hex(4).upper()}-{secrets.token_hex(4).upper()}"

def save_and_process_donation_image(file_storage, upload_folder=None) -> str:
    """
    Validates, strips metadata, resizes, and saves an uploaded book photograph locally.
    Never relies solely on client-supplied filename or extension.
    Returns relative path (e.g. 'uploads/books/<uuid>.webp').
    Raises ValueError on validation failure.
    """
    if not file_storage or not file_storage.filename:
        return None

    filename = file_storage.filename.lower()
    ext = filename.rsplit('.', 1)[-1] if '.' in filename else ''
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError("Invalid file extension. Please upload a JPG, PNG, or WEBP image.")

    if upload_folder is None:
        upload_folder = current_app.config['UPLOAD_FOLDER']
    upload_folder = Path(upload_folder)
    upload_folder.mkdir(parents=True, exist_ok=True)

    # Validate actual binary image data via Pillow
    try:
        # Open image from stream
        file_storage.stream.seek(0)
        img = Image.open(file_storage.stream)

        # Verify underlying image format
        if img.format not in ALLOWED_IMAGE_FORMATS:
            raise ValueError(f"Unsupported image format ({img.format}). Only JPEG, PNG, and WEBP are supported.")

        # Convert to RGB (handles RGBA, Palette, CMYK, etc.)
        if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
            # Create a clean white background for transparent images
            bg = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            bg.paste(img, mask=img.split()[-1])
            img = bg
        elif img.mode != 'RGB':
            img = img.convert('RGB')

        # Resize if dimensions exceed 1000px on any side (maintains aspect ratio)
        max_dimension = 1000
        if img.width > max_dimension or img.height > max_dimension:
            img.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)

        # Generate secure random filename to prevent directory traversal
        safe_filename = f"{uuid.uuid4().hex}.webp"
        destination = upload_folder / safe_filename

        # Save freshly re-encoded WEBP (strips EXIF / polyglot payloads)
        img.save(str(destination), 'WEBP', quality=85, method=6)

        return f"uploads/books/{safe_filename}"

    except (IOError, SyntaxError) as e:
        raise ValueError("The uploaded file could not be decoded as a valid image.")
    except Exception as e:
        if isinstance(e, ValueError):
            raise
        raise ValueError(f"Image processing failed: {str(e)}")

def get_default_cover_for_book(subject: str, class_grade: str) -> str:
    """Map subject and class to an existing local SVG cover or default placeholder."""
    subj = (subject or '').lower()
    grade = (class_grade or '').lower()

    if 'math' in subj or 'ریاضی' in subj:
        if '6' in grade or 'ششم' in grade:
            return 'img/covers/math_class6.svg'
        elif '7' in grade or 'ہفتم' in grade:
            return 'img/covers/math_class7.svg'
        else:
            return 'img/covers/math_class8.svg'

    if 'science' in subj or 'سائنس' in subj:
        if '6' in grade or 'ششم' in grade:
            return 'img/covers/science_class6.svg'
        elif '7' in grade or 'ہفتم' in grade:
            return 'img/covers/science_class7.svg'
        else:
            return 'img/covers/science_class8.svg'

    if 'urdu' in subj or 'اردو' in subj:
        if '6' in grade or 'ششم' in grade:
            return 'img/covers/urdu_class6.svg'
        elif '7' in grade or 'ہفتم' in grade or 'ستون' in grade:
            return 'img/covers/urdu_class7.svg'
        else:
            return 'img/covers/urdu_class8.svg'

    if 'sindhi' in subj or 'سنڌي' in subj:
        if '6' in grade or 'ششم' in grade or 'ڇھون' in grade:
            return 'img/covers/sindhi_class6.svg'
        elif '7' in grade or 'ستون' in grade or 'ہفتم' in grade:
            return 'img/covers/sindhi_class7.svg'
        else:
            return 'img/covers/sindhi_class8.svg'

    if 'english' in subj or 'انگریزی' in subj or 'انگريزي' in subj:
        if '6' in grade or 'ششم' in grade or 'ڇھون' in grade:
            return 'img/covers/english_class6.svg'
        elif '8' in grade or 'ہشتم' in grade or 'اٺون' in grade:
            return 'img/covers/english_class8.svg'
        else:
            return 'img/covers/english_class7.svg'

    if 'computer' in subj or 'کمپیوٹر' in subj or 'ڪمپيوٽر' in subj:
        if '6' in grade or 'ششم' in grade or 'ڇھون' in grade:
            return 'img/covers/computer_class6.svg'
        elif '8' in grade or 'ہشتم' in grade or 'اٺون' in grade:
            return 'img/covers/computer_class8.svg'
        else:
            return 'img/covers/computer_class7.svg'

    if 'islamiat' in subj or 'اسلامیات' in subj or 'اسلاميات' in subj:
        if '7' in grade or 'ہفتم' in grade or 'ستون' in grade:
            return 'img/covers/islamiat_class7.svg'
        elif '8' in grade or 'ہشتم' in grade or 'اٺون' in grade:
            return 'img/covers/islamiat_class8.svg'
        else:
            return 'img/covers/islamiat_class6.svg'

    if 'social' in subj or 'معاشرتی' in subj or 'سماجي' in subj or 'مطالعہ' in subj:
        if '7' in grade or 'ہفتم' in grade or 'ستون' in grade:
            return 'img/covers/social_class7.svg'
        elif '8' in grade or 'ہشتم' in grade or 'اٺون' in grade:
            return 'img/covers/social_class8.svg'
        else:
            return 'img/covers/social_class6.svg'

    return 'img/covers/placeholder.svg'

def create_donation(form_data, file_storage=None):
    """
    Validate and save a student book donation.
    Returns (success: bool, donation_code: str, error: str).
    """
    # 1. Extract and sanitize fields
    title = (form_data.get('title') or '').strip()
    author = (form_data.get('author') or '').strip()
    class_grade = (form_data.get('class_grade') or '').strip()
    subject = (form_data.get('subject') or '').strip()
    language = (form_data.get('language') or 'Urdu').strip()
    condition_state = (form_data.get('condition_state') or 'Good').strip()
    description = (form_data.get('description') or '').strip()
    
    donor_name = (form_data.get('donor_name') or '').strip()
    donor_class = (form_data.get('donor_class') or '').strip()
    donor_roll_no = (form_data.get('donor_roll_no') or '').strip()
    donor_contact = (form_data.get('donor_contact') or '').strip()

    # 2. Validation
    if not title or len(title) < 2:
        return False, None, "Book title is required (at least 2 characters)."
    if len(title) > 200:
        return False, None, "Book title cannot exceed 200 characters."

    if not class_grade or class_grade not in ('Class 6', 'Class 7', 'Class 8'):
        return False, None, "Please select a valid Class Level (Class 6, Class 7, or Class 8)."

    if not subject:
        return False, None, "Subject is required."
    if len(subject) > 100:
        return False, None, "Subject cannot exceed 100 characters."

    if language not in ('English', 'Urdu', 'Sindhi'):
        return False, None, "Language must be English, Urdu, or Sindhi."

    if condition_state not in ('Like New', 'Good', 'Fair'):
        return False, None, "Condition must be 'Like New', 'Good', or 'Fair'."

    if not donor_name or len(donor_name) < 2:
        return False, None, "Donor name is required (at least 2 characters)."
    if len(donor_name) > 100:
        return False, None, "Donor name cannot exceed 100 characters."

    if not donor_class:
        return False, None, "Donor Class and Section is required (e.g. 8-A)."

    # 3. Optional Photo Upload Processing
    temp_image_path = None
    if file_storage and file_storage.filename:
        try:
            temp_image_path = save_and_process_donation_image(file_storage)
        except ValueError as ve:
            return False, None, str(ve)
        except Exception as e:
            return False, None, f"Image processing error: {str(e)}"

    # 4. Save to Database via write transaction
    db = get_db()
    donation_code = generate_secure_donation_code(db)

    try:
        with db_transaction(db):
            cur = db.cursor()
            cur.execute(
                """
                INSERT INTO donations (
                    donation_code, title, author, subject, class_grade, language,
                    condition_state, description, temp_image_path,
                    donor_name, donor_class, donor_roll_no, donor_contact,
                    status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending');
                """,
                (
                    donation_code, title, author or None, subject, class_grade, language,
                    condition_state, description or None, temp_image_path,
                    donor_name, donor_class, donor_roll_no or '', donor_contact or None
                )
            )
            donation_id = cur.lastrowid

            # Log submission in activity logs
            cur.execute(
                """
                INSERT INTO activity_logs (
                    action, entity_type, entity_id, actor_type, actor_name, details
                ) VALUES ('donation_submitted', 'donation', ?, 'student', ?, ?);
                """,
                (
                    donation_id,
                    donor_name,
                    f"Donation {donation_code} for '{title}' submitted by {donor_name} ({donor_class})"
                )
            )

        return True, donation_code, None
    except Exception as e:
        current_app.logger.error(f"Failed to record donation: {e}")
        return False, None, "A database error occurred while saving your donation. Please try again."

def get_donation_by_code(donation_code: str):
    """Retrieve full donation details by its unique reference code."""
    db = get_db()
    cur = db.cursor()
    code_clean = str(donation_code).strip().upper()
    cur.execute(
        """
        SELECT d.*, 
               t.full_name AS reviewer_name,
               b.book_code AS approved_book_code
        FROM donations d
        LEFT JOIN teachers t ON d.reviewed_by = t.id
        LEFT JOIN books b ON d.book_id = b.id
        WHERE d.donation_code = ?
        LIMIT 1;
        """,
        (code_clean,)
    )
    row = cur.fetchone()
    return dict(row) if row else None

def get_donation_by_id(donation_id: int):
    """Retrieve donation details by primary key."""
    db = get_db()
    cur = db.cursor()
    cur.execute(
        """
        SELECT d.*, 
               t.full_name AS reviewer_name,
               b.book_code AS approved_book_code
        FROM donations d
        LEFT JOIN teachers t ON d.reviewed_by = t.id
        LEFT JOIN books b ON d.book_id = b.id
        WHERE d.id = ?
        LIMIT 1;
        """,
        (donation_id,)
    )
    row = cur.fetchone()
    return dict(row) if row else None

def get_donations_for_teacher(status=None, search_query=None, class_grade=None, subject=None, limit=50, offset=0):
    """
    Retrieve donation records for teacher review with filtering, search, and pagination.
    Returns (donations_list, total_count).
    """
    db = get_db()
    cur = db.cursor()

    where_clauses = []
    params = []

    # Status filter
    if status and status.strip() in ('pending', 'approved', 'rejected'):
        where_clauses.append("d.status = ?")
        params.append(status.strip())

    # Class grade filter
    if class_grade and class_grade.strip():
        where_clauses.append("d.class_grade = ?")
        params.append(class_grade.strip())

    # Subject filter
    if subject and subject.strip():
        where_clauses.append("d.subject = ?")
        params.append(subject.strip())

    # Search query
    if search_query and search_query.strip():
        term = f"%{search_query.strip()}%"
        where_clauses.append(
            "(d.title LIKE ? OR d.author LIKE ? OR d.donor_name LIKE ? OR d.donor_roll_no LIKE ? OR d.donation_code LIKE ?)"
        )
        params.extend([term, term, term, term, term])

    where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

    # Count matching records
    count_sql = f"SELECT COUNT(*) FROM donations d {where_sql};"
    cur.execute(count_sql, params)
    total_count = cur.fetchone()[0]

    # Select records with pagination
    query_parts = [
        f"""
        SELECT d.*, 
               t.full_name AS reviewer_name,
               b.book_code AS approved_book_code
        FROM donations d
        LEFT JOIN teachers t ON d.reviewed_by = t.id
        LEFT JOIN books b ON d.book_id = b.id
        {where_sql}
        ORDER BY 
            CASE WHEN d.status = 'pending' THEN 0 ELSE 1 END,
            d.id DESC
        """
    ]
    query_params = list(params)

    if limit is not None:
        query_parts.append("LIMIT ?")
        query_params.append(int(limit))
        if offset is not None:
            query_parts.append("OFFSET ?")
            query_params.append(int(offset))

    full_query = " ".join(query_parts)
    cur.execute(full_query, query_params)
    rows = cur.fetchall()
    return [dict(r) for r in rows], total_count

def get_pending_donations_count() -> int:
    """Return count of unreviewed pending donations."""
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT COUNT(*) FROM donations WHERE status = 'pending';")
    return cur.fetchone()[0]

def approve_donation(donation_id: int, teacher_id: int, teacher_name: str = 'Teacher'):
    """
    Approve a pending donation:
    1. Validates status is still pending (prevents duplicate approval).
    2. Generates the next unique book code (KB-BK-000001).
    3. Creates public book record marked 'available' and linked to donation.
    4. Updates donation record with reviewer and timestamp.
    5. Logs action in activity log.
    All inside a single database transaction.
    Returns (success: bool, book_code: str, error: str).
    """
    db = get_db()
    
    try:
        with db_transaction(db):
            cur = db.cursor()

            # 1. Fetch and validate donation status
            cur.execute("SELECT * FROM donations WHERE id = ?;", (donation_id,))
            donation_row = cur.fetchone()
            if not donation_row:
                return False, None, "Donation record not found."

            donation = dict(donation_row)
            if donation['status'] != 'pending':
                return False, None, f"Cannot approve donation: Current status is '{donation['status']}'."

            # 2. Generate next sequential 6-digit Book Code (KB-BK-000001 format)
            cur.execute("SELECT book_code FROM books WHERE book_code LIKE 'KB-BK-%';")
            existing_codes = cur.fetchall()
            max_num = 0
            for r in existing_codes:
                code_str = r[0]
                match = re.search(r'KB-BK-(\d+)', code_str)
                if match:
                    try:
                        num = int(match.group(1))
                        if num > max_num:
                            max_num = num
                    except ValueError:
                        pass

            next_book_code = f"KB-BK-{max_num + 1:06d}"

            # 3. Determine image path (preserve donor photo or assign local SVG cover)
            image_path = donation.get('temp_image_path')
            if not image_path:
                image_path = get_default_cover_for_book(
                    donation['subject'],
                    donation['class_grade']
                )

            # 4. Insert into books table
            cur.execute(
                """
                INSERT INTO books (
                    book_code, title, author, subject, class_grade, language,
                    condition_state, description, image_path, status, is_approved,
                    donation_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'available', 1, ?);
                """,
                (
                    next_book_code,
                    donation['title'],
                    donation.get('author') or 'Unknown',
                    donation['subject'],
                    donation['class_grade'],
                    donation['language'],
                    donation['condition_state'],
                    donation.get('description') or '',
                    image_path,
                    donation['id']
                )
            )
            new_book_id = cur.lastrowid

            # 5. Update donation record
            cur.execute(
                """
                UPDATE donations
                SET status = 'approved',
                    book_id = ?,
                    reviewed_by = ?,
                    reviewed_at = CURRENT_TIMESTAMP
                WHERE id = ?;
                """,
                (new_book_id, teacher_id, donation['id'])
            )

            # 6. Log in activity logs
            cur.execute(
                """
                INSERT INTO activity_logs (
                    action, entity_type, entity_id, actor_type, actor_name, details
                ) VALUES ('donation_approved', 'donation', ?, 'teacher', ?, ?);
                """,
                (
                    donation['id'],
                    teacher_name,
                    f"Donation {donation['donation_code']} approved by {teacher_name}. Created book {next_book_code} ('{donation['title']}')."
                )
            )

        return True, next_book_code, None

    except Exception as e:
        current_app.logger.error(f"Error approving donation {donation_id}: {e}")
        return False, None, f"Database transaction failed: {str(e)}"

def reject_donation(donation_id: int, teacher_id: int, teacher_name: str = 'Teacher', reason: str = ''):
    """
    Reject a pending donation:
    1. Validates status is still pending.
    2. Records rejection reason.
    3. Retains history without creating a public book listing.
    Returns (success: bool, None, error: str).
    """
    reason_clean = (reason or '').strip()
    if not reason_clean:
        reason_clean = "Not specified"

    db = get_db()

    try:
        with db_transaction(db):
            cur = db.cursor()

            # 1. Fetch and validate donation status
            cur.execute("SELECT * FROM donations WHERE id = ?;", (donation_id,))
            donation_row = cur.fetchone()
            if not donation_row:
                return False, None, "Donation record not found."

            donation = dict(donation_row)
            if donation['status'] != 'pending':
                return False, None, f"Cannot reject donation: Current status is '{donation['status']}'."

            # 2. Update donation record
            cur.execute(
                """
                UPDATE donations
                SET status = 'rejected',
                    rejection_reason = ?,
                    reviewed_by = ?,
                    reviewed_at = CURRENT_TIMESTAMP
                WHERE id = ?;
                """,
                (reason_clean, teacher_id, donation['id'])
            )

            # 3. Log in activity logs
            cur.execute(
                """
                INSERT INTO activity_logs (
                    action, entity_type, entity_id, actor_type, actor_name, details
                ) VALUES ('donation_rejected', 'donation', ?, 'teacher', ?, ?);
                """,
                (
                    donation['id'],
                    teacher_name,
                    f"Donation {donation['donation_code']} ('{donation['title']}') rejected by {teacher_name}. Reason: {reason_clean}"
                )
            )

        return True, None, None

    except Exception as e:
        current_app.logger.error(f"Error rejecting donation {donation_id}: {e}")
        return False, None, f"Database transaction failed: {str(e)}"
