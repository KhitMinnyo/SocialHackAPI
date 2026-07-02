"""Promotions routes with intentional vulnerabilities.

OWASP API6:2023 - Unrestricted Access to Sensitive Business Flows

This module exposes a "verified badge" business flow. In a real platform,
granting the verified badge involves human review (identity checks,
notability, etc). Here the flow is fully automated and has NO protection
against being driven by scripts/bots:

- No CAPTCHA / proof-of-humanity
- No per-account cooldown or limit on how many times the flow can be invoked
- No device/IP fingerprinting or velocity checks
- The eligibility rule itself (follower count) can be gamed because the
  /users/:id/follow endpoint (see users.py) has no rate limiting either,
  so an attacker can script mass account creation + mass following to
  satisfy the "eligibility" check and then instantly claim the badge.
"""

from flask import Blueprint, request, jsonify
from app import db
from app.models import User
from app.utils import token_required

promotions_bp = Blueprint("promotions", __name__)

# VULNERABILITY: Business rule threshold is trivially low and there is no
# check for *who* the followers are (bot accounts count just as much as
# real ones).
VERIFIED_BADGE_FOLLOWER_THRESHOLD = 5


@promotions_bp.route("/promotions/verification/eligibility", methods=["GET"])
@token_required
def check_eligibility():
    """Check whether the current user is eligible for the verified badge."""
    user = User.query.get(request.current_user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    followers_count = user.followers_list.count()
    eligible = followers_count >= VERIFIED_BADGE_FOLLOWER_THRESHOLD

    return jsonify({
        "username": user.username,
        "followers_count": followers_count,
        "required_followers": VERIFIED_BADGE_FOLLOWER_THRESHOLD,
        "eligible": eligible,
        "already_verified": user.is_verified,
    }), 200


@promotions_bp.route("/promotions/verification/apply", methods=["POST"])
@token_required
def apply_verified_badge():
    """Apply for the verified badge.

    VULNERABILITY (API6:2023 - Unrestricted Access to Sensitive Business Flows):
    - Fully automated approval, no human-in-the-loop review.
    - No rate limiting: can be called repeatedly with no cooldown.
    - No bot/fraud detection on the followers used to satisfy eligibility.
    - No re-verification that followers are genuine/unique real users.

    This lets an attacker script the entire flow end-to-end:
        1. POST /api/v1/auth/register  x N   (create bot accounts, no CAPTCHA/email verification)
        2. POST /api/v1/users/:id/follow      (bot accounts follow the target account)
        3. POST /api/v1/promotions/verification/apply  (instantly get verified=True)
    """
    user = User.query.get(request.current_user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    if user.is_verified:
        return jsonify({"message": "User is already verified", "is_verified": True}), 200

    followers_count = user.followers_list.count()

    # VULNERABILITY: No check on WHO the followers are, no CAPTCHA, no
    # manual review queue, no per-user cooldown before re-applying.
    if followers_count < VERIFIED_BADGE_FOLLOWER_THRESHOLD:
        return jsonify({
            "error": "Not eligible yet",
            "followers_count": followers_count,
            "required_followers": VERIFIED_BADGE_FOLLOWER_THRESHOLD,
        }), 403

    user.is_verified = True
    db.session.commit()

    return jsonify({
        "message": "Congratulations! Your account is now verified.",
        "username": user.username,
        "is_verified": user.is_verified,
        "followers_count": followers_count,
    }), 200


@promotions_bp.route("/promotions/verification/revoke/<int:user_id>", methods=["POST"])
@token_required
def revoke_badge_self_service(user_id):
    """Self-service badge revocation (meant for a user to remove their own badge).

    VULNERABILITY: BOLA - no check that the caller owns user_id. Also usable
    for harassment (revoking someone else's badge) which is itself a
    business-flow abuse.
    """
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    # VULNERABILITY: No ownership check - request.current_user_id is never compared to user_id
    user.is_verified = False
    db.session.commit()

    return jsonify({"message": f"Verified badge revoked for '{user.username}'"}), 200
