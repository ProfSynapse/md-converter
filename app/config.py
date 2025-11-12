"""
Configuration Settings
Location: /mnt/c/Users/Joseph/Documents/Code/md-converter/app/config.py

This module defines configuration classes for different environments.
It loads environment variables and sets default values.

Used by: app/__init__.py for application configuration
"""
import os
from pathlib import Path


class Config:
    """Base configuration class"""

    # Flask configuration
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

    # Application settings
    MAX_FILE_SIZE = int(os.environ.get('MAX_FILE_SIZE', 10 * 1024 * 1024))  # 10MB
    ALLOWED_EXTENSIONS = {'md', 'markdown', 'txt', 'html', 'htm'}
    MAX_CONTENT_LENGTH = MAX_FILE_SIZE

    # HTML conversion settings
    MAX_HTML_SIZE = 10 * 1024 * 1024  # 10MB
    IMAGE_FETCH_TIMEOUT = 10  # seconds
    MAX_IMAGES_PER_DOCUMENT = 100  # DOS prevention

    # Paths
    BASE_DIR = Path(__file__).parent.parent
    # Use /tmp/converted in production (Docker) for better compatibility
    CONVERTED_FOLDER = Path(os.environ.get('CONVERTED_FOLDER', '/tmp/converted'))
    TEMPLATE_PATH = BASE_DIR / 'app' / 'templates' / 'template.docx'

    # Conversion settings
    INCLUDE_FRONT_MATTER = True
    CLEANUP_INTERVAL = 24 * 3600  # 24 hours in seconds

    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')

    # OAuth2 configuration
    GOOGLE_OAUTH_CLIENT_ID = os.environ.get('GOOGLE_OAUTH_CLIENT_ID')
    GOOGLE_OAUTH_CLIENT_SECRET = os.environ.get('GOOGLE_OAUTH_CLIENT_SECRET')
    GOOGLE_CLOUD_PROJECT_ID = os.environ.get('GOOGLE_CLOUD_PROJECT_ID')

    # Flask-Dance settings
    OAUTHLIB_RELAX_TOKEN_SCOPE = True  # Allow scope flexibility
    OAUTHLIB_INSECURE_TRANSPORT = False  # HTTPS only in production

    # Session cookie security
    SESSION_COOKIE_HTTPONLY = True  # Prevent JavaScript access
    SESSION_COOKIE_SECURE = True  # HTTPS only (enforced in production)
    SESSION_COOKIE_SAMESITE = 'Lax'  # CSRF protection
    SESSION_PERMANENT = False  # Session expires when browser closes
    PERMANENT_SESSION_LIFETIME = 3600  # 1 hour if session made permanent


class DevelopmentConfig(Config):
    """Development environment configuration"""
    DEBUG = True
    LOG_LEVEL = 'DEBUG'
    SESSION_COOKIE_SECURE = False  # Allow HTTP for localhost
    OAUTHLIB_INSECURE_TRANSPORT = True  # Allow HTTP OAuth for local testing


class ProductionConfig(Config):
    """Production environment configuration"""
    DEBUG = False
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')

    # Production secret key should be set via environment variable
    SECRET_KEY = os.environ.get('SECRET_KEY')
    if not SECRET_KEY:
        import secrets
        SECRET_KEY = secrets.token_hex(32)


class TestingConfig(Config):
    """Testing environment configuration"""
    TESTING = True
    DEBUG = True
    LOG_LEVEL = 'DEBUG'
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB for testing


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': Config
}
