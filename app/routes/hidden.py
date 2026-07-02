"""Hidden/undocumented endpoints — targets for wordlist-based fuzzing practice.

These routes exist purely so ffuf/gobuster/dirsearch-style tools have
something genuine to find. Unlike the debug endpoint (/api/v1/debug) or the
leaked OpenAPI spec (/openapi.json), these paths are:

- NOT listed in the root "/" endpoint index
- NOT listed in /openapi.json
- Filtered OUT of /api/v1/debug's "registered_routes" dump (see the
  VULNERABILITY note in app/__init__.py's debug_info() function)

That last point is itself a deliberate lesson: someone on the ops team
apparently DID try to keep these out of the debug dump "for security" -
but filtering an internal *listing* does nothing to actually protect the
*endpoint*. The routes are still live, still unauthenticated, and still
trivially discoverable with a wordlist. Security through obscurity is not
security.

Common real-world equivalents of what's simulated here: forgotten backup
files left in a web root, leaked .env files, and old
staging/prototype admin panels that were never torn down.
"""

from flask import Blueprint, jsonify, Response, current_app

hidden_bp = Blueprint("hidden", __name__)


@hidden_bp.route("/backup", methods=["GET"])
def backup_directory_listing():
    """[HIDDEN] Simulated exposed backup directory (autoindex-style).

    VULNERABILITY: A backup directory was left web-accessible. Directory
    listing itself already leaks filenames worth investigating further.
    """
    body = (
        "Index of /backup\n"
        "-----------------\n"
        "socialhack_db_2024.sql.bak       42.1K   2024-11-03 02:14\n"
        "old_config.json.bak               1.2K   2024-09-15 18:02\n"
        "README.txt                        0.3K   2024-01-01 00:00\n"
    )
    return Response(body, mimetype="text/plain")


@hidden_bp.route("/backup/socialhack_db_2024.sql.bak", methods=["GET"])
def backup_sql_dump():
    """[HIDDEN] Simulated leaked database backup file.

    VULNERABILITY: A raw DB dump containing credentials and API keys is
    directly downloadable with no authentication.
    """
    body = (
        "-- SocialHack DB backup (auto-generated, DO NOT commit to git)\n"
        "-- Generated: 2024-11-03\n\n"
        "INSERT INTO users (username, email, password_hash, role, api_key) VALUES\n"
        "  ('admin', 'admin@socialhack.local', '$2b$12$Kx...redacted...', "
        "'admin', 'ak_admin_MASTER_KEY_x9z8y7'),\n"
        "  ('alice', 'alice@socialhack.local', '$2b$12$7f...redacted...', "
        "'user', 'ak_alice_7f3d9a2b1c4e5f6g');\n\n"
        "-- FLAG{ffuf_found_the_forgotten_backup}\n"
    )
    return Response(body, mimetype="text/plain")


@hidden_bp.route("/.env", methods=["GET"])
def dotenv_leak():
    """[HIDDEN] Simulated leaked .env file.

    VULNERABILITY: Environment file with real application secrets
    (matching the live config) is web-accessible. This is one of the
    single most common real-world findings from directory fuzzing.
    """
    body = (
        f"FLASK_SECRET_KEY={current_app.config.get('SECRET_KEY')}\n"
        f"JWT_SECRET_KEY={current_app.config.get('JWT_SECRET_KEY')}\n"
        f"DATABASE_URL={current_app.config.get('SQLALCHEMY_DATABASE_URI')}\n"
        "AWS_ACCESS_KEY_ID=AKIA1234567890ABCDEF\n"
        "AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY\n"
        "STRIPE_SECRET_KEY=sk_test_51H8xxxxxxxxxxxxxxxxxxxx\n"
        "# FLAG{dotenv_files_should_never_be_web_accessible}\n"
    )
    return Response(body, mimetype="text/plain")


@hidden_bp.route("/admin_old", methods=["GET"])
def old_staging_admin_panel():
    """[HIDDEN] Simulated forgotten staging admin prototype.

    VULNERABILITY: An old prototype admin panel from before the current
    /api/v1/admin/* routes existed. It was supposed to be torn down before
    launch and never was - the same class of mistake as the /api/v0 legacy
    API from Stage 8, just discovered through fuzzing instead of the debug
    endpoint this time.
    """
    return jsonify({
        "warning": "Deprecated staging admin prototype - scheduled for "
                   "removal before launch (this never actually happened)",
        "flag": "FLAG{old_admin_panel_still_deployed}",
        "hint": "This isn't the only forgotten surface on this server - "
                "an entire API VERSION was left running too. "
                "See Stage 8.2 (Improper Inventory Management).",
    }), 200
