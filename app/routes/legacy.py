"""Legacy / shadow API routes with intentional vulnerabilities.

OWASP API9:2023 - Improper Inventory Management

This blueprint simulates a "v0" API version that predates the current
"v1" API. It was supposed to be decommissioned when v1 shipped, but (as
happens all the time in real organizations) it was simply left running:

- It is NOT listed in the root "/" endpoint index (see app/__init__.py).
- It is NOT documented in README.md.
- It does NOT use @token_required at all - it predates the JWT-based auth
  system entirely, so none of the routes require authentication.
- It exposes the exact same underlying data as the v1 API, so any
  protection added to v1 (rate limiting, auth, filtering, etc.) does NOT
  apply here - it's a completely separate, unmonitored attack surface.

This is a very common real-world finding: old API versions, staging
endpoints, or internal-only routes that were never inventoried and never
decommissioned, and that quietly bypass every control added to the
"current" API.
"""

from flask import Blueprint, jsonify, request
from app.models import User, Post, Message

legacy_bp = Blueprint("legacy", __name__)


@legacy_bp.route("/users", methods=["GET"])
def legacy_list_users():
    """[UNDOCUMENTED / UNAUTHENTICATED] List all users - old v0 API.

    VULNERABILITY: No @token_required decorator at all. Anyone who
    discovers this endpoint (via fuzzing, old documentation, JS bundles,
    API gateway configs, etc.) can dump every user's full record without
    ever logging in.
    """
    users = User.query.all()
    return jsonify({
        "api_version": "v0 (deprecated 2019, never decommissioned)",
        "total": len(users),
        # VULNERABILITY: uses to_full_dict() - same excessive exposure as v1's admin panel,
        # but reachable with ZERO authentication.
        "users": [u.to_full_dict() for u in users],
    }), 200


@legacy_bp.route("/users/<int:user_id>", methods=["GET"])
def legacy_get_user(user_id):
    """[UNDOCUMENTED / UNAUTHENTICATED] Get a single user - old v0 API."""
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify({"user": user.to_full_dict()}), 200


@legacy_bp.route("/users/<int:user_id>", methods=["PUT"])
def legacy_update_user(user_id):
    """[UNDOCUMENTED / UNAUTHENTICATED] Update a user - old v0 API.

    VULNERABILITY: Unauthenticated mass assignment. Anyone can edit ANY
    field on ANY user (including role, is_verified, password_hash) without
    logging in at all.
    """
    from app import db

    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body is required"}), 400

    # VULNERABILITY: No auth, no allow-list - identical mass-assignment bug
    # as the v1 API, but nobody needs a token to trigger it here.
    for key, value in data.items():
        if hasattr(user, key) and key not in ("id",):
            setattr(user, key, value)

    db.session.commit()
    return jsonify({"message": "User updated (legacy v0 API)", "user": user.to_full_dict()}), 200


@legacy_bp.route("/export-all", methods=["GET"])
def legacy_export_all():
    """[UNDOCUMENTED / UNAUTHENTICATED] Full database dump - old v0 debug tool.

    VULNERABILITY: A leftover "internal debugging" endpoint from before the
    platform launched. Dumps users, posts and private messages in a single
    unauthenticated request.
    """
    return jsonify({
        "api_version": "v0-internal",
        "warning": "FOR INTERNAL USE ONLY - remove before launch (this note was never actioned)",
        "users": [u.to_full_dict() for u in User.query.all()],
        "posts": [p.to_dict() for p in Post.query.all()],
        # VULNERABILITY: private direct messages dumped with no auth check
        "messages": [m.to_dict() for m in Message.query.all()],
    }), 200
