"""
Kitaab Bank - Maintenance & Deterministic Restoration Concurrency Manager
Provides deterministic connection draining, cross-process maintenance gating,
and crash-resilient recovery for database restoration and exhibition mode.
"""

import os
import re
import errno
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

def get_restore_recovery_lock_file():
    """Locate the OS-locked file that serializes startup restore recovery."""
    try:
        from flask import current_app
        if current_app and current_app.config.get('DATABASE_PATH'):
            return Path(current_app.config['DATABASE_PATH']).parent / '.restore_recovery.lock'
    except Exception:
        pass
    return Path(__file__).resolve().parent.parent.parent / '.restore_recovery.lock'


def read_maintenance_lock_info():
    """Read and validate the owner PID and exact bytes of the maintenance gate."""
    lock_file = get_maintenance_file()
    if not lock_file.exists():
        return None

    payload = lock_file.read_bytes()
    try:
        value = payload.decode('utf-8').strip()
    except UnicodeDecodeError as exc:
        raise ValueError("Maintenance lock is not valid UTF-8.") from exc

    match = re.fullmatch(r"MAINTENANCE_ACTIVE:[^:]+:PID:(\\d+)", value)
    if not match:
        raise ValueError("Maintenance lock has an unknown or malformed owner.")

    pid = int(match.group(1))
    if pid <= 0:
        raise ValueError("Maintenance lock contains an invalid process ID.")
    return {"pid": pid, "payload": payload}


def is_process_running(pid):
    """Return whether a PID is alive without ever signalling it on Windows.

    Access-denied and otherwise ambiguous states are treated as alive so startup
    recovery fails closed rather than touching a database owned by another process.
    """
    if not isinstance(pid, int) or isinstance(pid, bool) or pid <= 0:
        raise ValueError("Process ID must be a positive integer.")
    if pid == os.getpid():
        return True

    if os.name == "nt":
        import ctypes
        from ctypes import wintypes

        PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
        ERROR_ACCESS_DENIED = 5
        ERROR_INVALID_PARAMETER = 87
        STILL_ACTIVE = 259

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        open_process = kernel32.OpenProcess
        open_process.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        open_process.restype = wintypes.HANDLE
        handle = open_process(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
        if not handle:
            error_code = ctypes.get_last_error()
            if error_code == ERROR_INVALID_PARAMETER:
                return False
            if error_code == ERROR_ACCESS_DENIED:
                return True
            raise OSError(error_code, ctypes.FormatError(error_code))

        try:
            exit_code = wintypes.DWORD()
            if not kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code)):
                error_code = ctypes.get_last_error()
                raise OSError(error_code, ctypes.FormatError(error_code))
            return exit_code.value == STILL_ACTIVE
        finally:
            kernel32.CloseHandle(handle)

    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError as exc:
        if exc.errno == errno.ESRCH:
            return False
        if exc.errno == errno.EPERM:
            return True
        raise


def clear_stale_maintenance_lock(expected_payload):
    """Remove a lock only when its bytes still match the previously checked owner."""
    global _in_memory_maintenance
    with _STATE_LOCK:
        lock_file = get_maintenance_file()
        if not lock_file.exists():
            _in_memory_maintenance = False
            return True
        if lock_file.read_bytes() != expected_payload:
            return False
        lock_file.unlink()
        _in_memory_maintenance = False
        return True


@contextmanager
def restore_recovery_context():
    """Acquire a cross-process, crash-released lock for startup recovery.

    POSIX uses flock; Windows uses a one-byte msvcrt file lock. The lock file
    intentionally remains on disk: the operating system releases the lock when
    the process exits, including after a crash.
    """
    lock_file = get_restore_recovery_lock_file()
    lock_file.parent.mkdir(parents=True, exist_ok=True)
    stream = open(lock_file, "a+b")
    acquired = False
    windows_lock = os.name == "nt"
    try:
        stream.seek(0, os.SEEK_END)
        if stream.tell() == 0:
            stream.write(b"\\0")
            stream.flush()
        stream.seek(0)

        if windows_lock:
            import msvcrt
            try:
                msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
            except OSError as exc:
                raise TimeoutError("Another process is already recovering the interrupted restore.") from exc
        else:
            import fcntl
            try:
                fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as exc:
                raise TimeoutError("Another process is already recovering the interrupted restore.") from exc
        acquired = True
        yield
    finally:
        if acquired:
            try:
                stream.seek(0)
                if windows_lock:
                    import msvcrt
                    msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(stream.fileno(), fcntl.LOCK_UN)
            except OSError:
                pass
        stream.close()

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
