"""Web UI page for the /api/v1/otp/* endpoints (OWASP API4:2023 -
Unrestricted Resource Consumption, rate-limit bypass angle -
app/routes/otp.py + app/rate_limiter.py).

Same house rule as the rest of app/routes/web_*.py: this file has no
logic of its own - the page's own JavaScript (app/static/js/otp.js) calls
the existing, unmodified /api/v1/otp/request and /api/v1/otp/verify
endpoints via SH.apiFetch().

Like web_promotions.py, this page is a plain wrapper with no client-side
twist at all. The rate limiter's bypass depends on setting a custom
X-Forwarded-For header on each request (see app/rate_limiter.py), and
this page never gives the visitor any control over request headers -
SH.apiFetch() only ever sets Content-Type and Authorization. There is
nothing to "protect against" here: an ordinary web UI never had a way to
touch that header in the first place. Calling the same two endpoints
directly (curl/Postman/Burp) can still set X-Forwarded-For freely and
bypass the limiter exactly as before - see otp.py's own docstring.
"""
from flask import Blueprint, render_template

web_otp_bp = Blueprint("web_otp", __name__)


@web_otp_bp.route("/app/otp", methods=["GET"])
def otp_page():
    return render_template("web/otp.html")
