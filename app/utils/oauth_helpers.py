"""
OAuth Helper Functions
Location: /Users/jrosenbaum/Documents/Code/md-converter/app/utils/oauth_helpers.py

This module provides utility functions for OAuth2 credential management:
- get_google_credentials(): Get OAuth2 credentials from Flask-Dance session
- is_authenticated(): Check if user is authenticated
- check_auth_required(): Check if authentication is required for requested formats

Dependencies:
    - Flask-Dance: OAuth token management
    - google-auth: Google OAuth2 credentials

Used by: app/api/routes.py for conversion requests
"""
from flask_dance.contrib.google import google
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
import logging

logger = logging.getLogger(__name__)


def get_google_credentials():
    """
    Get OAuth2 credentials from Flask-Dance session.

    This function extracts the OAuth token from the Flask-Dance session
    and creates a google.oauth2.credentials.Credentials object that can
    be used with Google API client libraries.

    Returns:
        google.oauth2.credentials.Credentials: Credentials object with valid token

    Raises:
        ValueError: If user not authenticated or credentials invalid

    Example:
        >>> credentials = get_google_credentials()
        >>> docs_service = build('docs', 'v1', credentials=credentials)
    """
    if not google.authorized:
        raise ValueError("User not authenticated")

    token_data = google.token

    credentials = Credentials(
        token=token_data['access_token'],
        refresh_token=token_data.get('refresh_token'),
        token_uri='https://oauth2.googleapis.com/token',
        client_id=google.client_id,
        client_secret=google.client_secret,
        scopes=token_data.get('scope', [])
    )

    # Check if token needs refresh
    if credentials.expired and credentials.refresh_token:
        logger.info("Access token expired, refreshing...")
        try:
            credentials.refresh(Request())
            # Update Flask-Dance session with new token
            google.token['access_token'] = credentials.token
            if credentials.expiry:
                google.token['expires_at'] = credentials.expiry.timestamp()
            logger.info("Token refreshed successfully")
        except Exception as e:
            logger.error(f"Token refresh failed: {e}", exc_info=True)
            raise ValueError("Failed to refresh OAuth token") from e

    return credentials


def is_authenticated():
    """
    Check if user is authenticated with Google.

    Returns:
        bool: True if user has valid OAuth session, False otherwise

    Example:
        >>> if is_authenticated():
        ...     print("User is signed in")
    """
    return google.authorized


def check_auth_required(formats):
    """
    Check if authentication is required for requested formats.

    Args:
        formats: List of format strings (e.g., ['docx', 'pdf', 'gdocs'])
                 or single format string

    Returns:
        bool: True if auth required but not authenticated, False otherwise

    Example:
        >>> if check_auth_required(['docx', 'gdocs']):
        ...     return "Please sign in to use Google Docs", 401
    """
    # Handle single format string
    if isinstance(formats, str):
        formats = [formats]

    # Google Docs requires authentication
    return 'gdocs' in formats and not google.authorized
