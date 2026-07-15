"""Mock mobile-app config endpoints with intentional vulnerabilities.

"Beyond the Lab" extension — teaches the "secrets in the client" problem without
shipping a real APK. A mobile app ships its configuration/secrets INSIDE the
distributed binary; anyone can extract them. These endpoints simulate what a
reverse-engineer would recover from `apktool d app.apk` (strings.xml,
BuildConfig, bundled config JSON) and from the app's own runtime config fetch.

VULNERABILITIES:
1. Hardcoded secrets shipped to every client: API keys, the OAuth mobile
   client_secret (same value trusted by app/routes/oauth.py!), and a master
   fallback key. "Confidential" secrets embedded in a public client are not
   confidential.
2. Client-trusted feature flags / roles: the config tells the client it is not
   an admin, but nothing server-side enforces that (the real controls are the
   API's, which are themselves broken - see the BFLA lab).
3. No certificate pinning advertised -> traffic is interceptable (Burp), which
   is how you'd capture the /api/v1/* calls in the first place.
"""

from flask import Blueprint, jsonify, Response

mobile_bp = Blueprint("mobile", __name__)

# VULNERABILITY: secrets embedded in the shipped mobile client. The
# oauth_client_secret here is the SAME value app/routes/oauth.py trusts, so
# extracting it from the "app" lets an attacker impersonate the official client.
_MOBILE_CONFIG = {
    "app": "SocialHack Mobile",
    "version": "3.2.1",
    "api_base": "http://localhost:5001/api/v1",
    "oauth_client_id": "socialhack-mobile",
    "oauth_client_secret": "mobile_client_secret_9a8b7c6d",   # VULN: shipped secret
    "analytics_api_key": "ak_mobile_analytics_7z8y9x",         # VULN
    "master_fallback_key": "ak_admin_MASTER_KEY_x9z8y7",       # VULN: same as admin!
    "feature_flags": {
        "is_admin_build": False,        # VULN: client-side only, not enforced
        "certificate_pinning": False,   # VULN: traffic interceptable
        "debug_menu_enabled": True,
    },
    "flag": "FLAG{hardcoded_secrets_in_the_mobile_client}",
}


@mobile_bp.route("/mobile/config", methods=["GET"])
def mobile_config():
    """Runtime config the mobile app fetches on launch - NO auth required."""
    return jsonify(_MOBILE_CONFIG), 200


@mobile_bp.route("/.well-known/mobile-config.json", methods=["GET"])
def wellknown_mobile_config():
    """Same config under a conventional well-known path (discoverable by fuzzing)."""
    return jsonify(_MOBILE_CONFIG), 200


@mobile_bp.route("/mobile/strings.xml", methods=["GET"])
def strings_xml():
    """Simulated Android res/values/strings.xml recovered from `apktool d`.

    VULNERABILITY: secrets committed into Android string resources - one of the
    most common real-world mobile findings.
    """
    body = (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        "<resources>\n"
        '    <string name="app_name">SocialHack</string>\n'
        '    <string name="api_base">http://localhost:5001/api/v1</string>\n'
        '    <string name="oauth_client_secret">mobile_client_secret_9a8b7c6d</string>\n'
        '    <string name="gmaps_api_key">AIzaSyD-EXAMPLE-mobile-maps-key-1234</string>\n'
        '    <string name="master_fallback_key">ak_admin_MASTER_KEY_x9z8y7</string>\n'
        "    <!-- FLAG{hardcoded_secrets_in_the_mobile_client} -->\n"
        "</resources>\n"
    )
    return Response(body, mimetype="application/xml")
