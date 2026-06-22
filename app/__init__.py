"""SocialHack API - A deliberately vulnerable social media API for learning API security."""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

db = SQLAlchemy()


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

    app.register_blueprint(auth_bp, url_prefix="/api/v1/auth")
    app.register_blueprint(users_bp, url_prefix="/api/v1/users")
    app.register_blueprint(posts_bp, url_prefix="/api/v1/posts")
    app.register_blueprint(comments_bp, url_prefix="/api/v1")
    app.register_blueprint(messages_bp, url_prefix="/api/v1/messages")
    app.register_blueprint(admin_bp, url_prefix="/api/v1/admin")
    app.register_blueprint(upload_bp, url_prefix="/api/v1")
    app.register_blueprint(misc_bp, url_prefix="/api/v1")
    app.register_blueprint(graphql_bp, url_prefix="/api/v1")

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
            "registered_routes": [
                str(rule) for rule in app.url_map.iter_rules()
            ],
        }

    # Create tables
    with app.app_context():
        from app import models  # noqa: F401

        db.create_all()

    return app
