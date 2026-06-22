"""Admin routes with intentional vulnerabilities."""

from flask import Blueprint, jsonify
from app import db
from app.models import User, Post, Comment, Message, Like
from app.utils import token_required

admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/users", methods=["GET"])
@token_required
def list_all_users():
    """List all users (admin only).

    VULNERABILITY: Broken Function Level Authorization
    Only checks for valid JWT, doesn't verify admin role from database.
    A regular user with a valid token can access this by forging JWT role.
    """
    # VULNERABILITY: Uses role from JWT payload, not database
    # The @token_required decorator sets request.current_user_role from JWT
    # But we're NOT using @admin_required here - just @token_required
    # So ANY authenticated user can access this
    users = User.query.all()

    return jsonify({
        "total_users": len(users),
        "users": [user.to_full_dict() for user in users],  # VULNERABILITY: Exposes EVERYTHING
    }), 200


@admin_bp.route("/users/<int:user_id>", methods=["DELETE"])
@token_required
def admin_delete_user(user_id):
    """Delete a user (admin only).

    VULNERABILITY: Broken Function Level Authorization - no role check.
    """
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    # VULNERABILITY: No admin role verification
    username = user.username
    db.session.delete(user)
    db.session.commit()

    return jsonify({
        "message": f"User '{username}' has been deleted by admin",
    }), 200


@admin_bp.route("/stats", methods=["GET"])
@token_required
def platform_stats():
    """Get platform statistics (admin only).

    VULNERABILITY: Broken Function Level Authorization - no role check.
    Exposes internal platform metrics.
    """
    # VULNERABILITY: No admin role check
    stats = {
        "total_users": User.query.count(),
        "total_posts": Post.query.count(),
        "total_comments": Comment.query.count(),
        "total_messages": Message.query.count(),
        "total_likes": Like.query.count(),
        "admin_users": User.query.filter_by(role="admin").count(),
        "moderator_users": User.query.filter_by(role="moderator").count(),
        "verified_users": User.query.filter_by(is_verified=True).count(),
        "private_accounts": User.query.filter_by(is_private=True).count(),
        "public_posts": Post.query.filter_by(is_public=True).count(),
        "private_posts": Post.query.filter_by(is_public=False).count(),
        # VULNERABILITY: Exposing database info
        "database_tables": ["users", "posts", "comments", "messages", "likes", "followers"],
        "server_info": {
            "framework": "Flask",
            "database": "SQLite",
            "auth": "JWT (HS256)",
        },
    }

    return jsonify(stats), 200


@admin_bp.route("/users/<int:user_id>/role", methods=["PUT"])
@token_required
def change_user_role(user_id):
    """Change a user's role (admin only).

    VULNERABILITY: No admin role verification.
    """
    from flask import request

    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    data = request.get_json()
    if not data or "role" not in data:
        return jsonify({"error": "Role is required"}), 400

    new_role = data["role"]
    if new_role not in ("user", "admin", "moderator"):
        return jsonify({"error": "Invalid role. Must be: user, admin, or moderator"}), 400

    old_role = user.role
    user.role = new_role
    db.session.commit()

    return jsonify({
        "message": f"User '{user.username}' role changed from '{old_role}' to '{new_role}'",
    }), 200
