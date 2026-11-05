"""
Kitaab Bank - Maintenance & Deterministic Restoration Concurrency Manager
Provides deterministic connection draining, cross-process maintenance gating,
and crash-resilient recovery for database restoration and exhibition mode.
"""

import os
import json
import time
import threading
from pathlib import Path
from contextlib import contextmanager

_STATE_LOCK = threading.RLock()
_in_memory_maintenance = False

# Tracking active in-flight requests and database connections
_active_requests = {}      # request_id -> thread_id
_active_db_threads = set() # set of thread_ids currently holding open DB connections

def get_maintenance_file():
    """Locate the .maintenance_lock file relative to DATABASE_PATH or project root."""
    try:
        from flask import current_app
        if current_app and current_app.config.get('DATABASE_PATH'):
            return Path(current_app.config['DATABASE_PATH']).parent / '.maintenance_lock'
    except Exception:
        pass
    return Path(__file__).resolve().parent.parent.parent / '.maintenance_lock'

def get_restore_in_progress_file():
    """Locate the .restore_in_progress marker file."""
    try:
        from flask import current_app
        if current_app and current_app.config.get('DATABASE_PATH'):
            return Path(current_app.config['DATABASE_PATH']).parent / '.restore_in_progress'
    except Exception:
        pass
    return Path(__file__).resolve().parent.parent.parent / '.restore_in_progress'

# -----------------------------------------------------------------------------
# 1. Maintenance Mode State
# -----------------------------------------------------------------------------
def is_maintenance_active():
    """
    Check if database maintenance mode is currently active.
    Returns True if in-memory flag is True or .maintenance_lock exists on disk.
    """
    global _in_memory_maintenance
    if _in_memory_maintenance:
        return True
    try:
        m_file = get_maintenance_file()
        return m_file.exists()
    except Exception:
        return False

def set_maintenance_mode(active=True):
    """Enable or disable maintenance mode in memory and on disk."""
    global _in_memory_maintenance
    with _STATE_LOCK:
        _in_memory_maintenance = active
        try:
            m_file = get_maintenance_file()
            if active:
                m_file.write_text(f"MAINTENANCE_ACTIVE:{time.time()}")
            else:
                if m_file.exists():
                    m_file.unlink()
        except Exception:
            pass

# -----------------------------------------------------------------------------
# 2. Deterministic Request & Connection Tracking
# -----------------------------------------------------------------------------
def register_request(req_id, thread_id=None):
    """Track an incoming web request."""
    with _STATE_LOCK:
        _active_requests[req_id] = thread_id or threading.get_ident()

def unregister_request(req_id):
    """Untrack a completed web request."""
    with _STATE_LOCK:
        _active_requests.pop(req_id, None)

def register_db_connection(thread_id=None):
    """Track that a thread currently holds an open SQLite database connection."""
    tid = thread_id or threading.get_ident()
    with _STATE_LOCK:
        _active_db_threads.add(tid)

def unregister_db_connection(thread_id=None):
    """Track that a thread's SQLite database connection has been closed."""
    tid = thread_id or threading.get_ident()
    with _STATE_LOCK:
        _active_db_threads.discard(tid)

def get_active_counts(exclude_thread=None):
    """Return count of active requests and active DB connections excluding a controller thread."""
    with _STATE_LOCK:
        req_count = sum(1 for tid in _active_requests.values() if tid != exclude_thread)
        db_count = sum(1 for tid in _active_db_threads if tid != exclude_thread)
        return req_count, db_count

def drain_connections(timeout=5.0, exclude_thread=None, poll_interval=0.05):
    """
    Deterministically poll until all active requests and database connections
    (excluding the controller thread) have completed and closed.
    
    Returns True if all connections drained cleanly within timeout; False if timed out.
    """
    start_time = time.time()
    while time.time() - start_time < timeout:
        req_count, db_count = get_active_counts(exclude_thread=exclude_thread)
        if req_count == 0 and db_count == 0:
            return True
        time.sleep(poll_interval)

    # Final check
    req_count, db_count = get_active_counts(exclude_thread=exclude_thread)
    return req_count == 0 and db_count == 0

@contextmanager
def maintenance_context(timeout=5.0):
    """
    Context manager to safely encapsulate database restoration.
    1. Sets maintenance mode (rejects new incoming requests with 503).
    2. Deterministically drains active in-flight requests and connections.
    3. Fails safely via TimeoutError if connections cannot be drained within timeout.
    4. Guarantees maintenance mode is released upon exit or failure.
    """
    current_tid = threading.get_ident()
    with _STATE_LOCK:
        set_maintenance_mode(True)
        try:
            drained = drain_connections(timeout=timeout, exclude_thread=current_tid)
            if not drained:
                req_c, db_c = get_active_counts(exclude_thread=current_tid)
                raise TimeoutError(
                    f"Connection drain timeout ({timeout}s): {req_c} active requests and "
                    f"{db_c} active DB connections could not be drained safely. Live database was not modified."
                )
            yield
        finally:
            set_maintenance_mode(False)

# -----------------------------------------------------------------------------
# 3. Interrupted Restore Crash Resilience
# -----------------------------------------------------------------------------
def mark_restore_in_progress(rollback_snapshot_path, target_backup=None):
    """Record that database restoration is in progress on disk before modifying live pages."""
    try:
        r_file = get_restore_in_progress_file()
        payload = {
            "rollback_snapshot": str(rollback_snapshot_path),
            "target_backup": str(target_backup) if target_backup else "",
            "started_at": time.time(),
            "pid": os.getpid()
        }
        r_file.write_text(json.dumps(payload))
    except Exception:
        pass

def clear_restore_in_progress():
    """Remove the .restore_in_progress marker once post-restore verification succeeds."""
    try:
        r_file = get_restore_in_progress_file()
        if r_file.exists():
            r_file.unlink()
    except Exception:
        pass

def get_interrupted_restore_info():
    """Check if an interrupted restore marker exists and return its metadata dict, or None."""
    try:
        r_file = get_restore_in_progress_file()
        if r_file.exists():
            content = r_file.read_text().strip()
            if content.startswith('{'):
                return json.loads(content)
            else:
                return {"rollback_snapshot": content}
    except Exception:
        pass
    return None
