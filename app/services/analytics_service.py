"""
Analytics Service: Live Statistical Engine & Reporting Desk
Calculates real metrics from SQLite without fabricated numbers.
Generates CSV exports for school administrative records.
"""

import io
import csv
from app.database import get_db

def get_dashboard_analytics():
    """
    Compute live administrative metrics and distributions for the Teacher Dashboard.
    """
    db = get_db()
    cur = db.cursor()

    # 1. Core Summary Metrics
    cur.execute("SELECT COUNT(*) FROM books;")
    total_inventory = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM books WHERE status = 'available' AND is_approved = 1;")
    available_books = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM books WHERE status = 'reserved';")
    reserved_books = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM books WHERE status = 'handed_over';")
    handed_over_books = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM books WHERE status = 'retired';")
    retired_books = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM donations;")
    total_donations = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM donations WHERE status = 'pending';")
    pending_donations = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM requests WHERE status = 'pending';")
    pending_requests = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM requests WHERE status = 'approved';")
    approved_requests = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM handovers;")
    completed_handovers = cur.fetchone()[0]

    cur.execute("SELECT COUNT(DISTINCT recipient_roll_no) FROM handovers WHERE recipient_roll_no IS NOT NULL AND recipient_roll_no != '';")
    unique_recipients = cur.fetchone()[0]

    pending_actions = pending_donations + pending_requests

    # 2. Class Distribution (Grades 6, 7, 8)
    cur.execute("""
        SELECT class_grade,
               COUNT(*) as total,
               SUM(CASE WHEN status = 'available' THEN 1 ELSE 0 END) as available,
               SUM(CASE WHEN status = 'reserved' THEN 1 ELSE 0 END) as reserved,
               SUM(CASE WHEN status = 'handed_over' THEN 1 ELSE 0 END) as handed_over
        FROM books
        GROUP BY class_grade
        ORDER BY class_grade ASC;
    """)
    class_rows = cur.fetchall()
    class_distribution = []
    for r in class_rows:
        cnt = r['total']
        pct = round((cnt / total_inventory * 100), 1) if total_inventory > 0 else 0
        class_distribution.append({
            'class_grade': r['class_grade'],
            'total': cnt,
            'percentage': pct,
            'available': r['available'],
            'reserved': r['reserved'],
            'handed_over': r['handed_over']
        })

    # 3. Subject Distribution
    cur.execute("""
        SELECT subject,
               COUNT(*) as total,
               SUM(CASE WHEN status = 'available' THEN 1 ELSE 0 END) as available,
               SUM(CASE WHEN status = 'handed_over' THEN 1 ELSE 0 END) as handed_over
        FROM books
        GROUP BY subject
        ORDER BY total DESC, subject ASC;
    """)
    subject_rows = cur.fetchall()
    subject_distribution = []
    for r in subject_rows:
        cnt = r['total']
        pct = round((cnt / total_inventory * 100), 1) if total_inventory > 0 else 0
        subject_distribution.append({
            'subject': r['subject'],
            'total': cnt,
            'percentage': pct,
            'available': r['available'],
            'handed_over': r['handed_over']
        })

    # 4. Status Breakdown
    statuses = [
        ('available', 'Available in Catalogue', available_books, 'success'),
        ('reserved', 'Reserved (Pending Pickup)', reserved_books, 'warning'),
        ('handed_over', 'Handed Over (Reused)', handed_over_books, 'primary'),
        ('retired', 'Retired / Damaged', retired_books, 'danger')
    ]
    status_distribution = []
    for code, label, count, color in statuses:
        pct = round((count / total_inventory * 100), 1) if total_inventory > 0 else 0
        status_distribution.append({
            'code': code,
            'label': label,
            'count': count,
            'percentage': pct,
            'color': color
        })

    # 5. Recent Activity Feed (Latest 8)
    cur.execute("""
        SELECT * FROM activity_logs
        ORDER BY id DESC
        LIMIT 8;
    """)
    recent_activity = [dict(r) for r in cur.fetchall()]

    # 6. Handover Velocity (Recent 7 days and 30 days)
    cur.execute("SELECT COUNT(*) FROM handovers WHERE date(handover_date) >= date('now', '-7 days');")
    handovers_7d = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM handovers WHERE date(handover_date) >= date('now', '-30 days');")
    handovers_30d = cur.fetchone()[0]

    return {
        'summary': {
            'total_inventory': total_inventory,
            'available_books': available_books,
            'reserved_books': reserved_books,
            'handed_over_books': handed_over_books,
            'retired_books': retired_books,
            'total_donations': total_donations,
            'pending_donations': pending_donations,
            'pending_requests': pending_requests,
            'approved_requests': approved_requests,
            'completed_handovers': completed_handovers,
            'unique_recipients': unique_recipients,
            'pending_actions': pending_actions,
            'reuse_rate': round((handed_over_books / total_inventory * 100), 1) if total_inventory > 0 else 0
        },
        'class_distribution': class_distribution,
        'subject_distribution': subject_distribution,
        'status_distribution': status_distribution,
        'recent_activity': recent_activity,
        'velocity': {
            'handovers_7d': handovers_7d,
            'handovers_30d': handovers_30d,
            'total_handovers': completed_handovers
        }
    }

def get_detailed_reports():
    """
    Compute comprehensive dataset for the Reports & Analytics desk and printable summary.
    """
    db = get_db()
    cur = db.cursor()

    dashboard_data = get_dashboard_analytics()
    summary = dashboard_data['summary']
    total_inventory = summary['total_inventory']

    # 1. Language Breakdown
    cur.execute("""
        SELECT language, COUNT(*) as count
        FROM books
        GROUP BY language
        ORDER BY count DESC;
    """)
    languages = []
    for r in cur.fetchall():
        cnt = r['count']
        pct = round((cnt / total_inventory * 100), 1) if total_inventory > 0 else 0
        languages.append({'language': r['language'], 'count': cnt, 'percentage': pct})

    # 2. Condition Breakdown
    cur.execute("""
        SELECT condition_state, COUNT(*) as count
        FROM books
        GROUP BY condition_state
        ORDER BY count DESC;
    """)
    conditions = []
    for r in cur.fetchall():
        cnt = r['count']
        pct = round((cnt / total_inventory * 100), 1) if total_inventory > 0 else 0
        conditions.append({'condition': r['condition_state'], 'count': cnt, 'percentage': pct})

    # 3. Monthly Trends (Handovers per month for last 6 months)
    cur.execute("""
        SELECT strftime('%Y-%m', handover_date) as month,
               COUNT(*) as count
        FROM handovers
        WHERE handover_date IS NOT NULL
        GROUP BY month
        ORDER BY month ASC
        LIMIT 12;
    """)
    monthly_handovers = [dict(r) for r in cur.fetchall()]

    # 4. Donor Breakdown by Class
    cur.execute("""
        SELECT donor_class, COUNT(*) as count
        FROM donations
        WHERE donor_class IS NOT NULL AND donor_class != ''
        GROUP BY donor_class
        ORDER BY count DESC;
    """)
    donor_classes = [dict(r) for r in cur.fetchall()]

    return {
        'summary': summary,
        'class_distribution': dashboard_data['class_distribution'],
        'subject_distribution': dashboard_data['subject_distribution'],
        'status_distribution': dashboard_data['status_distribution'],
        'languages': languages,
        'conditions': conditions,
        'monthly_handovers': monthly_handovers,
        'donor_classes': donor_classes,
        'velocity': dashboard_data['velocity']
    }

def sanitize_csv_cell(value):
    """
    Prevent CSV Formula Injection (CWE-1236).
    If a cell value begins with '=', '+', '-', '@', tab, or carriage return,
    prepend a single quote (') so spreadsheets strictly interpret it as literal text.
    """
    if value is None:
        return ""
    val_str = str(value)
    if val_str and val_str[0] in ('=', '+', '-', '@', '\t', '\r'):
        return "'" + val_str
    return val_str

def generate_inventory_csv():
    """
    Generate CSV text of the complete book inventory.
    Prepends UTF-8 BOM (\ufeff) for seamless opening in Microsoft Excel.
    Applies formula injection sanitization to all fields.
    """
    db = get_db()
    cur = db.cursor()
    cur.execute("""
        SELECT book_code, title, author, subject, class_grade, language,
               publisher, edition_year, condition_state, status,
               strftime('%Y-%m-%d %H:%M', created_at) as date_added
        FROM books
        ORDER BY id ASC;
    """)
    rows = cur.fetchall()

    output = io.StringIO()
    # Add UTF-8 BOM
    output.write('\ufeff')
    writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)

    writer.writerow([
        'Book Code', 'Title', 'Author', 'Subject', 'Class Grade',
        'Language', 'Publisher', 'Edition Year', 'Condition', 'Status', 'Date Added'
    ])

    for r in rows:
        writer.writerow([
            sanitize_csv_cell(r['book_code']),
            sanitize_csv_cell(r['title']),
            sanitize_csv_cell(r['author']),
            sanitize_csv_cell(r['subject']),
            sanitize_csv_cell(r['class_grade']),
            sanitize_csv_cell(r['language']),
            sanitize_csv_cell(r['publisher']),
            sanitize_csv_cell(r['edition_year']),
            sanitize_csv_cell(r['condition_state']),
            sanitize_csv_cell(r['status']),
            sanitize_csv_cell(r['date_added'])
        ])

    return output.getvalue()

def generate_handovers_csv():
    """
    Generate CSV text of the complete handover ledger.
    Prepends UTF-8 BOM (\ufeff) for seamless opening in Microsoft Excel.
    Applies formula injection sanitization to all fields.
    """
    db = get_db()
    cur = db.cursor()
    cur.execute("""
        SELECT handover_code, tracking_code, book_code, recipient_name,
               recipient_class, recipient_roll_no, recipient_contact,
               teacher_name, remarks,
               strftime('%Y-%m-%d %H:%M', handover_date) as date_handed_over
        FROM handovers
        ORDER BY id ASC;
    """)
    rows = cur.fetchall()

    output = io.StringIO()
    output.write('\ufeff')
    writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)

    writer.writerow([
        'Handover Code', 'Request Tracking Code', 'Book Code', 'Recipient Name',
        'Class Grade', 'Roll No', 'Contact', 'Authorized Teacher',
        'Remarks', 'Handover Date'
    ])

    for r in rows:
        writer.writerow([
            sanitize_csv_cell(r['handover_code']),
            sanitize_csv_cell(r['tracking_code']),
            sanitize_csv_cell(r['book_code']),
            sanitize_csv_cell(r['recipient_name']),
            sanitize_csv_cell(r['recipient_class']),
            sanitize_csv_cell(r['recipient_roll_no']),
            sanitize_csv_cell(r['recipient_contact']),
            sanitize_csv_cell(r['teacher_name']),
            sanitize_csv_cell(r['remarks']),
            sanitize_csv_cell(r['date_handed_over'])
        ])

    return output.getvalue()
