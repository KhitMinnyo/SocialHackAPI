"""Stored XSS -> session/token theft lab (in-memory, self-contained).

"Beyond the Lab" extension. This teaches the mechanism behind a very common
real-world pattern (the one this whole "Beyond the Lab" branch started
from): a victim who is already logged into a platform gets their session
hijacked through injected script, and the attacker then reuses that
session/token to act as the victim - e.g. auto-messaging every contact in
their friend list. See the new `quizapp-fun-2000` OAuth client in oauth.py
and cheatsheets/beyond-lab-xss-oauth-cheatsheet.md for the companion lab
that carries this through to "message everyone in the contact list."

Deliberately ISOLATED from the main `/app` web UI. app/routes/web.py's
docstring states "the UI itself has zero intentional vulnerabilities" -
that stays true. Everything below lives under its own `/xss-lab/*` and
`/api/v1/xss-lab/*` paths, a separate "attacker playground" a student posts
a payload into and then visits, the same way OWASP Juice Shop / PortSwigger
XSS labs work.

VULNERABILITIES:
1. Stored XSS: a widget's `content` is rendered with Jinja2's `| safe`
   filter - i.e. NOT auto-escaped - so a widget containing <script> executes
   for whoever views it (templates/xss_lab/widget.html).
2. SocialHack's JWT lives in localStorage (see static/js/app.js - a
   realistic, common SPA pattern) and these lab pages share the SAME origin
   (http://localhost:5001) as the real `/app` SPA. Injected script can
   therefore read `localStorage.getItem('socialhack_token')` directly - no
   cookie theft needed, same idea as real-world session/token hijacking via
   XSS or a malicious browser extension.
3. `/api/v1/xss-lab/collect` is an unauthenticated "attacker collector"
   endpoint. It stands in for the attacker's own server elsewhere on the
   internet - kept inside this same app so the full injection ->
   exfiltration -> reuse chain is reproducible with zero external
   infrastructure and zero real user data.
"""

import time
import uuid
from flask import Blueprint, request, jsonify, render_template
from app.utils import token_required

xss_lab_bp = Blueprint("xss_lab", __name__)

# In-memory "guestbook" widgets, keyed by id. Anyone logged in can post one;
# anyone (including a logged-out visitor) can view one.
_widgets = {}

# In-memory "attacker collector" inbox - what a real attacker's server would
# log when a stolen token gets exfiltrated to it.
_captured = []


@xss_lab_bp.route("/api/v1/xss-lab/widgets", methods=["POST"])
@token_required
def create_widget():
    """Post a new guestbook widget.

    VULNERABILITY: `content` is stored as-is and later rendered completely
    unescaped - this is the injection point. No filtering, no CSP, nothing.
    """
    data = request.get_json(silent=True) or {}
    content = data.get("content", "")
    if not content:
        return jsonify({"error": "content is required"}), 400

    widget_id = uuid.uuid4().hex[:8]
    _widgets[widget_id] = {
        "id": widget_id,
        "content": content,
        "author_user_id": request.current_user_id,
        "created_at": time.time(),
    }
    return jsonify({
        "message": "Widget created",
        "widget_id": widget_id,
        "view_url": f"/xss-lab/widget/{widget_id}",
    }), 201


@xss_lab_bp.route("/api/v1/xss-lab/widgets/<widget_id>", methods=["GET"])
def get_widget(widget_id):
    """Raw JSON view of a widget (for reference/debugging)."""
    widget = _widgets.get(widget_id)
    if not widget:
        return jsonify({"error": "Widget not found"}), 404
    return jsonify({"widget": widget}), 200


@xss_lab_bp.route("/xss-lab/widget/<widget_id>", methods=["GET"])
def widget_page(widget_id):
    """Render a widget as an HTML page - the page a 'victim' opens.

    VULNERABILITY: `widget.content` is rendered in the template with the
    Jinja2 `| safe` filter, i.e. NOT auto-escaped (see
    templates/xss_lab/widget.html). Whatever HTML/JS the author put in
    `content` runs in the viewer's browser, on this app's origin.
    """
    widget = _widgets.get(widget_id)
    if not widget:
        return jsonify({"error": "Widget not found"}), 404
    return render_template("xss_lab/widget.html", widget=widget)


@xss_lab_bp.route("/api/v1/xss-lab/collect", methods=["POST"])
def collect():
    """Unauthenticated 'attacker collector' endpoint.

    Stands in for an attacker's own server elsewhere on the internet, kept
    inside this app so the whole stored-XSS -> token-exfiltration chain is
    reproducible without any real external endpoint or real user data.
    Anything POSTed here (typically {"widget_id": "...", "stolen_token":
    "..."}) is just logged for the student to inspect on the dashboard.
    """
    data = request.get_json(silent=True) or {}
    _captured.append({
        "received_at": time.time(),
        "source_ip": request.remote_addr,
        "payload": data,
    })
    return jsonify({"status": "logged"}), 200


@xss_lab_bp.route("/xss-lab/attacker-dashboard", methods=["GET"])
def attacker_dashboard():
    """Everything the collector has received so far - the 'proof of impact'
    screen for this lab, the same idea as the OAuth lab's id_token or the
    MCP lab's exfiltrated admin api_key."""
    return render_template("xss_lab/dashboard.html", captured=list(reversed(_captured)))
