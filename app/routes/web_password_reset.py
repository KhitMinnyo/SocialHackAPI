"""Web UI pages for the "forgot password" flow, plus one lab-only inbox peek.

This module adds a friendlier front-end to auth.py's EXISTING (unmodified)
password-reset endpoints:

    POST /api/v1/auth/reset-password          (app/routes/auth.py, ch11)
    POST /api/v1/auth/reset-password/confirm  (app/routes/auth.py, ch11)

Neither endpoint above is touched by this file - both keep their exact
current behavior (including the intentional "predictable token, returned
directly in the response" vulnerability documented in ch11). This module
is purely additive:

  GET  /app/forgot-password        page shell - request a reset email
  GET  /app/mailbox                page shell - lab-only "inbox" viewer
  GET  /api/v1/auth/mailbox        NEW, read-only. Re-reads User.reset_token
                                    (already stored by reset_password() in
                                    auth.py) and renders it as a simulated
                                    email, since this app never sends real
                                    mail. Does not mutate anything, does not
                                    duplicate or change reset-password's own
                                    logic, and does not expose any field that
                                    POST /api/v1/auth/reset-password wasn't
                                    already returning directly in its own
                                    response.

Follows the same "web pages carry no vulnerabilities of their own, the
API underneath does" split as app/routes/web.py.
"""

from flask import Blueprint, jsonify, render_template, request

from app.models import User

web_password_reset_bp = Blueprint("web_password_reset", __name__)


@web_password_reset_bp.route("/app/forgot-password", methods=["GET"])
def forgot_password_page():
    """Page shell - form posts to the existing reset-password API via JS."""
    return render_template("web/forgot_password.html")


@web_password_reset_bp.route("/app/mailbox", methods=["GET"])
def mailbox_page():
    """Page shell - lab-only simulated inbox, see auth_mailbox() below."""
    return render_template("web/mailbox.html")


@web_password_reset_bp.route("/api/v1/auth/mailbox", methods=["GET"])
def auth_mailbox():
    """LAB-ONLY convenience endpoint - simulates checking an email inbox.

    SocialHackAPI never sends real email. POST /api/v1/auth/reset-password
    already returns the reset token directly in its own JSON response (see
    app/routes/auth.py - "VULNERABILITY: Token returned directly in
    response", ch11 Broken Authentication). This endpoint does not add a
    new secret or a new exposure path: it re-reads that SAME already-stored
    field (User.reset_token) so the web UI's forgot-password flow can be
    completed end-to-end without leaving the browser or reading raw JSON.
    Deliberately unauthenticated (like a throwaway-inbox viewer) - by the
    time someone needs this page they're locked out, so requiring a JWT
    would defeat the point.
    """
    email = (request.args.get("email") or "").strip()
    if not email:
        return jsonify({"error": "?email=<address> is required"}), 400

    user = User.query.filter_by(email=email).first()
    if not user or not user.reset_token:
        return jsonify({"empty": True, "email": email}), 200

    return jsonify({
        "empty": False,
        "email": email,
        "from": "SocialHack Security <security@socialhack.local>",
        "subject": "Reset your SocialHack password",
        "body_preview": (
            f"Hi {user.username}, we received a request to reset your "
            "SocialHack password. Use the code below within about an hour."
        ),
        "reset_token": user.reset_token,
    }), 200
