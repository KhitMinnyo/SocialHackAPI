"""Application configuration."""

import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    """Base configuration."""

    SECRET_KEY = "super-secret-flask-key-12345"
    # VULNERABILITY: Weak JWT secret - can be brute-forced
    JWT_SECRET_KEY = "socialhack-secret-key"
    JWT_ALGORITHM = "HS256"
    # VULNERABILITY: Long token expiry
    JWT_ACCESS_TOKEN_EXPIRES = 86400 * 30  # 30 days

    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(BASE_DIR, "..", "socialhack.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Upload settings
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "..", "uploads")
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB

    # VULNERABILITY: Debug mode enabled
    DEBUG = True

    # Rate limiting (intentionally disabled/weak)
    RATE_LIMIT_ENABLED = False
    RATE_LIMIT_MAX_REQUESTS = 1000
    RATE_LIMIT_WINDOW = 60


class TestingConfig(Config):
    """Testing configuration."""

    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
