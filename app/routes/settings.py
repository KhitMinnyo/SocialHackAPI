"""Account settings routes with an intentional CSRF vulnerability.

v2.0 book, Chapter 29.

The rest of SocialHackAPI authenticates with a JWT sent in the
Authorization header (stored in localStorage by the web UI), which makes
classic CSRF structurally impossible: an attacker page cannot read the
victim's localStorage (Same-Origin Policy) so it cannot attach the
header to a forged request.

This module deliberately introduces a SECOND, legacy authentication
scheme - a plain session cookie - to demonstrate what happens when an
API mixes cookie-based auth into a token-based app. Browsers attach
cookies automatically to ANY request aimed at this origin, including
cross-site ones launched from attacker HTML, so state-changing endpoints
protected only by the cookie become CSRF-able.

VULNERABILITIES:
1. POST /settings/update trusts the session cookie alone - no CSRF
   token, no Origin/Referer check, no SameSite enforcement beyond
   Flask's default.
2. GET /settings/session hands out that cookie (simulating a legacy
   login flow) so the lab is self-contained.
"""

import secrets

from flask import Blueprint, jsonify, request
from app import db
from app.models import User

settings_bp = Blueprint("settings", __name__)

# In-memory "session store" for the legacy cookie flow (lab-only).
_SESSIONS = {}


@settings_bp.route("/settings/session", methods=["GET"])
def create_session():
    """Simulate a legacy login that authenticates via COOKIE instead of
    a bearer token.

    Query param: ?user=alice  (any seeded username works)

    Returns a Set-Cookie header with a session id. A real victim would
    have this cookie silently attached by their browser to every request
    they make to this origin - which is exactly what the CSRF attack in
    Chapter 29 abuses.
    """
    username = request.args.get("user")
    if not username:
        return jsonify({"error": "?user=<username> required"}), 400

    sid = secrets.token_hex(16)
    _SESSIONS[sid] = username

    resp = jsonify({
        "message": f"Legacy cookie session created for '{username}'",
        "note": "Browser will now auto-attach this cookie to requests "
                "toward this origin - including cross-site forged ones.",
        "session_user": username,
    })
    # VULNERABILITY: no Secure flag (HTTP lab), and critically no explicit
    # SameSite=Strict/Lax hardening discussion marker - Flask's default
    # applies; the endpoint performs NO double-submit/CSRF token issuance.
    resp.set_cookie("sh_session", sid, httponly=True)
    return resp, 200


@settings_bp.route("/settings/update", methods=["POST"])
def update_settings():
    """Update the bio of whichever user owns the session cookie.

    VULNERABILITY: CSRF - the only authentication is the automatically
    attached cookie. An attacker page can submit:

        <form action="http://localhost:5001/api/v1/settings/update"
              method="POST"><input name="bio" value="hacked"></form>
        <script>document.forms[0].submit()</script>

    ...and the victim's browser sends it WITH the cookie attached.
    There is no CSRF token, no Origin/Referer validation, and JSON
    content-type is not enforced (form-encoded bodies are accepted),
    so even simple HTML forms work.
    """
    sid = request.cookies.get("sh_session")
    if not sid or sid not in _SESSIONS:
        return jsonify({"error": "not authenticated (no valid session cookie)"}), 401

    username = _SESSIONS[sid]

    # Accept form-encoded OR JSON - VULNERABILITY: permissive parsing makes
    # simple cross-site form posts possible (JSON-only would force a CORS
    # preflight that blocks most classic CSRF payloads).
    if request.is_json:
        bio = (request.get_json(silent=True) or {}).get("bio", "")
    else:
        bio = request.form.get("bio", "")

    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({"error": "user not found"}), 404

    user.bio = bio
    db.session.commit()

    return jsonify({
        "message": "Settings updated",
        "session_user": username,
        "new_bio": bio,
        # VULNERABILITY MARKER: response proves no Origin check happened -
        # a hardened endpoint would have rejected cross-site callers before
        # touching the database.
        "origin_header_seen": request.headers.get("Origin"),
    }), 200
