"""
Kitaab Bank - Maintenance & Restoration Concurrency Manager
Provides atomic locking and maintenance mode gating during database restoration
and exhibition demo mode switches to prevent concurrent writes from corrupting data.
"""

import os
import time
import threading
from pathlib import Path
from contextlib import contextmanager

MAINTENANCE_LOCK = threading.RLock()
_in_memory_maintenance = False

def get_maintenance_file():
    """Locate the .maintenance_lock file relative to DATABASE_PATH or project root."""
    try:
        from flask import current_app
        if current_app and current_app.config.get('DATABASE_PATH'):
            return Path(current_app.config['DATABASE_PATH']).parent / '.maintenance_lock'
    except Exception:
        pass
    return Path(__file__).resolve().parent.parent.parent / '.maintenance_lock'

def is_maintenance_active():
    """
    Check if database maintenance mode is currently active.
    Returns True if either in-memory flag is True or .maintenance_lock file exists on disk.
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

@contextmanager
def maintenance_context():
    """
    Context manager to safely encapsulate database restoration.
    1. Blocks incoming non-maintenance web requests with 503.
    2. Drains active requests (brief wait).
    3. Guarantees maintenance mode is cleared upon exit or failure.
    """
    with MAINTENANCE_LOCK:
        set_maintenance_mode(True)
        try:
            # Brief pause to allow in-flight queries on other threads to close
            time.sleep(0.3)
            yield
        finally:
            set_maintenance_mode(False)
