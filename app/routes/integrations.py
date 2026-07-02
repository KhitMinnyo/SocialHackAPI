"""Third-party integration routes with intentional vulnerabilities.

OWASP API10:2023 - Unsafe Consumption of APIs

Developers usually treat data coming FROM a partner/third-party API as
trusted, because the request itself is "outbound" and the connection was
initiated by our own server. That assumption is the bug: whoever controls
the content at the far end of that URL controls the data that flows back
into our system.

This is deliberately different from SSRF (API7, see routes/upload.py and
routes/misc.py webhook endpoints): SSRF is about the server being tricked
into making a request it shouldn't. API10 here is about the server making
an *intentional* request to a *configurable* partner endpoint and then
blindly trusting/parsing whatever JSON comes back - no schema validation,
no allow-listed domains, no TLS verification, and (worst of all) the
response fields are mass-assigned straight onto the local user record.
"""

import requests as http_requests
from flask import Blueprint, request, jsonify
from app import db
from app.models import User
from app.utils import token_required

integrations_bp = Blueprint("integrations", __name__)

# VULNERABILITY: No allow-list of trusted partner domains - any URL the
# caller supplies is fetched and trusted.
ALLOWED_PARTNER_DOMAINS = None  # intentionally not enforced


@integrations_bp.route("/integrations/import-profile", methods=["POST"])
@token_required
def import_profile_from_partner():
    """Import profile data from a 'partner' identity-verification API.

    Legitimate use case: a partner KYC/identity service returns verified
    profile attributes (bio, avatar, verification status) that we display
    on the user's profile.

    VULNERABILITY (API10:2023 - Unsafe Consumption of APIs):
    - The partner URL is fully attacker-controlled (no domain allow-list).
    - The response is trusted without schema/type validation.
    - Response fields are mass-assigned directly onto the User model -
      including sensitive fields like `role` and `is_verified` - so a
      malicious/attacker-run "partner API" can grant itself admin rights
      on the caller's account just by returning
      {"role": "admin", "is_verified": true} in its JSON response.
    - Redirects are followed automatically (allow_redirects=True) without
      re-validating the final destination.
    - No timeout-independent size limit - a huge response body is parsed
      into memory in full.
    """
    data = request.get_json()
    if not data or not data.get("source_url"):
        return jsonify({
            "error": "source_url is required. "
                     "Send {\"source_url\": \"http://your-mock-partner-api/profile.json\"}"
        }), 400

    source_url = data["source_url"]
    user = User.query.get(request.current_user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    try:
        # VULNERABILITY: No domain allow-list check on source_url before requesting it.
        resp = http_requests.get(source_url, timeout=5, allow_redirects=True)
    except Exception as e:
        return jsonify({"error": f"Failed to reach partner API: {str(e)}"}), 502

    if resp.status_code != 200:
        return jsonify({"error": f"Partner API returned HTTP {resp.status_code}"}), 502

    try:
        partner_data = resp.json()
    except ValueError:
        return jsonify({"error": "Partner API did not return valid JSON"}), 502

    if not isinstance(partner_data, dict):
        return jsonify({"error": "Partner API response must be a JSON object"}), 502

    # VULNERABILITY: Blind trust - every field the "partner" returns is
    # applied directly to the local user record with no schema, no type
    # checking, and no field allow-list. This is mass assignment driven by
    # EXTERNAL, attacker-controllable data rather than the request body.
    applied_fields = {}
    for key, value in partner_data.items():
        if hasattr(user, key) and key not in ("id", "password_hash", "created_at"):
            setattr(user, key, value)
            applied_fields[key] = value

    db.session.commit()

    return jsonify({
        "message": "Profile imported from partner API",
        "source_url": source_url,
        "fields_applied_from_partner": applied_fields,
        "user": user.to_private_dict(),
    }), 200


@integrations_bp.route("/integrations/exchange-rate", methods=["GET"])
@token_required
def get_exchange_rate():
    """Fetch a currency exchange rate from a configurable third-party API.

    VULNERABILITY: The 'provider' URL is caller-supplied and the numeric
    'rate' field from the response is trusted and echoed back with no
    bounds checking (e.g. no sanity range check, no type enforcement) -
    in a real app this kind of unchecked value often flows into pricing or
    financial calculations downstream.
    """
    provider_url = request.args.get("provider")
    if not provider_url:
        return jsonify({
            "error": "provider query param is required, e.g. "
                     "?provider=http://your-mock-provider/rate.json"
        }), 400

    try:
        resp = http_requests.get(provider_url, timeout=5, allow_redirects=True)
        payload = resp.json()
    except Exception as e:
        return jsonify({"error": f"Failed to reach provider: {str(e)}"}), 502

    # VULNERABILITY: No validation that 'rate' is a sane numeric value
    # within an expected range before trusting/using it.
    return jsonify({
        "provider": provider_url,
        "raw_response": payload,
        "rate": payload.get("rate") if isinstance(payload, dict) else None,
    }), 200
