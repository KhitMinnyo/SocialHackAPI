"""Miscellaneous routes with Command Injection, NoSQL-style Injection, and Webhook vulnerabilities."""

import os
import subprocess
import json
from flask import Blueprint, request, jsonify
from app import db
from app.models import User
from app.utils import token_required

misc_bp = Blueprint("misc", __name__)


# ===========================================================================
# COMMAND INJECTION
# ===========================================================================

@misc_bp.route("/tools/ping", methods=["POST"])
@token_required
def ping_host():
    """Ping a host.

    VULNERABILITY: Command Injection - user input passed directly to os.popen().
    An attacker can chain commands using ;, |, &&, ||, $(), ``, etc.
    """
    data = request.get_json()
    if not data or not data.get("host"):
        return jsonify({"error": "Host is required. Send {\"host\": \"example.com\"}"}), 400

    host = data["host"]

    # VULNERABILITY: No input sanitization - direct command injection
    try:
        # Using os.popen which is vulnerable to command injection
        cmd = f"ping -c 2 {host}"
        result = os.popen(cmd).read()

        return jsonify({
            "command": cmd,
            "output": result,
            "status": "completed",
        }), 200
    except Exception as e:
        return jsonify({
            "error": f"Command failed: {str(e)}",
            "command": cmd,
        }), 500


@misc_bp.route("/tools/dns-lookup", methods=["POST"])
@token_required
def dns_lookup():
    """DNS lookup for a domain.

    VULNERABILITY: Command Injection via subprocess with shell=True.
    """
    data = request.get_json()
    if not data or not data.get("domain"):
        return jsonify({"error": "Domain is required. Send {\"domain\": \"example.com\"}"}), 400

    domain = data["domain"]

    # VULNERABILITY: shell=True with unsanitized input
    try:
        cmd = f"nslookup {domain}"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)

        return jsonify({
            "command": cmd,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
        }), 200
    except subprocess.TimeoutExpired:
        return jsonify({"error": "Command timed out"}), 504
    except Exception as e:
        return jsonify({"error": f"Lookup failed: {str(e)}"}), 500


# ===========================================================================
# NOSQL-STYLE INJECTION (Simulated with JSON query parsing)
# ===========================================================================

@misc_bp.route("/tools/user-lookup", methods=["POST"])
@token_required
def user_lookup():
    """Look up users using a flexible query system.

    VULNERABILITY: NoSQL-style injection via JSON operators.
    Accepts MongoDB-like operators ($gt, $ne, $regex, $exists) in the query.
    This simulates NoSQL injection in a SQL database by interpreting
    JSON operators and building queries from them.

    Example legitimate request:
        {"username": "alice"}

    Example injection:
        {"username": {"$ne": ""}}           -- returns all users (not equal to empty)
        {"username": {"$regex": ".*"}}      -- returns all users (regex match all)
        {"role": {"$eq": "admin"}}          -- find admin users
        {"id": {"$gt": 0}}                 -- returns all users with id > 0
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "Query is required. Send {\"username\": \"alice\"} or use operators like {\"username\": {\"$ne\": \"\"}}"}), 400

    try:
        query = User.query

        for field, condition in data.items():
            # Check if the field exists on User model
            if not hasattr(User, field):
                continue

            column = getattr(User, field)

            if isinstance(condition, dict):
                # VULNERABILITY: Process MongoDB-like operators without restriction
                for operator, value in condition.items():
                    if operator == "$eq":
                        query = query.filter(column == value)
                    elif operator == "$ne":
                        # $ne: not equal - can be used to return all records
                        query = query.filter(column != value)
                    elif operator == "$gt":
                        query = query.filter(column > value)
                    elif operator == "$lt":
                        query = query.filter(column < value)
                    elif operator == "$gte":
                        query = query.filter(column >= value)
                    elif operator == "$lte":
                        query = query.filter(column <= value)
                    elif operator == "$regex":
                        # VULNERABILITY: regex matching
                        query = query.filter(column.like(f"%{value}%"))
                    elif operator == "$exists":
                        if value:
                            query = query.filter(column.isnot(None))
                        else:
                            query = query.filter(column.is_(None))
                    elif operator == "$in":
                        if isinstance(value, list):
                            query = query.filter(column.in_(value))
            else:
                # Direct equality match
                query = query.filter(column == condition)

        users = query.all()

        # VULNERABILITY: Returns too much data
        return jsonify({
            "query": data,
            "count": len(users),
            "results": [u.to_private_dict() for u in users],
        }), 200

    except Exception as e:
        return jsonify({
            "error": f"Query failed: {str(e)}",
            "query": data,
        }), 500


# ===========================================================================
# WEBHOOK REGISTRATION (SSRF variant)
# ===========================================================================

# In-memory webhook storage
_webhooks = {}
_webhook_counter = 0


@misc_bp.route("/webhook/register", methods=["POST"])
@token_required
def register_webhook():
    """Register a webhook URL.

    VULNERABILITY: SSRF variant - stores arbitrary URLs that will be called server-side.
    No URL validation, no domain allowlisting.
    """
    global _webhook_counter

    data = request.get_json()
    if not data or not data.get("url"):
        return jsonify({"error": "URL is required. Send {\"url\": \"https://your-server.com/hook\", \"events\": [\"post.created\", \"user.followed\"]}"}), 400

    url = data["url"]
    events = data.get("events", ["all"])

    # VULNERABILITY: No URL validation
    _webhook_counter += 1
    webhook_id = _webhook_counter

    _webhooks[webhook_id] = {
        "id": webhook_id,
        "url": url,
        "events": events,
        "user_id": request.current_user_id,
        "active": True,
    }

    return jsonify({
        "message": "Webhook registered",
        "webhook": _webhooks[webhook_id],
    }), 201


@misc_bp.route("/webhook/test/<int:webhook_id>", methods=["POST"])
@token_required
def test_webhook(webhook_id):
    """Test a registered webhook by sending a test payload.

    VULNERABILITY: SSRF - server makes request to the registered URL.
    No ownership check (BOLA) - any user can trigger any webhook.
    """
    import requests as http_requests

    webhook = _webhooks.get(webhook_id)
    if not webhook:
        return jsonify({"error": "Webhook not found"}), 404

    # VULNERABILITY: No ownership check - BOLA
    # VULNERABILITY: Server makes request to arbitrary URL
    test_payload = {
        "event": "test",
        "timestamp": __import__("datetime").datetime.now().isoformat(),
        "data": {"message": "Test webhook delivery"},
    }

    try:
        response = http_requests.post(
            webhook["url"],
            json=test_payload,
            timeout=5,
            allow_redirects=True,
        )

        return jsonify({
            "message": "Webhook test sent",
            "webhook_url": webhook["url"],
            "response_status": response.status_code,
            "response_body": response.text[:2000],
        }), 200
    except Exception as e:
        return jsonify({
            "error": f"Webhook delivery failed: {str(e)}",
            "webhook_url": webhook["url"],
        }), 500


@misc_bp.route("/webhook/list", methods=["GET"])
@token_required
def list_webhooks():
    """List all registered webhooks.

    VULNERABILITY: Returns ALL webhooks, not just the current user's.
    """
    # VULNERABILITY: No filtering by user - returns all webhooks (info disclosure)
    return jsonify({
        "total": len(_webhooks),
        "webhooks": list(_webhooks.values()),
    }), 200


# ===========================================================================
# HPP / CONTENT-TYPE CONFUSION (v2.0 book, Chapter 17.5)
# ===========================================================================

@misc_bp.route("/tools/report", methods=["GET", "POST"])
@token_required
def generate_report():
    """Generate an account report.

    VULNERABILITY: HTTP Parameter Pollution + Content-Type Confusion.
    A "gateway policy" (simulated inline - see the honest simplification
    note below) is supposed to block scope=all from untrusted callers,
    but:

    1. HPP - the policy validates only the FIRST 'scope' parameter while
       this handler acts on the LAST one (?scope=me&scope=all passes).
    2. Content-Type Confusion - the policy inspects application/json
       bodies only; the same field sent as form-urlencoded is parsed by
       the backend but never seen by the policy.

    SIMPLIFICATION (like routes/gateway_internal.py): there is only ONE
    HTTP parser here (Werkzeug), so the "policy view" is simulated by
    deliberately reading the first duplicate / json-only body. A real
    deployment has two independent parsers disagreeing - same bug class.
    """
    # --- what the simulated gateway policy sees ---
    raw_pairs = [p.split("=", 1) for p in request.query_string.decode().split("&") if "=" in p]
    query_scopes = [v for k, v in raw_pairs if k == "scope"]

    content_type = request.content_type or ""
    if request.is_json:
        body_scope = (request.get_json(silent=True) or {}).get("scope")
        policy_inspects_body = True
    elif "form-urlencoded" in content_type:
        body_scope = request.form.get("scope")
        policy_inspects_body = False          # ❌ form bodies are never inspected
    else:
        body_scope = None
        policy_inspects_body = False

    # Policy decision: based on FIRST query value + JSON body only
    policy_visible_scopes = []
    if query_scopes:
        policy_visible_scopes.append(query_scopes[0])     # ❌ ignores duplicates
    if policy_inspects_body and body_scope:
        policy_visible_scopes.append(body_scope)

    # --- what the handler actually acts on ---
    # ❌ VULNERABILITY: LAST duplicate wins inside the handler
    if query_scopes:
        effective_scope = query_scopes[-1]
    elif body_scope:
        effective_scope = body_scope
    else:
        effective_scope = "me"

    policy_blocked = any(s == "all" for s in policy_visible_scopes)
    if policy_blocked and effective_scope == "all":
        return jsonify({"error": "scope=all is not allowed for your role"}), 403

    if effective_scope == "all":
        # 🚩 Bypassed: full user directory leak
        users = User.query.all()
        return jsonify({
            "report_type": "full_directory",
            "bypass": {
                "gateway_policy_saw": policy_visible_scopes or ["(nothing)"],
                "handler_actually_used": effective_scope,
                "content_type_inspected_by_policy": policy_inspects_body,
            },
            "count": len(users),
            "users": [{"id": u.id, "username": u.username, "email": u.email} for u in users],
        }), 200

    return jsonify({
        "report_type": "own_account_summary",
        "note": "Try ?scope=me&scope=all (HPP) or send scope=all as "
                "application/x-www-form-urlencoded (content-type confusion).",
        "user_id": request.current_user_id,
    }), 200
