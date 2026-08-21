"""OAuth2 / OIDC authorization-server routes with intentional vulnerabilities.

"Beyond the Lab" extension — teaches OAuth2 Authorization Code flow attacks that
the core REST/GraphQL/WebSocket labs don't cover. Self-contained: no external
identity provider required.

The resource owner (the "logged-in user") is identified for lab purposes by an
existing SocialHack JWT passed as ?token= or Authorization: Bearer. In a real
browser flow this would be the user's session cookie + a consent screen.

VULNERABILITIES (classic OAuth2 mistakes):
1. Loose redirect_uri validation (substring match, not exact) -> authorization
   code can be exfiltrated to an attacker-controlled URL (code theft).
2. `state` parameter is optional and never verified -> CSRF on the callback.
3. Authorization codes never expire and can be REPLAYED (reused) at the token
   endpoint.
4. Client authentication is not enforced at /oauth/token (client_secret
   optional) -> public-client confusion.
5. PKCE is accepted (code_challenge) but NEVER enforced at token exchange
   (code_verifier ignored) -> PKCE downgrade.
6. Requested scope is trusted blindly -> scope escalation (e.g. scope=admin).
7. The issued access_token is a full SocialHack API JWT (same weak secret as
   app/config.py) -> stealing a code yields complete account/API access, and the
   id_token is signed with the same brute-forceable secret (ties to JWT lab).
"""

import time
import secrets
from flask import Blueprint, request, jsonify, redirect
from app.models import User
from app.utils import decode_token, generate_token
from flask import current_app
import jwt as pyjwt

oauth_bp = Blueprint("oauth", __name__)

# VULNERABILITY: registered clients; redirect_uris are validated only loosely below.
OAUTH_CLIENTS = {
    "socialhack-mobile": {
        "client_secret": "mobile_client_secret_9a8b7c6d",
        "redirect_uris": ["http://localhost:5001/app/oauth/callback"],
        "name": "SocialHack Official Mobile App",
    },
    # VULNERABILITY / lab narrative: any third party can get a client_id
    # registered here (there is no vetting step modeled in this lab) and
    # request whatever `scope` it likes at /authorize - see vulnerability #6
    # above ("Requested scope is trusted blindly"). This is the OAuth side of
    # the "malicious quiz app / bot" pattern real attackers use on platforms
    # like Facebook and Discord: the app LOOKS harmless, gets authorized with
    # an over-broad scope because there is no real consent screen, and the
    # resulting token has full API access regardless of what scope was
    # requested. See cheatsheets/beyond-lab-xss-oauth-cheatsheet.md for the
    # full walkthrough (through to spamming the victim's followers).
    "quizapp-fun-2000": {
        "client_secret": "quizapp_client_secret_leaked_00",
        "redirect_uris": ["https://quizapp-fun-2000.example/oauth/callback"],
        "name": '"Which SocialHack Personality Are You?" Quiz (unverified 3rd-party app)',
    },
}

# In-memory issued authorization codes: code -> metadata
_auth_codes = {}


def _current_owner_id():
    """Identify the consenting resource owner from an existing SocialHack JWT.

    Lab simplification: real OAuth would use the browser session + consent UI.
    """
    token = request.args.get("token")
    if not token:
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            token = auth.split(" ", 1)[1]
    if not token:
        return None
    payload = decode_token(token)
    if not payload:
        return None
    return payload.get("user_id")


def _redirect_uri_allowed(client, redirect_uri):
    """VULNERABILITY: substring match instead of exact match.

    A registered value merely needs to APPEAR somewhere in the supplied
    redirect_uri, so an attacker URL that *contains* the registered callback as
    a query parameter (or a look-alike host) passes validation, e.g.:
        http://evil.com/steal?next=http://localhost:5001/app/oauth/callback
    """
    return any(reg in redirect_uri for reg in client["redirect_uris"])


@oauth_bp.route("/oauth/authorize", methods=["GET"])
def authorize():
    client_id = request.args.get("client_id")
    redirect_uri = request.args.get("redirect_uri", "")
    response_type = request.args.get("response_type", "code")
    scope = request.args.get("scope", "profile")
    state = request.args.get("state")            # VULNERABILITY: optional, never verified
    code_challenge = request.args.get("code_challenge")  # PKCE: accepted, later ignored

    client = OAUTH_CLIENTS.get(client_id)
    if not client:
        return jsonify({"error": "invalid_client", "error_description": "Unknown client_id"}), 400

    if not redirect_uri or not _redirect_uri_allowed(client, redirect_uri):
        return jsonify({"error": "invalid_request", "error_description": "redirect_uri not allowed"}), 400

    if response_type != "code":
        return jsonify({"error": "unsupported_response_type"}), 400

    owner_id = _current_owner_id()
    if not owner_id:
        return jsonify({
            "error": "login_required",
            "error_description": "Provide a valid SocialHack JWT via ?token= or "
                                 "Authorization: Bearer to act as the consenting user.",
        }), 401

    # VULNERABILITY: short, no-expiry, replayable authorization code.
    code = secrets.token_hex(8)
    _auth_codes[code] = {
        "client_id": client_id,
        "user_id": owner_id,
        "redirect_uri": redirect_uri,
        "scope": scope,                 # VULNERABILITY: attacker-chosen scope trusted
        "code_challenge": code_challenge,
        "issued_at": time.time(),
        "used": False,
    }

    # Build the redirect back to the (attacker-controllable) redirect_uri.
    sep = "&" if "?" in redirect_uri else "?"
    location = f"{redirect_uri}{sep}code={code}"
    if state:
        location += f"&state={state}"

    # Debug/JSON mode so the lab is easily testable with curl (real flow 302s).
    if request.args.get("debug") == "1":
        return jsonify({
            "note": "In a real flow this is a 302 redirect to redirect_uri.",
            "redirect_to": location,
            "code": code,
            "scope": scope,
        }), 200

    return redirect(location, code=302)


@oauth_bp.route("/oauth/token", methods=["POST"])
def token():
    # Accept form or JSON, mirroring lenient real-world servers.
    data = request.get_json(silent=True) or request.form.to_dict() or request.args.to_dict()

    grant_type = data.get("grant_type", "authorization_code")
    code = data.get("code")
    redirect_uri = data.get("redirect_uri")
    client_id = data.get("client_id")
    client_secret = data.get("client_secret")     # VULNERABILITY: not enforced
    code_verifier = data.get("code_verifier")      # VULNERABILITY: never checked

    if grant_type != "authorization_code":
        return jsonify({"error": "unsupported_grant_type"}), 400

    entry = _auth_codes.get(code)
    if not entry:
        return jsonify({"error": "invalid_grant", "error_description": "Unknown code"}), 400

    # VULNERABILITY: code reuse allowed. A correct server would reject a code
    # whose `used` flag is already True (and delete it). Here we only note it.
    was_used = entry["used"]
    entry["used"] = True

    # VULNERABILITY: redirect_uri is NOT re-validated against the one used at
    # /authorize, and client_secret / PKCE code_verifier are ignored entirely.

    user = User.query.get(entry["user_id"])
    if not user:
        return jsonify({"error": "invalid_grant", "error_description": "User gone"}), 400

    # VULNERABILITY: the "access token" is a full SocialHack API JWT signed with
    # the same weak secret as the rest of the app -> whoever steals the code gets
    # complete API access as this user.
    access_token = generate_token(user.id, user.role)

    # OIDC id_token, signed with the same brute-forceable secret (ties to JWT lab).
    now = int(time.time())
    id_token = pyjwt.encode(
        {
            "iss": "http://localhost:5001",
            "sub": str(user.id),
            "aud": entry["client_id"],
            "name": user.username,
            "email": user.email,
            "role": user.role,
            "iat": now,
            "exp": now + 3600,
        },
        current_app.config["JWT_SECRET_KEY"],
        algorithm="HS256",
    )

    return jsonify({
        "access_token": access_token,
        "id_token": id_token,
        "token_type": "Bearer",
        "expires_in": 3600,
        "scope": entry["scope"],          # VULNERABILITY: echoes attacker-chosen scope
        "_lab_note_code_was_replayed": was_used,
        "_lab_note_client_secret_checked": False,
        "_lab_note_pkce_enforced": False,
    }), 200


@oauth_bp.route("/oauth/userinfo", methods=["GET"])
def userinfo():
    """OIDC-style userinfo endpoint.

    VULNERABILITY: accepts the access_token (a normal SocialHack JWT) and returns
    profile data with no scope enforcement.
    """
    auth = request.headers.get("Authorization", "")
    token_str = auth.split(" ", 1)[1] if auth.startswith("Bearer ") else request.args.get("access_token")
    payload = decode_token(token_str) if token_str else None
    if not payload:
        return jsonify({"error": "invalid_token"}), 401
    user = User.query.get(payload.get("user_id"))
    if not user:
        return jsonify({"error": "invalid_token"}), 401
    # VULNERABILITY: no scope check - returns sensitive fields regardless of scope
    return jsonify({
        "sub": str(user.id),
        "name": user.username,
        "email": user.email,
        "role": user.role,
        "api_key": user.api_key,
    }), 200
