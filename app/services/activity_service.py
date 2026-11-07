"""
Activity Log Service: Domain Logic for System Audit Trail & Teacher Actions
"""

from app.database import get_db

def record_activity(action, entity_type, entity_id, actor_type='system', actor_name=None, details=None):
    """
    Record an immutable audit entry in the activity_logs table.
    """
    db = get_db()
    # Do not commit a caller-owned transaction. Several domain services write
    # the activity row as part of a larger atomic operation.
    transaction_already_open = db.in_transaction
    cur = db.cursor()
    cur.execute(
        """
        INSERT INTO activity_logs (
            action, entity_type, entity_id, actor_type, actor_name, details, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP);
        """,
        (action, entity_type, entity_id, actor_type, actor_name or 'System', details or '')
    )
    if not transaction_already_open:
        db.commit()
    return cur.lastrowid

def get_activity_logs(
    action=None,
    actor_type=None,
    search_query=None,
    date_from=None,
    date_to=None,
    limit=50,
    offset=0
):
    """
    Retrieve activity logs with multi-field filtering and pagination.
    Returns (logs_list, total_count).
    """
    db = get_db()
    cur = db.cursor()

    sql = ["SELECT * FROM activity_logs WHERE 1=1"]
    params = []

    if action and action.strip() and action != 'all':
        sql.append("AND action = ?")
        params.append(action.strip())

    if actor_type and actor_type.strip() and actor_type != 'all':
        sql.append("AND actor_type = ?")
        params.append(actor_type.strip())

    if search_query and search_query.strip():
        term = f"%{search_query.strip()}%"
        sql.append("AND (details LIKE ? OR actor_name LIKE ? OR action LIKE ?)")
        params.extend([term, term, term])

    if date_from and date_from.strip():
        sql.append("AND date(created_at) >= date(?)")
        params.append(date_from.strip())

    if date_to and date_to.strip():
        sql.append("AND date(created_at) <= date(?)")
        params.append(date_to.strip())

    count_sql = "SELECT COUNT(*) " + " ".join(sql)[len("SELECT * "):]
    cur.execute(count_sql, params)
    total_count = cur.fetchone()[0]

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

def get_distinct_actions():
    """Retrieve distinct actions for filter dropdowns."""
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT DISTINCT action FROM activity_logs ORDER BY action ASC;")
    return [r[0] for r in cur.fetchall() if r[0]]

def get_distinct_actor_types():
    """Retrieve distinct actor types for filter dropdowns."""
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT DISTINCT actor_type FROM activity_logs ORDER BY actor_type ASC;")
    return [r[0] for r in cur.fetchall() if r[0]]
