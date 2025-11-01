"""
Authentication Module
Location: /Users/jrosenbaum/Documents/Code/md-converter/app/auth/__init__.py

This module provides OAuth2 authentication using Flask-Dance with Google.
It manages user authentication sessions via encrypted cookies (no database).

Dependencies:
    - Flask-Dance: OAuth flow management
    - google-api-python-client: Google API integration

Used by: app/__init__.py for blueprint registration
"""
from flask import Blueprint

auth_bp = Blueprint('auth', __name__)

from app.auth import routes
