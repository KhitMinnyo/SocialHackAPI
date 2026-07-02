"""A real, but intentionally bypassable, in-memory rate limiter.

This is deliberately NOT applied to any endpoint used by earlier labs
(register, login, follow, admin, etc.) so it can't break existing lesson
solutions that rely on making several rapid requests. It's applied only
to the new /api/v1/otp/request endpoint (app/routes/otp.py), which exists
specifically to teach rate-limit bypass techniques.

VULNERABILITY (API4:2023 - Unrestricted Resource Consumption, bypass angle):
- The rate limit key is derived from the client-supplied X-Forwarded-For
  header FIRST, falling back to the socket's remote address. This app is
  not actually running behind a real reverse proxy in this lab, so nothing
  strips or validates that header - any client can simply set a different
  X-Forwarded-For value on every request to get a fresh rate-limit bucket.
  This mirrors an extremely common real-world misconfiguration: trusting
  X-Forwarded-For without restricting it to a known, trusted proxy chain.
- The window is a naive FIXED window (not sliding/token-bucket), so a
  burst of requests timed just before/after a window boundary can also
  exceed the "intended" rate.
"""

import time
from collections import defaultdict
from flask import request

# In-memory store: {key: [timestamps...]}
_request_log = defaultdict(list)


def get_rate_limit_key():
    """Derive the rate-limit bucket key for the current request.

    VULNERABILITY: trusts X-Forwarded-For blindly, with no check that the
    request actually came through a trusted proxy that sets this header
    itself. A client can set any value it wants.
    """
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        # Take the first (client-claimed) address in the chain, exactly
        # like a naive "just read XFF" implementation would.
        return forwarded.split(",")[0].strip()
    return request.remote_addr or "unknown"


def is_rate_limited(bucket_name, max_requests, window_seconds):
    """Fixed-window rate limiter. Returns (limited: bool, remaining: int, reset_in: float)."""
    key = f"{bucket_name}:{get_rate_limit_key()}"
    now = time.time()

    window_start = now - (now % window_seconds)
    timestamps = _request_log[key]

    # Drop timestamps outside the current fixed window
    timestamps[:] = [t for t in timestamps if t >= window_start]

    if len(timestamps) >= max_requests:
        reset_in = window_start + window_seconds - now
        return True, 0, max(reset_in, 0)

    timestamps.append(now)
    remaining = max_requests - len(timestamps)
    reset_in = window_start + window_seconds - now
    return False, remaining, max(reset_in, 0)


def reset_all():
    """Testing helper - clears all rate-limit state."""
    _request_log.clear()
