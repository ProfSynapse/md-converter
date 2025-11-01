# OAuth2 Authentication Design

**Document Version**: 1.0
**Date**: 2025-11-01
**Phase**: PACT Architecture
**Status**: Ready for Implementation

---

## Executive Summary

This document specifies the detailed design for implementing OAuth2 "Sign in with Google" authentication using Flask-Dance with session-based token storage. The design eliminates the need for a database, provides automatic token refresh, and ensures secure session management compliant with modern web security standards.

**Primary Goals**:
1. Frictionless user authentication with Google accounts
2. No persistent user data storage (privacy-first)
3. Automatic token refresh for uninterrupted service
4. Secure session management via encrypted cookies
5. Clear error handling and graceful degradation

**Key Design Decision**: Use Flask-Dance with default session storage (encrypted cookies) instead of database-backed token storage. This simplifies deployment, reduces infrastructure requirements, and maintains user privacy.

---

## Authentication Architecture

### Component Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Browser (User Agent)                      │
│  ┌──────────────────────────────────────────────────────┐  │
│  │           Session Cookie (Encrypted)                  │  │
│  │  - OAuth access_token                                 │  │
│  │  - OAuth refresh_token                                │  │
│  │  - Token expiration time                              │  │
│  │  - User info (optional)                               │  │
│  │  Size: ~1-2KB, Encrypted with SECRET_KEY             │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTPS Only
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    Flask Application                         │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Flask-Dance Blueprint                    │  │
│  │  - OAuth flow management                              │  │
│  │  - Token storage (session backend)                    │  │
│  │  - Automatic token refresh                            │  │
│  │  - State parameter generation/validation             │  │
│  └──────────────────────┬───────────────────────────────┘  │
│                         │                                    │
│  ┌──────────────────────▼───────────────────────────────┐  │
│  │            Auth Blueprint (Custom)                    │  │
│  │  /auth/google       - Initiate flow                   │  │
│  │  /auth/google/authorized - Callback                   │  │
│  │  /auth/logout       - Sign out                        │  │
│  │  /auth/status       - Check auth state (AJAX)        │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              Google OAuth2 Authorization Server              │
│  - accounts.google.com/o/oauth2/auth                        │
│  - oauth2.googleapis.com/token                              │
└─────────────────────────────────────────────────────────────┘
```

---

## OAuth2 Flow Details

### 1. Login Initiation

**User Action**: Clicks "Sign in with Google" button

**Request Flow**:
```
GET /auth/google

Flask-Dance generates:
  - Authorization URL
  - State parameter (CSRF token)
  - Redirect to Google consent screen
```

**State Generation** (Automatic by Flask-Dance):
```python
# Flask-Dance internally generates secure state
state = secrets.token_urlsafe(32)
session['oauth_state'] = state

authorization_url = (
    f"https://accounts.google.com/o/oauth2/auth"
    f"?client_id={CLIENT_ID}"
    f"&redirect_uri={CALLBACK_URL}"
    f"&scope={SCOPES}"
    f"&response_type=code"
    f"&state={state}"
    f"&access_type=offline"
    f"&prompt=consent"
)
```

**Parameters Explained**:
- `client_id`: OAuth client ID from Google Cloud Console
- `redirect_uri`: `https://your-app.railway.app/auth/google/authorized`
- `scope`: `documents drive.file openid email profile`
- `response_type=code`: Authorization code flow
- `state`: CSRF protection token
- `access_type=offline`: Request refresh token
- `prompt=consent`: Force consent screen (ensures refresh token)

### 2. User Consent

**Google Consent Screen**:
```
┌──────────────────────────────────────────────────┐
│        Markdown Converter wants to:              │
│                                                   │
│  ✓ View and manage Google Docs documents         │
│  ✓ View files created with this app             │
│  ✓ See your email address                        │
│  ✓ See your personal info                        │
│                                                   │
│      [ Cancel ]     [ Allow ]                    │
└──────────────────────────────────────────────────┘
```

**User Experience**:
- If already signed into Google: One-click authorization
- If not signed in: Sign in, then authorize
- If previously authorized: Skip consent (unless `prompt=consent`)

### 3. Authorization Callback

**Callback Request**:
```
GET /auth/google/authorized?code=AUTH_CODE&state=STATE_TOKEN

Flask-Dance validates:
  1. State parameter matches session
  2. No error parameter present
  3. Authorization code present
```

**Token Exchange** (Automatic by Flask-Dance):
```
POST https://oauth2.googleapis.com/token
Content-Type: application/x-www-form-urlencoded

code=AUTH_CODE
&client_id=CLIENT_ID
&client_secret=CLIENT_SECRET
&redirect_uri=CALLBACK_URL
&grant_type=authorization_code

Response:
{
  "access_token": "ya29.a0AfH6SMBx...",
  "refresh_token": "1//0gH...",
  "expires_in": 3600,
  "scope": "https://www.googleapis.com/auth/documents...",
  "token_type": "Bearer"
}
```

**Session Storage** (Automatic by Flask-Dance):
```python
# Flask-Dance stores in session['google_oauth_token']
session['google_oauth_token'] = {
    'access_token': 'ya29...',
    'refresh_token': '1//0g...',
    'expires_at': timestamp + 3600,
    'token_type': 'Bearer'
}
```

### 4. Token Refresh

**Automatic Refresh** (Flask-Dance handles this):

```python
from flask_dance.contrib.google import google

# When making API call
if google.token.get('expires_at', 0) < time.time():
    # Token expired, Flask-Dance automatically refreshes
    # Uses refresh_token to get new access_token
    # Updates session transparently
```

**Refresh Request** (Automatic):
```
POST https://oauth2.googleapis.com/token
Content-Type: application/x-www-form-urlencoded

client_id=CLIENT_ID
&client_secret=CLIENT_SECRET
&refresh_token=REFRESH_TOKEN
&grant_type=refresh_token

Response:
{
  "access_token": "ya29.NEW_TOKEN...",
  "expires_in": 3600,
  "scope": "...",
  "token_type": "Bearer"
}
```

**Session Update**:
```python
# Flask-Dance automatically updates session
session['google_oauth_token']['access_token'] = new_access_token
session['google_oauth_token']['expires_at'] = new_expiry
# Note: refresh_token remains unchanged
```

### 5. Logout

**User Action**: Clicks "Sign out" button

**Request Flow**:
```
GET /auth/logout

1. Clear Flask session
2. (Optional) Revoke token with Google
3. Redirect to home page
```

**Token Revocation** (Optional but Recommended):
```python
@auth_bp.route('/logout')
def logout():
    """Sign out user and optionally revoke token."""
    if google.authorized:
        token = google.token.get('access_token')

        # Optional: Revoke token with Google
        try:
            requests.post(
                'https://oauth2.googleapis.com/revoke',
                params={'token': token},
                headers={'content-type': 'application/x-www-form-urlencoded'}
            )
        except Exception as e:
            logger.warning(f"Token revocation failed: {e}")

    # Clear session
    session.clear()

    flash('You have been signed out.', 'info')
    return redirect(url_for('index'))
```

---

## Implementation Specifications

### Flask-Dance Configuration

**Installation**:
```bash
# Install Flask-Dance (WITHOUT SQLAlchemy)
pip install Flask-Dance

# DO NOT install Flask-Dance[sqla] - we don't need database support
```

**Blueprint Setup** (`app/__init__.py`):
```python
from flask import Flask
from flask_dance.contrib.google import make_google_blueprint

def create_app(config_name='production'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Create Google OAuth blueprint
    google_bp = make_google_blueprint(
        client_id=app.config['GOOGLE_OAUTH_CLIENT_ID'],
        client_secret=app.config['GOOGLE_OAUTH_CLIENT_SECRET'],
        scope=[
            'https://www.googleapis.com/auth/documents',
            'https://www.googleapis.com/auth/drive.file',
            'openid',
            'email',
            'profile'
        ],
        redirect_to='index',  # Redirect to home after login
        redirect_url='/auth/google/authorized',  # Explicit callback URL
        login_url='/auth/google',  # Explicit login URL
    )

    # Register blueprint
    # Note: Flask-Dance uses session storage by default (no storage= parameter)
    app.register_blueprint(google_bp, url_prefix='/auth/google')

    # Register custom auth routes
    from app.auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    return app
```

**Key Configuration Points**:
- `client_id` and `client_secret` from Railway environment variables
- `scope`: Specific permissions needed (minimal necessary scopes)
- `redirect_to='index'`: Where to send user after successful login
- No `storage=` parameter: Uses session storage by default
- URL prefix `/auth/google` for Flask-Dance routes

### Session Configuration

**Security Settings** (`app/config.py`):
```python
import os
import secrets

class Config:
    """Base configuration."""

    # SECRET_KEY: CRITICAL for session security
    # Must be stable across deployments (set in Railway)
    SECRET_KEY = os.getenv('SECRET_KEY')
    if not SECRET_KEY:
        # Development fallback (WARNING: Not for production)
        SECRET_KEY = secrets.token_hex(32)
        print("WARNING: Using generated SECRET_KEY. Set SECRET_KEY env var in production!")

    # Session cookie security flags
    SESSION_COOKIE_HTTPONLY = True   # Prevent JavaScript access
    SESSION_COOKIE_SECURE = True     # HTTPS only (enforced in production)
    SESSION_COOKIE_SAMESITE = 'Lax'  # CSRF protection
    SESSION_PERMANENT = False         # Session expires on browser close
    PERMANENT_SESSION_LIFETIME = 3600  # 1 hour (if made permanent)

    # OAuth configuration
    GOOGLE_OAUTH_CLIENT_ID = os.getenv('GOOGLE_OAUTH_CLIENT_ID')
    GOOGLE_OAUTH_CLIENT_SECRET = os.getenv('GOOGLE_OAUTH_CLIENT_SECRET')
    GOOGLE_CLOUD_PROJECT_ID = os.getenv('GOOGLE_CLOUD_PROJECT_ID')

    # Flask-Dance settings
    OAUTHLIB_RELAX_TOKEN_SCOPE = True  # Allow scope flexibility
    OAUTHLIB_INSECURE_TRANSPORT = False  # HTTPS only in production


class DevelopmentConfig(Config):
    """Development environment configuration."""
    DEBUG = True
    SESSION_COOKIE_SECURE = False  # Allow HTTP for localhost
    OAUTHLIB_INSECURE_TRANSPORT = True  # Allow HTTP OAuth for local testing


class ProductionConfig(Config):
    """Production environment configuration."""
    DEBUG = False
    SESSION_COOKIE_SECURE = True  # Enforce HTTPS
    OAUTHLIB_INSECURE_TRANSPORT = False  # Enforce HTTPS for OAuth

    # Verify critical config
    if not Config.SECRET_KEY:
        raise RuntimeError("SECRET_KEY must be set in production")
    if not Config.GOOGLE_OAUTH_CLIENT_ID:
        raise RuntimeError("GOOGLE_OAUTH_CLIENT_ID must be set")
    if not Config.GOOGLE_OAUTH_CLIENT_SECRET:
        raise RuntimeError("GOOGLE_OAUTH_CLIENT_SECRET must be set")
```

### Custom Auth Routes

**Auth Blueprint** (`app/auth/__init__.py`):
```python
from flask import Blueprint

auth_bp = Blueprint('auth', __name__)

from app.auth import routes
```

**Auth Routes** (`app/auth/routes.py`):
```python
from flask import redirect, url_for, flash, jsonify, session
from flask_dance.contrib.google import google
import logging

from app.auth import auth_bp

logger = logging.getLogger(__name__)


@auth_bp.route('/status')
def status():
    """
    Check authentication status (AJAX endpoint).

    Returns:
        JSON with authentication state and user info
    """
    if google.authorized:
        try:
            # Fetch user info from Google
            resp = google.get('/oauth2/v2/userinfo')
            if resp.ok:
                user_info = resp.json()
                return jsonify({
                    'authenticated': True,
                    'user': {
                        'email': user_info.get('email'),
                        'name': user_info.get('name'),
                        'picture': user_info.get('picture')
                    }
                }), 200
        except Exception as e:
            logger.error(f"Failed to fetch user info: {e}", exc_info=True)

    return jsonify({'authenticated': False, 'user': None}), 200


@auth_bp.route('/logout')
def logout():
    """
    Sign out user and revoke OAuth token.

    Returns:
        Redirect to home page
    """
    if google.authorized:
        token = google.token.get('access_token')

        # Optional: Revoke token with Google
        if token:
            try:
                import requests
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
    flash('You have been signed out.', 'info')
    return redirect(url_for('index'))


@auth_bp.route('/profile')
def profile():
    """
    Display user profile (for testing/debugging).

    Returns:
        JSON with user profile data
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
```

**Note**: Flask-Dance automatically provides `/auth/google` (login) and `/auth/google/authorized` (callback) routes.

---

## Token Management

### Credentials Helper

**Utility Module** (`app/utils/oauth_helpers.py`):
```python
from flask_dance.contrib.google import google
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
import logging

logger = logging.getLogger(__name__)


def get_google_credentials():
    """
    Get OAuth2 credentials from Flask-Dance session.

    Returns:
        google.oauth2.credentials.Credentials object

    Raises:
        ValueError: If user not authenticated
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
            google.token['expires_at'] = credentials.expiry.timestamp()
            logger.info("Token refreshed successfully")
        except Exception as e:
            logger.error(f"Token refresh failed: {e}", exc_info=True)
            raise

    return credentials


def check_auth_required(formats):
    """
    Check if authentication is required for requested formats.

    Args:
        formats: List of format strings (e.g., ['docx', 'pdf', 'gdocs'])

    Returns:
        bool: True if auth required, False otherwise
    """
    return 'gdocs' in formats and not google.authorized
```

### Token Lifecycle Management

**Token Expiration Handling**:
```python
from datetime import datetime, timedelta

def is_token_valid():
    """
    Check if current access token is valid.

    Returns:
        bool: True if token valid, False otherwise
    """
    if not google.authorized:
        return False

    expires_at = google.token.get('expires_at', 0)
    # Add 5-minute buffer to avoid edge cases
    buffer = timedelta(minutes=5).total_seconds()

    return datetime.utcnow().timestamp() < (expires_at - buffer)
```

**Proactive Token Refresh**:
```python
def ensure_fresh_token():
    """
    Ensure access token is fresh before API calls.

    This should be called before making Google API requests.

    Returns:
        Credentials object with valid token

    Raises:
        ValueError: If authentication fails
    """
    if not google.authorized:
        raise ValueError("User not authenticated")

    credentials = get_google_credentials()

    # Token automatically refreshed by get_google_credentials()
    # if expired and refresh token available

    return credentials
```

---

## Error Handling

### Error Scenarios

#### 1. OAuth Callback Error

**Scenario**: Google returns error instead of authorization code

**Error Response**:
```
GET /auth/google/authorized?error=access_denied&state=...
```

**Handling** (Flask-Dance automatic):
```python
# Flask-Dance catches this and redirects to error page
# Customize by handling unauthorized signal

from flask_dance.contrib.google import google_authorized

@google_authorized.connect
def google_logged_in(blueprint, token):
    """
    Handle successful OAuth login.

    Called automatically by Flask-Dance after token exchange.
    """
    if not token:
        flash("Failed to sign in with Google.", "error")
        return False  # Prevents automatic redirect

    # Optional: Fetch and cache user info
    resp = blueprint.session.get('/oauth2/v2/userinfo')
    if resp.ok:
        user_info = resp.json()
        session['user_email'] = user_info.get('email')
        session['user_name'] = user_info.get('name')
        flash(f"Welcome, {user_info.get('name')}!", "success")

    return False  # Return False to prevent Flask-Dance default redirect
```

#### 2. Token Refresh Failure

**Scenario**: Refresh token revoked or expired

**Handling**:
```python
from google.auth.exceptions import RefreshError

try:
    credentials = get_google_credentials()
    # Use credentials for API call
except RefreshError:
    # Refresh failed - clear session and redirect to login
    logger.warning("Token refresh failed - re-authentication required")
    session.clear()
    flash("Your session has expired. Please sign in again.", "warning")
    return redirect(url_for('google.login'))
except ValueError:
    # User not authenticated
    flash("Please sign in to use Google Docs conversion.", "info")
    return redirect(url_for('google.login'))
```

#### 3. State Parameter Mismatch

**Scenario**: CSRF attack attempt

**Handling** (Flask-Dance automatic):
```python
# Flask-Dance validates state parameter automatically
# If mismatch, raises InvalidClientIdError

# Log security event
import logging
logger = logging.getLogger(__name__)

@app.errorhandler(InvalidClientIdError)
def handle_invalid_state(e):
    logger.warning(f"Invalid OAuth state detected: {e}")
    flash("Security validation failed. Please try again.", "error")
    return redirect(url_for('index'))
```

#### 4. Missing OAuth Configuration

**Scenario**: Environment variables not set

**Handling** (Application startup):
```python
# In app/__init__.py create_app()

if app.config['ENABLE_GOOGLE_DOCS_CONVERSION']:
    if not app.config['GOOGLE_OAUTH_CLIENT_ID']:
        logger.error("GOOGLE_OAUTH_CLIENT_ID not set")
        app.config['ENABLE_GOOGLE_DOCS_CONVERSION'] = False
    if not app.config['GOOGLE_OAUTH_CLIENT_SECRET']:
        logger.error("GOOGLE_OAUTH_CLIENT_SECRET not set")
        app.config['ENABLE_GOOGLE_DOCS_CONVERSION'] = False

if not app.config['ENABLE_GOOGLE_DOCS_CONVERSION']:
    logger.warning("Google Docs conversion disabled - OAuth not configured")
```

### Error Response Format

**API Error Response**:
```python
def format_auth_error(error_code, message, status=401):
    """
    Format authentication error response.

    Args:
        error_code: Machine-readable error code
        message: Human-readable error message
        status: HTTP status code

    Returns:
        tuple: (JSON response, status code)
    """
    return jsonify({
        'error': message,
        'code': error_code,
        'status': status,
        'auth_url': url_for('google.login', _external=True),
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }), status
```

**Usage in Routes**:
```python
@api_bp.route('/convert', methods=['POST'])
def convert():
    formats = request.form.getlist('formats')

    if 'gdocs' in formats and not google.authorized:
        return format_auth_error(
            'AUTH_REQUIRED',
            'Google Docs conversion requires authentication. Please sign in.',
            401
        )

    # ... rest of conversion logic
```

---

## Security Considerations

### CSRF Protection

**State Parameter**:
- Generated automatically by Flask-Dance
- Stored in server-side session
- Validated on callback
- Single-use (consumed after validation)

**Session Cookie SameSite**:
```python
SESSION_COOKIE_SAMESITE = 'Lax'  # Prevents CSRF via cross-site requests
```

### XSS Prevention

**httpOnly Flag**:
```python
SESSION_COOKIE_HTTPONLY = True  # JavaScript cannot access cookies
```

**Content Security Policy**:
```python
# In app/__init__.py
@app.after_request
def add_security_headers(response):
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "script-src 'self' https://cdn.tailwindcss.com 'unsafe-inline'; "
        "connect-src 'self';"
    )
    return response
```

### Secret Management

**SECRET_KEY Security**:
```bash
# Generate strong secret
python3 -c "import secrets; print(secrets.token_hex(32))"

# Set in Railway (SEALED)
SECRET_KEY=<64-character-hex-string>
```

**OAuth Client Secret**:
```bash
# Set in Railway (SEALED)
GOOGLE_OAUTH_CLIENT_SECRET=GOCSPX-...
```

**Verification Checklist**:
- [ ] SECRET_KEY is strong (32+ bytes, cryptographically random)
- [ ] SECRET_KEY is stable (not regenerated on deploy)
- [ ] SECRET_KEY is sealed in Railway
- [ ] GOOGLE_OAUTH_CLIENT_SECRET is sealed in Railway
- [ ] Secrets never logged in plain text
- [ ] Secrets never committed to version control

### HTTPS Enforcement

**Production Configuration**:
```python
# app/config.py ProductionConfig
SESSION_COOKIE_SECURE = True  # HTTPS only
OAUTHLIB_INSECURE_TRANSPORT = False  # HTTPS only for OAuth
```

**Railway Platform**:
- HTTPS automatically enabled
- Automatic certificate management
- HTTP → HTTPS redirect built-in

---

## Testing Strategy

### Unit Tests

**Test OAuth Configuration**:
```python
def test_oauth_config():
    """Test OAuth configuration is loaded correctly."""
    app = create_app('testing')

    assert app.config['GOOGLE_OAUTH_CLIENT_ID'] is not None
    assert app.config['GOOGLE_OAUTH_CLIENT_SECRET'] is not None
    assert 'google' in app.blueprints  # Flask-Dance blueprint registered
```

**Test Auth Helper Functions**:
```python
from app.utils.oauth_helpers import check_auth_required

def test_check_auth_required():
    """Test authentication requirement check."""
    assert check_auth_required(['docx', 'pdf']) == False
    assert check_auth_required(['gdocs']) == True
    assert check_auth_required(['docx', 'gdocs']) == True
```

### Integration Tests

**Test OAuth Login Flow**:
```python
def test_oauth_login_redirect(client):
    """Test OAuth login redirects to Google."""
    response = client.get('/auth/google')

    assert response.status_code == 302
    assert 'accounts.google.com' in response.location
    assert 'client_id' in response.location
    assert 'state' in response.location
```

**Test OAuth Callback** (with mocking):
```python
from unittest import mock

@mock.patch('flask_dance.contrib.google.google.authorized', True)
@mock.patch('flask_dance.contrib.google.google.token', {
    'access_token': 'test_token',
    'refresh_token': 'test_refresh',
    'expires_at': 9999999999
})
def test_google_docs_conversion_authenticated(client):
    """Test Google Docs conversion when authenticated."""
    with client.session_transaction() as sess:
        sess['google_oauth_token'] = {
            'access_token': 'test_token',
            'refresh_token': 'test_refresh',
            'expires_at': 9999999999
        }

    response = client.post('/api/convert', data={
        'file': (io.BytesIO(b'# Test'), 'test.md'),
        'formats': ['gdocs']
    })

    # Should not return 401 Unauthorized
    assert response.status_code != 401
```

**Test Authentication Status Endpoint**:
```python
def test_auth_status_not_authenticated(client):
    """Test /auth/status when not authenticated."""
    response = client.get('/auth/status')

    assert response.status_code == 200
    data = response.get_json()
    assert data['authenticated'] == False
    assert data['user'] is None
```

### Manual Testing Checklist

- [ ] Click "Sign in with Google" redirects to Google consent
- [ ] Google consent screen shows correct scopes
- [ ] Successful login redirects back to application
- [ ] User info displayed correctly after login
- [ ] Google Docs option enabled after login
- [ ] Session persists across page reloads
- [ ] Token automatically refreshes after 1 hour
- [ ] "Sign out" clears session
- [ ] Google Docs option disabled after sign out
- [ ] Multiple sign in/out cycles work correctly
- [ ] Works in incognito mode (new session)
- [ ] Session expires on browser close (if SESSION_PERMANENT=False)

---

## Deployment Checklist

### Google Cloud Console Setup

- [ ] Create Google Cloud Project
- [ ] Enable Google Docs API
- [ ] Enable Google Drive API
- [ ] Configure OAuth consent screen
  - [ ] Set application name
  - [ ] Add authorized domains
  - [ ] Configure scopes (documents, drive.file, email, profile)
  - [ ] Add test users (for development)
- [ ] Create OAuth client ID (Web application)
  - [ ] Add authorized JavaScript origins
  - [ ] Add authorized redirect URIs
  - [ ] Download client credentials

### Railway Configuration

- [ ] Set SECRET_KEY environment variable (SEALED)
- [ ] Set GOOGLE_OAUTH_CLIENT_ID environment variable
- [ ] Set GOOGLE_OAUTH_CLIENT_SECRET environment variable (SEALED)
- [ ] Set GOOGLE_CLOUD_PROJECT_ID environment variable
- [ ] Set OAUTHLIB_RELAX_TOKEN_SCOPE=true
- [ ] Set OAUTHLIB_INSECURE_TRANSPORT=false
- [ ] Verify HTTPS enabled (automatic in Railway)

### Application Deployment

- [ ] Install Flask-Dance dependency
- [ ] Update requirements.txt
- [ ] Deploy to Railway
- [ ] Test OAuth flow in production
- [ ] Monitor logs for errors
- [ ] Update OAuth redirect URIs if Railway URL changes

### Post-Deployment Verification

- [ ] `/health` endpoint shows OAuth configured
- [ ] `/auth/google` redirects to Google
- [ ] OAuth callback completes successfully
- [ ] Tokens stored in session correctly
- [ ] Google Docs conversion works for authenticated users
- [ ] Sign out clears session
- [ ] No errors in Railway logs

---

## Monitoring and Logging

### Key Metrics to Track

**Authentication Metrics**:
- OAuth login attempts
- OAuth login success/failure rate
- Token refresh success/failure rate
- Average session duration
- Active authenticated users (approximate)

**Logging Strategy**:
```python
# OAuth login initiated
logger.info(f"OAuth login initiated from IP {request.remote_addr}")

# OAuth callback successful
logger.info(f"OAuth callback successful, user authenticated: {user_email}")

# OAuth callback failed
logger.warning(f"OAuth callback failed: {error_code}")

# Token refresh
logger.info(f"Access token refreshed for user: {user_email}")

# Token refresh failed
logger.error(f"Token refresh failed: {error}", exc_info=True)

# Sign out
logger.info(f"User signed out: {user_email}")

# Security events
logger.warning(f"Invalid OAuth state parameter detected from IP {request.remote_addr}")
logger.warning(f"Unauthorized access attempt to Google Docs conversion")
```

### Health Check Enhancement

```python
@app.route('/health')
def health_check():
    """Enhanced health check including OAuth status."""
    health = {
        'status': 'healthy',
        'features': {
            'oauth_enabled': app.config.get('ENABLE_GOOGLE_DOCS_CONVERSION', False),
            'oauth_client_configured': bool(app.config.get('GOOGLE_OAUTH_CLIENT_ID'))
        }
    }

    # Don't expose actual secrets
    if not health['features']['oauth_client_configured']:
        health['status'] = 'degraded'
        health['warnings'] = ['OAuth not configured']

    return jsonify(health), 200 if health['status'] == 'healthy' else 503
```

---

## Appendix

### Flask-Dance Session Storage

**How Flask-Dance Uses Sessions**:
```python
# Flask-Dance stores OAuth token in session by default
# Location: session['google_oauth_token']
# Structure:
{
    'access_token': 'ya29...',
    'refresh_token': '1//0g...',
    'expires_at': 1234567890,  # Unix timestamp
    'token_type': 'Bearer',
    'scope': ['...', '...']
}
```

**Session Cookie Characteristics**:
- Size: ~1-2KB (well within 4KB browser limit)
- Encrypted: Using Flask SECRET_KEY with itsdangerous
- Signed: Prevents tampering
- Secure: httpOnly, Secure, SameSite flags
- Lifetime: Browser session (unless SESSION_PERMANENT=True)

### OAuth Scope Reference

**Required Scopes**:
```python
[
    'https://www.googleapis.com/auth/documents',      # Create/edit Docs
    'https://www.googleapis.com/auth/drive.file',     # Access app-created files
    'openid',                                          # OpenID Connect
    'email',                                           # User email address
    'profile'                                          # User profile info
]
```

**Scope Permissions**:
- `documents`: Full access to Google Docs documents
- `drive.file`: Access only to files created by this app (not all Drive files)
- `openid`, `email`, `profile`: User identification

### Troubleshooting Guide

**Issue**: OAuth callback returns `redirect_uri_mismatch`

**Solution**: Update authorized redirect URIs in Google Cloud Console to match exact URL

---

**Issue**: `InvalidClientIdError` on callback

**Solution**: Verify CLIENT_ID and CLIENT_SECRET match Google Cloud Console values

---

**Issue**: Session cookie not persisting

**Solution**: Check SECRET_KEY is set and stable across deployments

---

**Issue**: Token refresh fails with `invalid_grant`

**Solution**: User revoked access or refresh token expired. Re-authenticate required.

---

**Authentication Design Status**: COMPLETE
**Ready for Implementation**: YES
**Next Document**: Google Docs Converter Design
