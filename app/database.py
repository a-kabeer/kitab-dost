import sqlite3
import time
from contextlib import contextmanager
from flask import g, current_app

def get_db():
    """Get or create SQLite connection for the current application context."""
    if 'db' not in g:
        db_path = current_app.config['DATABASE_PATH']
        timeout = current_app.config.get('SQLITE_TIMEOUT', 5.0)

        conn = sqlite3.connect(
            str(db_path),
            timeout=timeout
        )
        conn.row_factory = sqlite3.Row

        # Execute performance, concurrency and data safety pragmas
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON;")
        cursor.execute("PRAGMA journal_mode = WAL;")
        cursor.execute("PRAGMA busy_timeout = 5000;")
        cursor.execute("PRAGMA synchronous = NORMAL;")
        cursor.close()

        g.db = conn

    return g.db

def close_db(e=None):
    """Close the current request's SQLite connection if open."""
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db(app):
    """Initialize the SQLite database schema, enforce WAL mode, and seed default teacher."""
    db_path = app.config['DATABASE_PATH']
    # Ensure parent directory exists
    db_path.parent.mkdir(parents=True, exist_ok=True)

    with app.app_context():
        db = get_db()
        with current_app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

        # Ensure author column exists in donations table (schema migration)
        cur = db.cursor()
        cur.execute("PRAGMA table_info(donations);")
        donation_cols = [r[1] for r in cur.fetchall()]
        if 'author' not in donation_cols:
            cur.execute("ALTER TABLE donations ADD COLUMN author TEXT;")
            db.commit()

        # Seed initial teacher account if none exists
        cur = db.cursor()
        cur.execute("SELECT COUNT(*) FROM teachers;")
        if cur.fetchone()[0] == 0:
            from werkzeug.security import generate_password_hash
            pwd_hash = generate_password_hash("Teacher@123")
            cur.execute(
                "INSERT INTO teachers (username, password_hash, full_name, email, role, is_active) "
                "VALUES (?, ?, ?, ?, ?, 1);",
                ('teacher', pwd_hash, 'School Teacher / Incharge', 'teacher@school.edu.pk', 'admin')
            )
            db.commit()

        # Verify WAL mode
        cur.execute("PRAGMA journal_mode;")
        mode = cur.fetchone()[0]
        cur.close()

        app.logger.info(f"Database initialized at {db_path} with journal_mode: {mode}")

@contextmanager
def db_transaction(db=None, max_retries=3, initial_delay=0.1):
    """
    Context manager for short, safe write transactions.
    Uses 'BEGIN IMMEDIATE' to acquire write lock up front, preventing deadlocks.
    Includes exponential backoff retry for transient SQLite lock contention.
    """
    if db is None:
        db = get_db()

    delay = initial_delay
    for attempt in range(1, max_retries + 1):
        try:
            db.execute("BEGIN IMMEDIATE")
            yield db
            db.commit()
            return
        except sqlite3.OperationalError as e:
            db.execute("ROLLBACK")
            if "database is locked" in str(e).lower() and attempt < max_retries:
                time.sleep(delay)
                delay *= 2
                continue
            raise e
        except Exception as e:
            db.execute("ROLLBACK")
            raise e
