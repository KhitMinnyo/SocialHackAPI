"""OTP (one-time code) request routes — a real, bypassable rate limiter.

OWASP API4:2023 - Unrestricted Resource Consumption (rate-limit bypass angle)

Unlike posts/like or auth/login (which have NO rate limiting at all, by
design, so earlier labs can hammer them freely), this endpoint has a REAL
rate limiter applied: 3 requests per 60 seconds. The point of this lesson
isn't "no rate limit" - it's "a rate limit exists, but its implementation
can be bypassed."
"""

import random
from flask import Blueprint, request, jsonify
from app.utils import token_required
from app.rate_limiter import is_rate_limited

otp_bp = Blueprint("otp", __name__)

# In-memory store of the "currently valid" OTP per phone number, so the
# lab can demonstrate that bypassing the rate limit lets you keep
# requesting fresh codes for the SAME target phone number indefinitely.
_otp_store = {}

MAX_REQUESTS = 3
WINDOW_SECONDS = 60


@otp_bp.route("/otp/request", methods=["POST"])
@token_required
def request_otp():
    """Request a one-time verification code for a phone number.

    VULNERABILITY: Real rate limiting IS applied (3 req/60s), but the
    limiter keys on a client-spoofable X-Forwarded-For header (see
    app/rate_limiter.py). Rotating that header on every request resets
    the bucket, making the limit meaningless against a determined caller
    targeting the same phone_number over and over (e.g. OTP brute-force
    or SMS-bombing a victim).
    """
    data = request.get_json()
    if not data or not data.get("phone_number"):
        return jsonify({"error": "phone_number is required. Send {\"phone_number\": \"+959123456789\"}"}), 400

    phone_number = data["phone_number"]

    limited, remaining, reset_in = is_rate_limited("otp_request", MAX_REQUESTS, WINDOW_SECONDS)
    if limited:
        return jsonify({
            "error": "Rate limit exceeded. Try again later.",
            "retry_after_seconds": round(reset_in, 1),
        }), 429

    code = f"{random.randint(0, 999999):06d}"
    _otp_store[phone_number] = code

    return jsonify({
        "message": f"OTP sent to {phone_number}",
        # VULNERABILITY (kept consistent with this course's style, e.g.
        # auth/reset-password): the code is returned directly instead of
        # actually being sent via SMS, so the lab is fully self-contained.
        "otp_code": code,
        "requests_remaining_in_window": remaining,
        "window_seconds": WINDOW_SECONDS,
    }), 200


@otp_bp.route("/otp/verify", methods=["POST"])
@token_required
def verify_otp():
    """Verify a one-time code for a phone number."""
    data = request.get_json()
    if not data or not data.get("phone_number") or not data.get("code"):
        return jsonify({"error": "phone_number and code are required"}), 400

    phone_number = data["phone_number"]
    code = data["code"]

    expected = _otp_store.get(phone_number)
    if expected and expected == code:
        return jsonify({"message": "OTP verified successfully", "verified": True}), 200

    return jsonify({"error": "Invalid or expired code", "verified": False}), 400
