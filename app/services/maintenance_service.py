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
        # Fail closed: inability to inspect the marker means the gate state is unknown.
        return True

def set_maintenance_mode(active=True, exclusive=False):
    """Enable or disable database maintenance mode in memory and on disk.

    File-system failures are deliberately raised: restore must not proceed when
    the cross-process maintenance gate cannot be established or removed.
    """
    global _in_memory_maintenance
    with _STATE_LOCK:
        m_file = get_maintenance_file()
        if active:
            try:
                m_file.parent.mkdir(parents=True, exist_ok=True)
                payload = f"MAINTENANCE_ACTIVE:{time.time()}:PID:{os.getpid()}".encode("utf-8")
                if exclusive:
                    # O_EXCL atomically acquires the cross-process gate; a second
                    # process cannot replace an active restore's lock file.
                    descriptor = os.open(str(m_file), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
                    with os.fdopen(descriptor, "wb") as lock_stream:
                        lock_stream.write(payload)
                        lock_stream.flush()
                        os.fsync(lock_stream.fileno())
                else:
                    temp_file = m_file.with_name(m_file.name + ".tmp")
                    temp_file.write_bytes(payload)
                    os.replace(temp_file, m_file)
            except FileExistsError:
                # Another process owns an exclusive gate; do not claim ownership.
                raise
            except Exception:
                # Disk gate could not be established. Keep this process gated
                # rather than allowing uncertain DB access after a restore error.
                _in_memory_maintenance = True
                raise
            _in_memory_maintenance = True
        else:
            if m_file.exists():
                m_file.unlink()
            _in_memory_maintenance = False


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
    Gate new requests, drain work already in flight, and hold maintenance mode
    only while the caller performs the protected restore operation.
    """
    current_tid = threading.get_ident()

    # Establish the gate under lock, then release the lock before draining.
    # New requests can now register and promptly receive HTTP 503.
    with _STATE_LOCK:
        if _in_memory_maintenance or get_maintenance_file().exists():
            raise TimeoutError("Database maintenance is already active in this process or another process.")
        try:
            set_maintenance_mode(True, exclusive=True)
        except FileExistsError as exc:
            raise TimeoutError("Database maintenance is already active in another process.") from exc

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
    """Atomically persist restore metadata before modifying live database pages."""
    r_file = get_restore_in_progress_file()
    r_file.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "rollback_snapshot": str(rollback_snapshot_path),
        "target_backup": str(target_backup) if target_backup else "",
        "started_at": time.time(),
        "pid": os.getpid()
    }
    temp_file = r_file.with_name(r_file.name + ".tmp")
    temp_file.write_text(json.dumps(payload), encoding="utf-8")
    os.replace(temp_file, r_file)


def clear_restore_in_progress():
    """Remove the restore marker; surface failures so callers can fail safely."""
    r_file = get_restore_in_progress_file()
    if r_file.exists():
        r_file.unlink()


def get_interrupted_restore_info():
    """Return persisted restore metadata, or None when no marker exists."""
    r_file = get_restore_in_progress_file()
    if not r_file.exists():
        return None
    content = r_file.read_text(encoding="utf-8").strip()
    if content.startswith('{'):
        return json.loads(content)
    # Backward compatibility with older marker files containing only a path.
    return {"rollback_snapshot": content}
