"""
Kitaab Bank - Fast Exhibition Demo Seeder & Reset Tool
Resets database and populates clean, realistic exhibition data in < 1 second.
Includes:
- 18 Textbooks across Classes 6, 7, 8 in Urdu, English, Sindhi
- Full circulation distribution (Available, Reserved, Handed Over)
- Realistic student donations in all states (Pending, Approved, Rejected)
- Realistic student requests in all states (Pending, Approved/Reserved, Completed)
- Completed handover transactions with printable receipts
- Activity logs spanning past 30 days
"""

import sys
import os
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash
from flask import current_app

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _initial_teacher_password():
    """Read the configured bootstrap password in-app, or environment for CLI use."""
    try:
        return current_app.config.get('INITIAL_TEACHER_PASSWORD', 'Teacher@123')
    except RuntimeError:
        return os.environ.get('INITIAL_TEACHER_PASSWORD', 'Teacher@123')
DB_PATH = PROJECT_ROOT / 'kitaab_bank.db'

def reset_and_seed_demo_data(target_db=None, create_safety_backup=True, target_backup_dir=None):
    """Clean reset and seed for exhibition showcase with automatic safety backup."""
    db_file = target_db or DB_PATH
    db_path_obj = Path(db_file)

    # 0. Data Safety: Capture automated pre-demo safety backup
    if create_safety_backup and db_path_obj.exists():
        try:
            if target_backup_dir:
                bck_dir = Path(target_backup_dir)
            elif target_db and Path(target_db).resolve() != DB_PATH.resolve():
                bck_dir = Path(target_db).parent / 'backups'
            else:
                try:
                    from flask import current_app
                    if current_app and current_app.config.get('BACKUP_FOLDER'):
                        bck_dir = Path(current_app.config['BACKUP_FOLDER'])
                    else:
                        bck_dir = PROJECT_ROOT / 'backups'
                except Exception:
                    bck_dir = PROJECT_ROOT / 'backups'

            bck_dir.mkdir(parents=True, exist_ok=True)

            live_c = sqlite3.connect(str(db_file), timeout=10.0)
            live_cur = live_c.cursor()

            # Prevent repeated demo activation from replacing the original recovery point with demo data
            live_cur.execute("SELECT value FROM system_settings WHERE key = 'is_demo_mode';")
            demo_row = live_cur.fetchone()
            is_already_demo = (demo_row and demo_row[0] == '1')

            if not is_already_demo:
                # Truncate WAL to ensure clean snapshot
                try:
                    live_cur.execute("PRAGMA wal_checkpoint(TRUNCATE);")
                except Exception:
                    pass

                now_dt = datetime.now()
                base_name = f"kitab_bank_backup_{now_dt.strftime('%Y%m%d_%H%M%S')}_pre_demo"
                pre_demo_filename = f"{base_name}.db"
                pre_demo_path = bck_dir / pre_demo_filename
                counter = 1
                while pre_demo_path.exists():
                    pre_demo_filename = f"{base_name}_{counter}.db"
                    pre_demo_path = bck_dir / pre_demo_filename
                    counter += 1

                # Capture full live database backup (even if books table is empty)
                safety_c = sqlite3.connect(str(pre_demo_path))
                live_c.backup(safety_c)
                safety_c.close()

                # Verify captured backup integrity
                chk_c = sqlite3.connect(str(pre_demo_path))
                chk_cur = chk_c.cursor()
                chk_cur.execute("PRAGMA integrity_check;")
                res = chk_cur.fetchone()
                chk_c.close()
                if not res or res[0] != 'ok':
                    raise RuntimeError(f"Pre-demo backup integrity verification failed: {res}")

                # Calculate SHA-256 and catalog
                import hashlib
                hasher = hashlib.sha256()
                with open(pre_demo_path, 'rb') as f:
                    while chunk := f.read(65536):
                        hasher.update(chunk)
                checksum = hasher.hexdigest()
                size_bytes = pre_demo_path.stat().st_size

                live_cur.execute(
                    """
                    INSERT INTO backup_records (filename, file_size_bytes, checksum_sha256, verification_status)
                    VALUES (?, ?, ?, 'VALID');
                    """,
                    (pre_demo_filename, size_bytes, checksum)
                )
                pre_demo_backup_id = live_cur.lastrowid

                # Store exact pre-demo backup ID in system_settings
                live_cur.execute(
                    """
                    INSERT INTO system_settings (key, value, updated_at)
                    VALUES ('demo_pre_backup_id', ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = CURRENT_TIMESTAMP;
                    """,
                    (str(pre_demo_backup_id),)
                )
                live_c.commit()
            live_c.close()
        except Exception:
            pass

    conn = sqlite3.connect(str(db_file), timeout=30.0)
    conn.execute("PRAGMA busy_timeout = 10000;")
    conn.execute("PRAGMA synchronous = NORMAL;")
    cur = conn.cursor()

    # Ensure schema exists before clearing tables
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='books';")
    if not cur.fetchone():
        schema_path = PROJECT_ROOT / 'app' / 'schema.sql'
        if schema_path.exists():
            with open(schema_path, 'r', encoding='utf-8') as f:
                cur.executescript(f.read())

    # Begin batch transaction for sub-second execution
    conn.execute("BEGIN TRANSACTION;")

    # 1. Clear dynamic tables in foreign key order (preserve backup_records!)
    cur.execute("PRAGMA foreign_keys = OFF;")
    cur.execute("DELETE FROM handovers;")
    cur.execute("DELETE FROM requests;")
    cur.execute("DELETE FROM donations;")
    cur.execute("DELETE FROM books;")
    cur.execute("DELETE FROM activity_logs;")
    try:
        cur.execute("DELETE FROM sqlite_sequence WHERE name IN ('books', 'donations', 'requests', 'handovers', 'activity_logs');")
    except Exception:
        pass
    # NOTE: backup_records is strictly preserved to protect historical backups!
    cur.execute("PRAGMA foreign_keys = ON;")

    # 2. Ensure Default Teacher Account
    cur.execute("SELECT id FROM teachers WHERE username = 'teacher';")
    teacher_row = cur.fetchone()
    if not teacher_row:
        cur.execute(
            """
            INSERT INTO teachers (username, password_hash, full_name, email, role, is_active)
            VALUES ('teacher', ?, 'Sir Tariq Mahmood', 'tariq.mahmood@school.edu.pk', 'admin', 1);
            """,
            (generate_password_hash(_initial_teacher_password()),)
        )
        teacher_id = cur.lastrowid
    else:
        teacher_id = teacher_row[0]

    # 3. Seed Realistic Textbooks (18 Books across Classes 6, 7, 8)
    books_data = [
        # Class 6
        ('KB-BK-000001', 'Mathematics for Class 6', 'Prof. Dr. M. A. Memon, S. K. Baloch', 'Mathematics', 'Class 6', 'English', 'Sindh Textbook Board, Jamshoro', 2025, 'Good', 'Covers Sets, Integers, Fractions, and Basic Geometry.', 'img/covers/math_class6.svg', 'available', 1),
        ('KB-BK-000002', 'General Science for Grade 6', 'Dr. Tariq Mahmood & Panel', 'General Science', 'Class 6', 'English', 'Sindhi Textbook Board', 2024, 'Like New', 'Cellular organization, plant systems, atoms and molecules.', 'img/covers/science_class6.svg', 'available', 1),
        ('KB-BK-000003', 'اردو لازمی برائے جماعت ششم', 'سید شبیر علی کاظمی', 'Urdu', 'Class 6', 'Urdu', 'قومی درسی کتب کونسل', 2025, 'Good', 'حمد، نعت، اسباق سیرت طیبہ، کہانیاں اور گرائمر۔', 'img/covers/urdu_class6.svg', 'available', 1),
        ('KB-BK-000004', 'سنڌي سليس درجو ڇھون', 'استاد محمد عثمان', 'Sindhi', 'Class 6', 'Sindhi', 'سنڌ ٽيڪسٽ بڪ بورڊ', 2024, 'Fair', 'شاعري، مضمون ۽ بنيادي سنڌي وياڪرڻ۔', 'img/covers/sindhi_class6.svg', 'available', 1),
        ('KB-BK-000005', 'اسلامیات لازمی برائے جماعت ششم', 'مولانا عبدالحمید طارق', 'Islamiat', 'Class 6', 'Urdu', 'پنجاب کریکولم اینڈ ٹیکسٹ بک بورڈ', 2025, 'Like New', 'قرآن مجید، ایمانیات و عبادات، سیرت النبی ﷺ۔', 'img/covers/islamiat_class6.svg', 'available', 1),
        ('KB-BK-000006', 'Social Studies & Geography 6', 'Dr. Farooq Ahmed, M. Saleem', 'Social Studies', 'Class 6', 'English', 'PTB & STBB Joint Publication', 2024, 'Good', 'Geography of South Asia, Indus Valley Civilization.', 'img/covers/social_class6.svg', 'reserved', 1),

        # Class 7
        ('KB-BK-000007', 'Mathematics for Class 7', 'Prof. K. B. Soomro', 'Mathematics', 'Class 7', 'English', 'Sindhi Textbook Board', 2025, 'Like New', 'Direct and Inverse Proportion, Algebraic Expressions.', 'img/covers/math_class7.svg', 'available', 1),
        ('KB-BK-000008', 'General Science for Grade 7', 'Dr. A. R. Kazi', 'General Science', 'Class 7', 'English', 'Sindhi Textbook Board', 2024, 'Good', 'Human organ systems, transport in plants, forces and motion.', 'img/covers/science_class7.svg', 'available', 1),
        ('KB-BK-000009', 'English Grammar & Composition 7', 'A. J. Thomson', 'English', 'Class 7', 'English', 'National Education Press', 2024, 'Good', 'Tenses, active/passive voice, direct/indirect speech.', 'img/covers/english_class7.svg', 'available', 1),
        ('KB-BK-000010', 'سنڌي درسي ڪتاب درجو ستون', 'غلام محمد گرامي', 'Sindhi', 'Class 7', 'Sindhi', 'سنڌ ٽيڪسٽ بڪ بورڊ', 2025, 'Good', 'شاهه لطيف جا بيت، لوڪ ادب، سنڌي ساهت.', 'img/covers/sindhi_class7.svg', 'available', 1),
        ('KB-BK-000011', 'Computer Science for Class 7', 'Engr. Farooq Aziz', 'Computer Science', 'Class 7', 'English', 'Sindhi Textbook Board', 2025, 'Like New', 'Computer hardware, Python basics, scratch programming.', 'img/covers/computer_class7.svg', 'reserved', 1),
        ('KB-BK-000012', 'اردو زبان و ادب جماعت ہفتم', 'محمود شام', 'Urdu', 'Class 7', 'Urdu', 'پنجاب ٹیکسٹ بک بورڈ', 2024, 'Fair', 'شاعری، نثر نگاری، خطوط نویسی اور ذخیرہ الفاظ۔', 'img/covers/urdu_class7.svg', 'handed_over', 1),

        # Class 8
        ('KB-BK-000013', 'Mathematics for Class 8', 'Prof. Dr. M. A. Memon', 'Mathematics', 'Class 8', 'English', 'Sindhi Textbook Board', 2025, 'Good', 'Number Systems, Financial Arithmetic, Polynomials, Linear Equations.', 'img/covers/math_class8.svg', 'available', 1),
        ('KB-BK-000014', 'General Science for Grade 8', 'Dr. Tariq Mahmood', 'General Science', 'Class 8', 'English', 'Sindhi Textbook Board', 2024, 'Like New', 'Nervous system, cell division, chemical reactions, acid/bases.', 'img/covers/science_class8.svg', 'available', 1),
        ('KB-BK-000015', 'اردو لازمی برائے جماعت ہشتم', 'سید وقار عظیم', 'Urdu', 'Class 8', 'Urdu', 'قومی نصاب و درسی کتب کونسل', 2025, 'Like New', 'قومی و ملی نظمیں، علامہ اقبال کی شاعری، تاریخ اسلام۔', 'img/covers/urdu_class8.svg', 'available', 1),
        ('KB-BK-000016', 'سنڌي لازمی درجو اٺون', 'استاد حيدر بخش جتوئي', 'Sindhi', 'Class 8', 'Sindhi', 'سنڌ ٽيڪسٽ بڪ بورڊ', 2024, 'Good', 'ڪلاسيڪل شاعري، سچل سرمست جو ڪلام، مضمون نگاري.', 'img/covers/sindhi_class8.svg', 'available', 1),
        ('KB-BK-000017', 'Computer Science for Class 8', 'Engr. Farooq Aziz', 'Computer Science', 'Class 8', 'English', 'Sindhi Textbook Board', 2025, 'Good', 'Networks, cybersecurity, algorithmic problem solving.', 'img/covers/computer_class8.svg', 'reserved', 1),
        ('KB-BK-000018', 'Social Studies for Class 8', 'Prof. Nisar Ahmed', 'Social Studies', 'Class 8', 'English', 'Sindhi Textbook Board', 2024, 'Good', 'History of the Subcontinent, Pakistan Movement.', 'img/covers/social_class8.svg', 'handed_over', 1)
    ]

    for b in books_data:
        cur.execute(
            """
            INSERT INTO books (
                book_code, title, author, subject, class_grade, language,
                publisher, edition_year, condition_state, description,
                image_path, status, is_approved
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            b
        )

    # 3b. Fetch real mapped IDs for books to ensure complete relational integrity
    cur.execute("SELECT book_code, id FROM books;")
    b_map = dict(cur.fetchall())

    # 4. Seed Realistic Student Donations
    now = datetime.now()
    donations_data = [
        ('KB-DON-7K9M-2X4P', 'Advanced Mathematics Class 8', 'STBB', 'Mathematics', 'Class 8', 'English', 'Good', 'Clean copy with slight margin notes.', 'Zainab Fatima', 'Class 8-A', '8012', '0300-1122334', 'approved', b_map['KB-BK-000013'], (now - timedelta(days=12)).strftime('%Y-%m-%d %H:%M:%S')),
        ('KB-DON-3M9X-7P4Q', 'Science Explorer Grade 7', 'Oxford Press', 'General Science', 'Class 7', 'English', 'Like New', 'Hardly used textbook from last term.', 'Hamza Ali', 'Class 7-B', '7025', '0321-9988776', 'pending', None, (now - timedelta(hours=4)).strftime('%Y-%m-%d %H:%M:%S')),
        ('KB-DON-8L2W-5V1N', 'Commercial Geography 8', 'Old Curriculum', 'Social Studies', 'Class 8', 'English', 'Fair', 'Outdated 2018 edition.', 'Bilal Ahmed', 'Class 8-C', '8045', '0345-5544332', 'rejected', None, (now - timedelta(days=5)).strftime('%Y-%m-%d %H:%M:%S'))
    ]

    don_ids = []
    for d in donations_data:
        cur.execute(
            """
            INSERT INTO donations (
                donation_code, title, author, subject, class_grade, language,
                condition_state, description, donor_name, donor_class,
                donor_roll_no, donor_contact, status, book_id, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            d
        )
        don_ids.append(cur.lastrowid)

    # 5. Seed Student Requests & Handovers
    # Request 1: Pending for Available Book (Mathematics Class 6)
    cur.execute(
        """
        INSERT INTO requests (
            tracking_code, book_id, requester_name, requester_class,
            requester_roll_no, requester_contact, notes, status, created_at
        ) VALUES ('KB-REQ-4T7M-9P2Q', ?, 'Ayesha Siddiqua', 'Class 6-A', '6014', '0312-3344556', 'Need for upcoming term math homework.', 'pending', ?);
        """,
        (b_map['KB-BK-000001'], (now - timedelta(hours=2)).strftime('%Y-%m-%d %H:%M:%S'))
    )
    req1_id = cur.lastrowid

    # Request 2: Approved / Reserved for Book 6 (Social Studies Class 6)
    cur.execute(
        """
        INSERT INTO requests (
            tracking_code, book_id, requester_name, requester_class,
            requester_roll_no, requester_contact, notes, status, reviewed_by, reviewed_at, created_at
        ) VALUES ('KB-REQ-8L1N-3K5V', ?, 'Saad Rehman', 'Class 6-B', '6028', '0333-7788990', 'Reserved for pickup on Thursday.', 'approved', ?, ?, ?);
        """,
        (b_map['KB-BK-000006'], teacher_id, now.strftime('%Y-%m-%d %H:%M:%S'), (now - timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S'))
    )
    req2_id = cur.lastrowid

    # Request 3: Approved / Reserved for Book 11 (Computer Science Class 7)
    cur.execute(
        """
        INSERT INTO requests (
            tracking_code, book_id, requester_name, requester_class,
            requester_roll_no, requester_contact, notes, status, reviewed_by, reviewed_at, created_at
        ) VALUES ('KB-REQ-2W9X-4M7L', ?, 'Maryam Noor', 'Class 7-A', '7009', '0301-4455667', 'Programming syllabus textbook needed.', 'approved', ?, ?, ?);
        """,
        (b_map['KB-BK-000011'], teacher_id, now.strftime('%Y-%m-%d %H:%M:%S'), (now - timedelta(days=2)).strftime('%Y-%m-%d %H:%M:%S'))
    )
    req3_id = cur.lastrowid

    # Request 4 & Handover 1: Book 12 (Urdu Class 7) -> Handed Over
    cur.execute(
        """
        INSERT INTO requests (
            tracking_code, book_id, requester_name, requester_class,
            requester_roll_no, requester_contact, status, reviewed_by, reviewed_at, created_at
        ) VALUES ('KB-REQ-9K3P-5T8M', ?, 'Farhan Ahmed', 'Class 6-C', '6035', '0322-1144778', 'completed', ?, ?, ?);
        """,
        (b_map['KB-BK-000012'], teacher_id, (now - timedelta(days=10)).strftime('%Y-%m-%d %H:%M:%S'), (now - timedelta(days=11)).strftime('%Y-%m-%d %H:%M:%S'))
    )
    req4_id = cur.lastrowid

    cur.execute(
        """
        INSERT INTO handovers (
            handover_code, request_id, book_id, tracking_code, book_code,
            recipient_name, recipient_class, recipient_roll_no, recipient_contact,
            handed_over_by, teacher_name, remarks, handover_date
        ) VALUES ('KB-HO-000001', ?, ?, 'KB-REQ-9K3P-5T8M', 'KB-BK-000012',
                  'Farhan Ahmed', 'Class 6-C', '6035', '0322-1144778',
                  ?, 'Sir Tariq Mahmood', 'Verified student card. Textbook handed over in like new condition.', ?);
        """,
        (req4_id, b_map['KB-BK-000012'], teacher_id, (now - timedelta(days=9)).strftime('%Y-%m-%d %H:%M:%S'))
    )
    ho1_id = cur.lastrowid

    # Request 5 & Handover 2: Book 18 (Social Studies Class 8) -> Handed Over
    cur.execute(
        """
        INSERT INTO requests (
            tracking_code, book_id, requester_name, requester_class,
            requester_roll_no, requester_contact, status, reviewed_by, reviewed_at, created_at
        ) VALUES ('KB-REQ-7M2L-4P9K', ?, 'Zain Ul Abideen', 'Class 7-C', '7042', '0344-9988112', 'completed', ?, ?, ?);
        """,
        (b_map['KB-BK-000018'], teacher_id, (now - timedelta(days=18)).strftime('%Y-%m-%d %H:%M:%S'), (now - timedelta(days=19)).strftime('%Y-%m-%d %H:%M:%S'))
    )
    req5_id = cur.lastrowid

    cur.execute(
        """
        INSERT INTO handovers (
            handover_code, request_id, book_id, tracking_code, book_code,
            recipient_name, recipient_class, recipient_roll_no, recipient_contact,
            handed_over_by, teacher_name, remarks, handover_date
        ) VALUES ('KB-HO-000002', ?, ?, 'KB-REQ-7M2L-4P9K', 'KB-BK-000018',
                  'Zain Ul Abideen', 'Class 7-C', '7042', '0344-9988112',
                  ?, 'Sir Tariq Mahmood', 'Student collected textbook before mid-term exams.', ?);
        """,
        (req5_id, b_map['KB-BK-000018'], teacher_id, (now - timedelta(days=17)).strftime('%Y-%m-%d %H:%M:%S'))
    )
    ho2_id = cur.lastrowid

    # 6. Seed Realistic Historical Activity Logs
    activity_items = [
        ('handover_completed', 'handover', ho2_id, 'teacher', 'Sir Tariq Mahmood', "Handover 'KB-HO-000002' confirmed: 'سوشل اسٽڊيز برائے جماعت ہشتم' issued to Zain Ul Abideen (Class 7-C)", (now - timedelta(days=17)).strftime('%Y-%m-%d %H:%M:%S')),
        ('donation_approved', 'donation', don_ids[0], 'teacher', 'Sir Tariq Mahmood', f"Donation 'KB-DON-7K9M-2X4P' approved into catalogue as 'KB-BK-000013'", (now - timedelta(days=12)).strftime('%Y-%m-%d %H:%M:%S')),
        ('handover_completed', 'handover', ho1_id, 'teacher', 'Sir Tariq Mahmood', "Handover 'KB-HO-000001' confirmed: 'اردو زبان و ادب جماعت ہفتم' issued to Farhan Ahmed (Class 6-C)", (now - timedelta(days=9)).strftime('%Y-%m-%d %H:%M:%S')),
        ('book_added', 'book', b_map['KB-BK-000007'], 'teacher', 'Sir Tariq Mahmood', "New textbook 'Mathematics for Class 7' (KB-BK-000007) added to inventory", (now - timedelta(days=7)).strftime('%Y-%m-%d %H:%M:%S')),
        ('request_approved', 'request', req2_id, 'teacher', 'Sir Tariq Mahmood', "Request 'KB-REQ-8L1N-3K5V' approved: Book 'KB-BK-000006' reserved for Saad Rehman", (now - timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')),
        ('donation_submitted', 'donation', don_ids[1], 'student', 'Hamza Ali', "Donation 'KB-DON-3M9X-7P4Q' submitted by Hamza Ali (Class 7-B)", (now - timedelta(hours=4)).strftime('%Y-%m-%d %H:%M:%S')),
        ('request_submitted', 'request', req1_id, 'student', 'Ayesha Siddiqua', "Book request 'KB-REQ-4T7M-9P2Q' submitted for 'Mathematics for Class 6'", (now - timedelta(hours=2)).strftime('%Y-%m-%d %H:%M:%S')),
        ('teacher_login', 'teacher', teacher_id, 'teacher', 'Sir Tariq Mahmood', "Teacher 'teacher' signed in from local workstation", now.strftime('%Y-%m-%d %H:%M:%S'))
    ]

    for act in activity_items:
        cur.execute(
            """
            INSERT INTO activity_logs (
                action, entity_type, entity_id, actor_type, actor_name, details, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?);
            """,
            act
        )

    # 7. Mark is_demo_mode = '1' in system_settings
    cur.execute(
        """
        INSERT INTO system_settings (key, value, updated_at) VALUES ('is_demo_mode', '1', CURRENT_TIMESTAMP)
        ON CONFLICT(key) DO UPDATE SET value = '1', updated_at = CURRENT_TIMESTAMP;
        """
    )

    conn.commit()
    conn.close()
    return True

if __name__ == '__main__':
    print("=" * 65)
    print("KITAAB BANK - FAST EXHIBITION DEMO SEEDER")
    print("=" * 65)
    start = datetime.now()
    reset_and_seed_demo_data()
    duration_ms = (datetime.now() - start).total_seconds() * 1000
    print(f"✓ Exhibition Demo Database Seeded Successfully in {duration_ms:.1f}ms!")
    print("  - 18 Textbooks (Available: 13, Reserved: 3, Handed Over: 2)")
    print("  - 3 Student Donations (Pending: 1, Approved: 1, Rejected: 1)")
    print("  - 5 Student Requests (Pending: 1, Approved/Reserved: 2, Completed: 2)")
    print("  - 2 Permanent Handovers (KB-HO-000001, KB-HO-000002)")
    print("  - 8 Activity Logs over past 30 days")
    print("  - Default Teacher Account: teacher / Teacher@123")
    print("=" * 65)
