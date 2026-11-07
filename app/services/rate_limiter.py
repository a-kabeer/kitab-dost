"""
Thread-safe in-memory sliding-window rate limiter for Kitaab Bank.

The direct peer address is used by default. Forwarded client addresses are
accepted only when the immediate peer is explicitly configured as trusted.
"""

import ipaddress
import threading
import time
from flask import request, current_app, has_request_context

_rate_limits = {}
_rate_lock = threading.Lock()
_MAX_TRACKED_KEYS = 10000
_MAX_RETENTION_SECONDS = 3600


def get_client_ip():
    """Return the peer IP, trusting forwarded headers only from configured proxies."""
    if not has_request_context():
        return '127.0.0.1'

    remote_ip = request.remote_addr or '127.0.0.1'
    trusted_proxies = current_app.config.get('TRUSTED_PROXY_IPS', ())
    if remote_ip not in trusted_proxies:
        return remote_ip

    forwarded_for = request.headers.get('X-Forwarded-For', '')
    if not forwarded_for:
        return remote_ip

    candidate = forwarded_for.split(',')[0].strip()
    try:
        return str(ipaddress.ip_address(candidate))
    except ValueError:
        return remote_ip


def _prune_locked(now):
    """Remove timestamps and keys older than the maximum supported window."""
    cutoff = now - _MAX_RETENTION_SECONDS
    for key, history in list(_rate_limits.items()):
        fresh = [timestamp for timestamp in history if timestamp > cutoff]
        if fresh:
            _rate_limits[key] = fresh
        else:
            _rate_limits.pop(key, None)


def _key(action_key):
    return f"{action_key}:{get_client_ip()}"


def is_currently_limited(action_key: str, max_requests: int, window_seconds: int = 3600) -> bool:
    """Check a threshold without recording an attempt."""
    if max_requests < 1 or window_seconds < 1:
        raise ValueError("Rate limit and window must be positive integers")
    now = time.time()
    key = _key(action_key)
    cutoff = now - window_seconds
    with _rate_lock:
        _prune_locked(now)
        history = [timestamp for timestamp in _rate_limits.get(key, []) if timestamp > cutoff]
        if history:
            _rate_limits[key] = history
        else:
            _rate_limits.pop(key, None)
        return len(history) >= max_requests


def record_attempt(action_key: str, window_seconds: int = 3600):
    """Record a failed or otherwise countable attempt without applying a threshold."""
    if window_seconds < 1:
        raise ValueError("window_seconds must be positive")
    now = time.time()
    key = _key(action_key)
    cutoff = now - window_seconds
    with _rate_lock:
        _prune_locked(now)
        history = [timestamp for timestamp in _rate_limits.get(key, []) if timestamp > cutoff]
        history.append(now)
        _rate_limits[key] = history
        if len(_rate_limits) > _MAX_TRACKED_KEYS:
            _prune_locked(now)
            if len(_rate_limits) > _MAX_TRACKED_KEYS:
                oldest_key = min(_rate_limits, key=lambda item: _rate_limits[item][-1])
                _rate_limits.pop(oldest_key, None)


def reset_rate_limit(action_key: str):
    """Clear a counter for the current client."""
    key = _key(action_key)
    with _rate_lock:
        _rate_limits.pop(key, None)


def is_rate_limited(action_key: str, max_requests: int, window_seconds: int = 3600) -> bool:
    """
    Check and record one attempt in a sliding window.
    Returns True when the client is already at the configured threshold.
    """
    if max_requests < 1 or window_seconds < 1:
        raise ValueError("Rate limit and window must be positive integers")
    now = time.time()
    key = _key(action_key)
    cutoff = now - window_seconds
    with _rate_lock:
        _prune_locked(now)
        history = [timestamp for timestamp in _rate_limits.get(key, []) if timestamp > cutoff]
        if len(history) >= max_requests:
            _rate_limits[key] = history
            return True
        history.append(now)
        _rate_limits[key] = history
        return False


def reset_rate_limits():
    """Clear all in-memory rate limits (primarily for automated testing)."""
    with _rate_lock:
        _rate_limits.clear()
