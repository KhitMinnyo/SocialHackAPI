"""Web UI page for the /api/v1/export/profile endpoint (Excessive Data
Exposure / BOPLA - app/routes/upload.py).

Same house rule as the rest of app/routes/web_*.py: this file has no
logic of its own - the page's own JavaScript (app/static/js/export-profile.js)
calls the existing, unmodified GET /api/v1/export/profile endpoint via
SH.apiFetch() and offers the response as a downloadable file. Like
web_promotions.py and web_otp.py, this is a plain wrapper with no
client-side twist - the excessive data exposure is entirely on the API
side already (to_full_dict() returning fields like password_hash,
api_key, and internal_notes), and calling the endpoint directly
(curl/Postman/Burp) still returns the exact same over-exposed payload.
"""
from flask import Blueprint, render_template

web_export_bp = Blueprint("web_export", __name__)


@web_export_bp.route("/app/export", methods=["GET"])
def export_profile_page():
    return render_template("web/export_profile.html")
