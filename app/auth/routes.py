"""
Authentication Routes
Location: /Users/jrosenbaum/Documents/Code/md-converter/app/auth/routes.py

This module implements authentication endpoints for OAuth2 flow:
- /auth/status - Check authentication status (AJAX endpoint)
- /auth/logout - Sign out user and clear session

Note: /auth/google and /auth/google/authorized are provided by Flask-Dance

Dependencies:
    - Flask-Dance: OAuth flow management
    - app/auth: Blueprint

Used by: Frontend JavaScript for auth status checks
"""
from flask import redirect, url_for, flash, jsonify, session
from flask_dance.contrib.google import google
import logging
import requests

from app.auth import auth_bp

logger = logging.getLogger(__name__)


@auth_bp.route('/status')
def status():
    """
    Check authentication status (AJAX endpoint).

    This endpoint is called by frontend JavaScript to determine
    if the user is authenticated and to display user information.

    Returns:
        JSON with authentication state and user info:
        {
            'authenticated': bool,
            'user': {
                'email': str,
                'name': str,
                'picture': str (URL)
            } or None
        }

    Status Codes:
        200: Success (regardless of auth status)

    Example:
        >>> fetch('/auth/status')
        ... .then(res => res.json())
        ... .then(data => console.log(data.authenticated))
    """
    if google.authorized:
        try:
            # Fetch user info from Google
            resp = google.get('/oauth2/v2/userinfo')
            if resp.ok:
                user_info = resp.json()
                logger.debug(f"Auth status check: authenticated as {user_info.get('email')}")
                return jsonify({
                    'authenticated': True,
                    'user': {
                        'email': user_info.get('email'),
                        'name': user_info.get('name'),
                        'picture': user_info.get('picture')
                    }
                }), 200
            else:
                logger.warning(f"Failed to fetch user info: {resp.status_code}")
        except Exception as e:
            logger.error(f"Failed to fetch user info: {e}", exc_info=True)

    logger.debug("Auth status check: not authenticated")
    return jsonify({'authenticated': False, 'user': None}), 200


@auth_bp.route('/logout')
def logout():
    """
    Sign out user and revoke OAuth token.

    Clears the Flask session and optionally revokes the OAuth token
    with Google to ensure complete sign out.

    Returns:
        Redirect to home page

    Example:
        >>> curl http://localhost:8080/auth/logout
        [Redirects to /]
    """
    if google.authorized:
        token = google.token.get('access_token')

        # Optional: Revoke token with Google
        if token:
            try:
                requests.post(
                    'https://oauth2.googleapis.com/revoke',
                    params={'token': token},
                    headers={'content-type': 'application/x-www-form-urlencoded'}
                )
                logger.info("OAuth token revoked successfully")
            except Exception as e:
                logger.warning(f"Token revocation failed: {e}")

    # Clear Flask session
    session.clear()

    logger.info("User signed out")
    return redirect('/')


@auth_bp.route('/profile')
def profile():
    """
    Display user profile (for testing/debugging).

    Returns detailed user profile information from Google.
    This endpoint is primarily for development and testing.

    Returns:
        JSON with user profile data or error message

    Status Codes:
        200: Success
        401: Not authenticated

    Example:
        >>> curl http://localhost:8080/auth/profile
        {
            "email": "user@example.com",
            "name": "John Doe",
            "picture": "https://...",
            "verified_email": true
        }
    """
    if not google.authorized:
        return jsonify({'error': 'Not authenticated'}), 401

    try:
        resp = google.get('/oauth2/v2/userinfo')
        if resp.ok:
            return jsonify(resp.json()), 200
        else:
            return jsonify({'error': 'Failed to fetch user info'}), resp.status_code
    except Exception as e:
        logger.error(f"Profile fetch error: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500
