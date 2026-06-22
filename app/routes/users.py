"""User routes with intentional vulnerabilities."""

from flask import Blueprint, request, jsonify
from app import db
from app.models import User
from app.utils import token_required

users_bp = Blueprint("users", __name__)


@users_bp.route("/<int:user_id>", methods=["GET"])
@token_required
def get_user(user_id):
    """Get user profile.

    VULNERABILITY: BOLA - any authenticated user can view any profile,
    including private profiles. Returns too much data.
    """
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    # VULNERABILITY: No check if requesting user has permission to view this profile
    # VULNERABILITY: Returns private data regardless of is_private setting
    return jsonify({"user": user.to_private_dict()}), 200


@users_bp.route("/<int:user_id>", methods=["PUT"])
@token_required
def update_user(user_id):
    """Update user profile.

    VULNERABILITY: BOLA - can update any user's profile, not just own.
    VULNERABILITY: Mass Assignment - can change role, is_verified, etc.
    """
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    # VULNERABILITY: No check if current user owns this profile
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body is required"}), 400

    # VULNERABILITY: Mass assignment - accepts ALL fields
    for key, value in data.items():
        if hasattr(user, key) and key not in ("id", "password_hash", "created_at"):
            setattr(user, key, value)

    db.session.commit()

    return jsonify({
        "message": "Profile updated successfully",
        "user": user.to_private_dict(),
    }), 200


@users_bp.route("/<int:user_id>", methods=["DELETE"])
@token_required
def delete_user(user_id):
    """Delete user account.

    VULNERABILITY: BOLA - can delete any user's account.
    """
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    # VULNERABILITY: No ownership check
    db.session.delete(user)
    db.session.commit()

    return jsonify({"message": f"User '{user.username}' deleted successfully"}), 200


@users_bp.route("/search", methods=["GET"])
@token_required
def search_users():
    """Search users.

    VULNERABILITY: SQL Injection - raw query with user input.
    """
    query = request.args.get("q", "")

    if not query:
        return jsonify({"error": "Search query 'q' is required"}), 400

    # VULNERABILITY: SQL Injection - using raw SQL with string formatting
    try:
        sql = f"SELECT id, username, email, bio, role, is_verified FROM users WHERE username LIKE '%{query}%' OR bio LIKE '%{query}%'"
        result = db.session.execute(db.text(sql))
        users = []
        for row in result:
            users.append({
                "id": row[0],
                "username": row[1],
                "email": row[2],
                "bio": row[3],
                "role": row[4],
                "is_verified": row[5],
            })
        return jsonify({"users": users, "count": len(users)}), 200
    except Exception as e:
        # VULNERABILITY: Returns full error message including SQL details
        return jsonify({"error": f"Search failed: {str(e)}"}), 500


@users_bp.route("/<int:user_id>/followers", methods=["GET"])
@token_required
def get_followers(user_id):
    """Get user's followers.

    VULNERABILITY: Returns follower details for private accounts.
    """
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    # VULNERABILITY: No privacy check - shows followers even for private accounts
    followers = user.followers_list.all()

    return jsonify({
        "user": user.username,
        "followers_count": len(followers),
        "followers": [f.to_private_dict() for f in followers],
    }), 200


@users_bp.route("/<int:user_id>/following", methods=["GET"])
@token_required
def get_following(user_id):
    """Get who a user follows."""
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    following = user.followed.all()

    return jsonify({
        "user": user.username,
        "following_count": len(following),
        "following": [f.to_dict() for f in following],
    }), 200


@users_bp.route("/<int:user_id>/follow", methods=["POST"])
@token_required
def follow_user(user_id):
    """Follow a user."""
    user_to_follow = User.query.get(user_id)
    if not user_to_follow:
        return jsonify({"error": "User not found"}), 404

    current_user = User.query.get(request.current_user_id)
    if not current_user:
        return jsonify({"error": "Current user not found"}), 404

    if current_user.id == user_to_follow.id:
        return jsonify({"error": "Cannot follow yourself"}), 400

    if user_to_follow in current_user.followed.all():
        return jsonify({"error": "Already following this user"}), 400

    current_user.followed.append(user_to_follow)
    db.session.commit()

    return jsonify({"message": f"Now following {user_to_follow.username}"}), 200


@users_bp.route("/<int:user_id>/unfollow", methods=["POST"])
@token_required
def unfollow_user(user_id):
    """Unfollow a user."""
    user_to_unfollow = User.query.get(user_id)
    if not user_to_unfollow:
        return jsonify({"error": "User not found"}), 404

    current_user = User.query.get(request.current_user_id)
    if not current_user:
        return jsonify({"error": "Current user not found"}), 404

    if user_to_unfollow not in current_user.followed.all():
        return jsonify({"error": "Not following this user"}), 400

    current_user.followed.remove(user_to_unfollow)
    db.session.commit()

    return jsonify({"message": f"Unfollowed {user_to_unfollow.username}"}), 200
