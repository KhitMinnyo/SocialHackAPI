"""SocialHack API - A deliberately vulnerable social media API for learning API security."""

from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_sock import Sock

db = SQLAlchemy()
sock = Sock()


def create_app(config_name="default"):
    """Application factory pattern."""
    app = Flask(__name__)

    # Load config
    if config_name == "testing":
        app.config.from_object("app.config.TestingConfig")
    else:
        app.config.from_object("app.config.Config")

    # Initialize extensions
    db.init_app(app)
    # VULNERABILITY: CORS Misconfiguration
    # - Allows ANY origin with wildcard
    # - supports_credentials=True with wildcard = dangerous
    # - Exposes all headers
    CORS(app,
         origins="*",
         supports_credentials=True,
         allow_headers=["*"],
         expose_headers=["*"],
         methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])

    # VULNERABILITY: Add custom CORS headers for extra misconfig
    @app.after_request
    def add_cors_headers(response):
        origin = __import__('flask').request.headers.get('Origin', '*')
        response.headers['Access-Control-Allow-Origin'] = origin
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, PATCH, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = '*'
        # VULNERABILITY: Exposing server info in headers
        response.headers['X-Powered-By'] = 'Flask/SocialHack'
        response.headers['Server'] = 'SocialHack-API/1.0'
        return response

    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.users import users_bp
    from app.routes.posts import posts_bp
    from app.routes.comments import comments_bp
    from app.routes.messages import messages_bp
    from app.routes.admin import admin_bp
    from app.routes.upload import upload_bp
    from app.routes.misc import misc_bp
    from app.routes.graphql_api import graphql_bp
    from app.routes.promotions import promotions_bp
    from app.routes.integrations import integrations_bp
    from app.routes.legacy import legacy_bp
    from app.routes.docs import docs_bp
    from app.routes.hidden import hidden_bp
    from app.routes.otp import otp_bp
    from app.routes.gateway_internal import gateway_bp
    from app.routes.web import web_bp

    app.register_blueprint(auth_bp, url_prefix="/api/v1/auth")
    app.register_blueprint(users_bp, url_prefix="/api/v1/users")
    app.register_blueprint(posts_bp, url_prefix="/api/v1/posts")
    app.register_blueprint(comments_bp, url_prefix="/api/v1")
    app.register_blueprint(messages_bp, url_prefix="/api/v1/messages")
    app.register_blueprint(admin_bp, url_prefix="/api/v1/admin")
    app.register_blueprint(upload_bp, url_prefix="/api/v1")
    app.register_blueprint(misc_bp, url_prefix="/api/v1")
    app.register_blueprint(graphql_bp, url_prefix="/api/v1")
    app.register_blueprint(promotions_bp, url_prefix="/api/v1")
    app.register_blueprint(integrations_bp, url_prefix="/api/v1")
    # VULNERABILITY (API9:2023 - Improper Inventory Management): this legacy
    # "v0" API is intentionally NOT listed in the root "/" endpoint index
    # below, and intentionally has no auth on any of its routes.
    app.register_blueprint(legacy_bp, url_prefix="/api/v0")
    # VULNERABILITY (API9:2023 - Improper Inventory Management): /openapi.json
    # and /swagger are also intentionally NOT listed in the root "/" endpoint
    # index - they must be discovered like a real attacker would (recon,
    # fuzzing, or guessing the common convention).
    app.register_blueprint(docs_bp, url_prefix="")
    # VULNERABILITY (API9:2023 - Improper Inventory Management, "security
    # through obscurity" flavor): these "hidden" routes are deliberately
    # filtered OUT of the /api/v1/debug registered_routes dump below - see
    # the filter in debug_info(). They are otherwise completely live,
    # unauthenticated endpoints. The only realistic way to find them is
    # wordlist-based fuzzing (ffuf/gobuster) - see Stage 3.5.
    app.register_blueprint(hidden_bp, url_prefix="")
    # VULNERABILITY (API4:2023 - Unrestricted Resource Consumption, bypass
    # angle): a REAL rate limiter is applied here (unlike posts/like or
    # auth/login, which have none at all by design elsewhere in this app) -
    # but its key is derived from a client-spoofable X-Forwarded-For header.
    # See app/rate_limiter.py and Stage 5.5.
    app.register_blueprint(otp_bp, url_prefix="/api/v1")

    # "Gateway"-protected internal endpoints - see fake_gateway_layer() below
    # and Stage 7.7 for the (bypassable) simulated protection.
    app.register_blueprint(gateway_bp, url_prefix="/api/v1")

    # SocialHack Web UI - a realistic, click-through social media frontend.
    # This blueprint has NO vulnerabilities of its own: it only renders page
    # shells (Jinja2 templates). All real data loading/mutation happens in
    # the browser via client-side JS calling the same /api/v1/* endpoints
    # documented throughout this course. See app/routes/web.py and Tutorial
    # 2.5 for how this ties into the Stage 2 Burp Suite workflow.
    app.register_blueprint(web_bp, url_prefix="/app")

    # VULNERABILITY (simulated API Gateway misconfiguration, Stage 7.7):
    # a naive exact-string path blocklist standing in for "the gateway".
    # Two bypasses are possible:
    #   1. Trailing-slash variant of the protected path isn't in the exact
    #      blocklist (the check never normalizes the path), but Flask still
    #      routes it to the same handler (strict_slashes=False).
    #   2. The alias route /api/v1/internal/infra-stats reaches the exact
    #      same handler/data but was never added to the blocklist at all.
    # Even for paths that DO match, the "trust" check is just a plain,
    # client-spoofable header - nothing proves the request actually came
    # through a real gateway (no mTLS, no network-level segmentation).
    GATEWAY_BLOCKED_EXACT_PATHS = {"/api/v1/gateway-internal/stats"}
    GATEWAY_TRUST_HEADER = "X-Gateway-Verified"
    GATEWAY_TRUST_VALUE = "trusted-internal-99"

    @app.before_request
    def fake_gateway_layer():
        if request.path in GATEWAY_BLOCKED_EXACT_PATHS:
            if request.headers.get(GATEWAY_TRUST_HEADER) != GATEWAY_TRUST_VALUE:
                return jsonify({
                    "error": "Blocked by gateway - internal endpoint, "
                             "requires gateway authentication",
                }), 403
        return None

    # WebSocket chat - VULNERABILITY: no Origin validation (CSWSH), no real
    # auth requirement, no per-room authorization. See app/ws_chat.py and
    # Stage 7.6. Registered after init_app() so flask-sock's route
    # decorator has an app to bind to.
    sock.init_app(app)
    from app.ws_chat import register_ws_routes
    register_ws_routes(sock)

    # Root endpoint
    @app.route("/")
    def index():
        return {
            "app": "SocialHack API",
            "version": "1.0.0",
            "description": "Social Media Platform API",
            # VULNERABILITY: Information disclosure - exposing internal details
            "debug_mode": app.debug,
            "database": app.config.get("SQLALCHEMY_DATABASE_URI", ""),
            "endpoints": {
                "auth": "/api/v1/auth",
                "users": "/api/v1/users",
                "posts": "/api/v1/posts",
                "comments": "/api/v1/posts/<id>/comments",
                "messages": "/api/v1/messages",
                "admin": "/api/v1/admin",
                "upload": "/api/v1/upload",
                "export": "/api/v1/export",
                "tools": "/api/v1/tools",
                "graphql": "/api/v1/graphql",
                "webhooks": "/api/v1/webhook",
                "promotions": "/api/v1/promotions",
                "integrations": "/api/v1/integrations",
                "otp": "/api/v1/otp",
                "web_ui": "/app",
            },
        }

    # Debug endpoint - VULNERABILITY: Information disclosure
    @app.route("/api/v1/debug")
    def debug_info():
        return {
            "server": "Flask/" + Flask.__module__,
            "python_version": __import__("sys").version,
            "database_uri": app.config.get("SQLALCHEMY_DATABASE_URI"),
            "secret_key": app.config.get("SECRET_KEY"),
            "jwt_secret": app.config.get("JWT_SECRET_KEY"),
            "debug": app.debug,
            # VULNERABILITY (false sense of coverage): routes belonging to
            # the "hidden" blueprint are filtered OUT of this dump - someone
            # apparently thought that was enough to keep them safe. It
            # isn't: the endpoints are still fully live and reachable, just
            # not listed here. Filtering a *listing* is not the same as
            # actually protecting an *endpoint* - a wordlist fuzzer doesn't
            # care whether this dump mentions a path or not.
            "registered_routes": [
                str(rule) for rule in app.url_map.iter_rules()
                if not rule.endpoint.startswith("hidden.")
            ],
        }

    # Create tables
    with app.app_context():
        from app import models  # noqa: F401

        db.create_all()

    return app
