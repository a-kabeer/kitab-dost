"""
In-memory sliding window rate limiter for Kitaab Bank.
Configured for shared school Wi-Fi and ngrok exhibition tunnels.
"""

import time
from collections import defaultdict
from flask import request, current_app

# Store request timestamps per (key_prefix, ip)
_rate_limits = defaultdict(list)

def get_client_ip():
    """Extract client IP safely from X-Forwarded-For or remote_addr."""
    x_forwarded_for = request.headers.get('X-Forwarded-For')
    if x_forwarded_for:
        # First IP in chain is the original client
        return x_forwarded_for.split(',')[0].strip()
    return request.remote_addr or '127.0.0.1'

def is_rate_limited(action_key: str, max_requests: int, window_seconds: int = 3600) -> bool:
    """
    Check if the current client IP has exceeded the allowed request threshold.
    Returns True if rate limited (should block), False if allowed.
    """
    client_ip = get_client_ip()
    composite_key = f"{action_key}:{client_ip}"
    now = time.time()
    cutoff = now - window_seconds

    # Filter out expired timestamps
    history = [t for t in _rate_limits[composite_key] if t > cutoff]
    
    if len(history) >= max_requests:
        _rate_limits[composite_key] = history
        return True
    
    history.append(now)
    _rate_limits[composite_key] = history
    return False

def reset_rate_limits():
    """Clear in-memory rate limits (primarily for automated testing)."""
    _rate_limits.clear()
