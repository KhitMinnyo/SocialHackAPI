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
