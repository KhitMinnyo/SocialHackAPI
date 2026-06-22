"""Authentication utilities with intentional vulnerabilities."""

import jwt
import bcrypt
import base64
import time
from functools import wraps
from flask import request, jsonify, current_app


def hash_password(password):
    """Hash a password using bcrypt."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def check_password(password, password_hash):
    """Verify a password against a hash."""
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def generate_token(user_id, role="user"):
    """Generate a JWT token.

    VULNERABILITY: Weak secret key, long expiry, role in payload can be tampered.
    """
    payload = {
        "user_id": user_id,
        "role": role,
        "iat": int(time.time()),
        "exp": int(time.time()) + current_app.config["JWT_ACCESS_TOKEN_EXPIRES"],
    }
    return jwt.encode(
        payload,
        current_app.config["JWT_SECRET_KEY"],
        algorithm=current_app.config["JWT_ALGORITHM"],
    )


def decode_token(token):
    """Decode a JWT token.

    VULNERABILITY: Accepts 'none' algorithm, doesn't properly validate.
    """
    try:
        # VULNERABILITY: accepts multiple algorithms including 'none'
        payload = jwt.decode(
            token,
            current_app.config["JWT_SECRET_KEY"],
            algorithms=["HS256", "none"],
        )
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def generate_reset_token(username):
    """Generate a password reset token.

    VULNERABILITY: Predictable token - just base64(username:timestamp).
    """
    timestamp = int(time.time())
    raw = f"{username}:{timestamp}"
    return base64.b64encode(raw.encode()).decode()


def decode_reset_token(token):
    """Decode a password reset token."""
    try:
        raw = base64.b64decode(token.encode()).decode()
        username, timestamp = raw.rsplit(":", 1)
        # Token valid for 1 hour
        if int(time.time()) - int(timestamp) > 3600:
            return None
        return username
    except Exception:
        return None


def token_required(f):
    """Decorator that requires a valid JWT token.

    VULNERABILITY: Only checks token validity, doesn't re-verify user exists or role.
    """

    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        # Check Authorization header
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header.split(" ", 1)[1]

        if not token:
            return jsonify({"error": "Authentication token is missing"}), 401

        payload = decode_token(token)
        if payload is None:
            return jsonify({"error": "Invalid or expired token"}), 401

        # VULNERABILITY: We trust the role from the JWT payload without checking DB
        request.current_user_id = payload.get("user_id")
        request.current_user_role = payload.get("role", "user")

        return f(*args, **kwargs)

    return decorated


def admin_required(f):
    """Decorator that requires admin role.

    VULNERABILITY: Only checks JWT payload role, not the actual database role.
    """

    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header.split(" ", 1)[1]

        if not token:
            return jsonify({"error": "Authentication token is missing"}), 401

        payload = decode_token(token)
        if payload is None:
            return jsonify({"error": "Invalid or expired token"}), 401

        request.current_user_id = payload.get("user_id")
        request.current_user_role = payload.get("role", "user")

        # VULNERABILITY: Checks role from JWT, not from database
        # An attacker who forges a JWT with role=admin can bypass this
        if request.current_user_role != "admin":
            return jsonify({"error": "Admin access required"}), 403

        return f(*args, **kwargs)

    return decorated
