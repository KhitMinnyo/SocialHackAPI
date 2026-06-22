"""Input validators - intentionally weak."""


def validate_username(username):
    """Validate username format. Intentionally permissive."""
    if not username or len(username) < 1:
        return False, "Username is required"
    return True, ""


def validate_email(email):
    """Validate email format. Intentionally weak - only checks for @."""
    if not email or "@" not in email:
        return False, "Valid email is required"
    return True, ""


def validate_password(password):
    """Validate password. Intentionally weak - no complexity requirements."""
    if not password or len(password) < 1:
        return False, "Password is required"
    return True, ""


def sanitize_input(value):
    """Sanitize input. VULNERABILITY: Does nothing - pass-through."""
    return value
