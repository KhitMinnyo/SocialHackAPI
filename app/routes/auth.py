"""Authentication routes with intentional vulnerabilities."""

from flask import Blueprint, request, jsonify
from app import db
from app.models import User
from app.utils import (
    hash_password,
    check_password,
    generate_token,
    generate_reset_token,
    decode_reset_token,
    token_required,
)

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["POST"])
def register():
    """Register a new user.

    VULNERABILITY: Mass Assignment - accepts role, is_verified, and other fields directly.
    """
    data = request.get_json()

    if not data:
        return jsonify({"error": "Request body is required"}), 400

    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    if not username or not email or not password:
        return jsonify({"error": "Username, email, and password are required"}), 400

    # Check if user exists - VULNERABILITY: Verbose error messages
    if User.query.filter_by(username=username).first():
        return jsonify({"error": f"Username '{username}' is already taken"}), 409

    if User.query.filter_by(email=email).first():
        return jsonify({"error": f"Email '{email}' is already registered"}), 409

    # VULNERABILITY: Mass assignment - all fields from request body are accepted
    new_user = User(
        username=username,
        email=email,
        password_hash=hash_password(password),
        bio=data.get("bio", ""),
        profile_pic=data.get("profile_pic", ""),
        role=data.get("role", "user"),  # VULNERABILITY: Role can be set by user
        is_verified=data.get("is_verified", False),  # VULNERABILITY: Can self-verify
        is_private=data.get("is_private", False),
    )

    db.session.add(new_user)
    db.session.commit()

    token = generate_token(new_user.id, new_user.role)

    return jsonify({
        "message": "User registered successfully",
        "user": new_user.to_private_dict(),  # VULNERABILITY: Returns too much data
        "token": token,
    }), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    """Login user.

    VULNERABILITY: No rate limiting, verbose error messages.
    """
    data = request.get_json()

    if not data:
        return jsonify({"error": "Request body is required"}), 400

    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    user = User.query.filter_by(username=username).first()

    # VULNERABILITY: Different error messages for invalid username vs invalid password
    if not user:
        return jsonify({"error": f"User '{username}' not found"}), 404

    if not check_password(password, user.password_hash):
        return jsonify({"error": "Incorrect password"}), 401

    # Update login stats
    user.login_count += 1
    user.last_login_ip = request.remote_addr
    db.session.commit()

    token = generate_token(user.id, user.role)

    return jsonify({
        "message": "Login successful",
        "user": user.to_private_dict(),  # VULNERABILITY: Excessive data
        "token": token,
    }), 200


@auth_bp.route("/reset-password", methods=["POST"])
def reset_password():
    """Request password reset.

    VULNERABILITY: Predictable reset token (base64 of username:timestamp).
    """
    data = request.get_json()

    if not data:
        return jsonify({"error": "Request body is required"}), 400

    email = data.get("email")
    if not email:
        return jsonify({"error": "Email is required"}), 400

    user = User.query.filter_by(email=email).first()

    # VULNERABILITY: Different response for existing vs non-existing email
    if not user:
        return jsonify({"error": f"No account found with email '{email}'"}), 404

    # VULNERABILITY: Predictable token
    reset_token = generate_reset_token(user.username)
    user.reset_token = reset_token
    db.session.commit()

    # In a real app, this would be sent via email
    # VULNERABILITY: Token returned directly in response
    return jsonify({
        "message": "Password reset token generated",
        "reset_token": reset_token,
        "note": "In production, this would be sent to your email",
    }), 200


@auth_bp.route("/reset-password/confirm", methods=["POST"])
def confirm_reset():
    """Confirm password reset with token."""
    data = request.get_json()

    if not data:
        return jsonify({"error": "Request body is required"}), 400

    token = data.get("token")
    new_password = data.get("new_password")

    if not token or not new_password:
        return jsonify({"error": "Token and new_password are required"}), 400

    username = decode_reset_token(token)
    if not username:
        return jsonify({"error": "Invalid or expired reset token"}), 400

    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    user.password_hash = hash_password(new_password)
    user.reset_token = None
    db.session.commit()

    return jsonify({"message": "Password reset successful"}), 200


@auth_bp.route("/refresh", methods=["POST"])
@token_required
def refresh_token():
    """Refresh JWT token.

    VULNERABILITY: Generates new token with role from current JWT (not DB).
    """
    token = generate_token(request.current_user_id, request.current_user_role)

    return jsonify({
        "message": "Token refreshed",
        "token": token,
    }), 200
