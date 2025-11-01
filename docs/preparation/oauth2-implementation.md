# OAuth2 Implementation for Google Sign-In (Primary Implementation)

**Last Updated**: November 1, 2025
**Status**: Primary Implementation
**Priority**: High (core authentication method)

---

## Executive Summary

OAuth2 user authentication enables users to sign in with their Google account and have converted documents saved directly to their own Google Drive. This is the **primary and recommended authentication method** for the markdown converter application.

**Recommendation**: Implement OAuth2 as the core authentication mechanism with session-based token storage (no database required). Service account authentication can be added later as an alternative for users who don't want to sign in.

**Key Benefits of OAuth2 as Primary Approach**:
- **User Ownership**: Documents created in user's own Google Drive (not shared from service account)
- **No Database Required**: Session-based token storage using encrypted Flask cookies
- **Privacy-First**: No persistent user data storage, fully GDPR-compliant
- **Natural Scaling**: Quotas scale with user base (60 writes/min per user vs 600/min total for service account)
- **Frictionless UX**: One-click sign-in if user already authenticated in browser
- **Better Control**: Users can organize, edit, delete, and manage their documents

**Why Not Service Account**:
- Service account creates centralized quota bottleneck (600 writes/min for all users)
- Documents owned by service account (not user)
- Requires sharing mechanism for users to access documents
- Less scalable for growing user base
- More complex permission management

**Implementation Complexity**: Moderate, but manageable with Flask-Dance library which handles OAuth flow with minimal boilerplate and supports session storage without requiring SQLAlchemy or database setup.

### Important: What Users DON'T Need to Do

Users of the application **do NOT need**:
- Google Cloud Platform account
- Google Cloud Project
- OAuth client credentials
- Service account setup
- Any Google Cloud Console access
- Technical knowledge of OAuth2

**Only the developer/administrator needs to**:
1. Create the Google Cloud Project
2. Set up the OAuth consent screen
3. Create OAuth client credentials
4. Configure Railway environment variables

**Users only need to**:
1. Have a Google account (any Gmail account)
2. Click "Sign in with Google" button
3. Authorize the application (one-time consent)
4. Use the application to convert documents

The frictionless UX means if users are already signed into Google in their browser, authorization is typically a single click with no password entry required.

---

## Architecture Overview

### Authentication Flow

```
User clicks "Sign in with Google"
        ↓
Application redirects to Google OAuth consent screen
        ↓
User authorizes application (grants scopes)
        ↓
Google redirects back to application with authorization code
        ↓
Application exchanges code for access token + refresh token
        ↓
Application stores tokens (session or database)
        ↓
Application uses access token to create documents in user's Drive
        ↓
Access token expires (1 hour) → refresh using refresh token
```

### Token Management

**Access Token**:
- Short-lived (1 hour)
- Used for API requests
- Refresh when expired

**Refresh Token**:
- Long-lived (doesn't expire unless revoked)
- Used to get new access tokens
- Store securely (encrypted in database or secure session)

---

## Step 1: Configure OAuth Consent Screen

### 1.1 Navigate to OAuth Consent Screen

1. Google Cloud Console → APIs & Services → OAuth consent screen
2. Select user type:
   - **Internal**: Only for G Suite/Workspace users in your organization
   - **External**: For any Google user (recommended for public app)

### 1.2 Configure App Information

**OAuth consent screen**:
```
App name: Markdown to Google Docs Converter
User support email: your-email@example.com
App logo: [Upload your logo - 120x120px PNG/JPG]

Application home page: https://your-app.railway.app
Application privacy policy: https://your-app.railway.app/privacy
Application terms of service: https://your-app.railway.app/terms
```

**Authorized domains**:
```
railway.app
your-custom-domain.com
```

**Developer contact email**: `your-email@example.com`

### 1.3 Configure Scopes

Click "Add or Remove Scopes" and select:

**Required scopes for document creation**:
- `https://www.googleapis.com/auth/documents` - Create and edit Google Docs
- `https://www.googleapis.com/auth/drive.file` - Access files created by this app

**Optional scopes** (if needed):
- `https://www.googleapis.com/auth/userinfo.email` - User's email address
- `https://www.googleapis.com/auth/userinfo.profile` - User's basic profile info

**Important**: Don't request scopes you don't need. Each scope requires justification during Google verification.

### 1.4 Test Users (for development)

While app is in "Testing" status, add test users:
```
developer1@gmail.com
developer2@gmail.com
```

**Testing mode limitations**:
- Only listed test users can sign in
- No Google verification required
- Suitable for development

### 1.5 Publishing (for production)

To make app available to all users:
1. Click "Publish App"
2. Submit for Google verification (if using sensitive/restricted scopes)
3. Verification process: 4-6 weeks typically
4. Provide video demo, privacy policy, homepage

**Scopes requiring verification**:
- Most Drive and Docs scopes require verification
- `drive.file` scope may not require verification (app-created files only)

---

## Step 2: Create OAuth Client ID

### 2.1 Navigate to Credentials

1. APIs & Services → Credentials
2. Click "Create Credentials" → "OAuth client ID"

### 2.2 Configure OAuth Client

**Application type**: Web application

**Name**: `Markdown Converter Web Client`

**Authorized JavaScript origins**:
```
http://localhost:8080
https://your-app.railway.app
https://your-custom-domain.com
```

**Authorized redirect URIs**:
```
http://localhost:8080/auth/google/callback
https://your-app.railway.app/auth/google/callback
https://your-custom-domain.com/auth/google/callback
```

### 2.3 Save Credentials

After creation, you'll receive:
- **Client ID**: `123456789-abc123def456.apps.googleusercontent.com`
- **Client Secret**: `GOCSPX-abc123def456xyz789`

**Download JSON**:
```json
{
  "web": {
    "client_id": "123456789-abc123def456.apps.googleusercontent.com",
    "project_id": "markdown-converter-prod",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_secret": "GOCSPX-abc123def456xyz789",
    "redirect_uris": ["https://your-app.railway.app/auth/google/callback"]
  }
}
```

**Security**: Store client secret securely (environment variable, not in code)

---

## Step 3: Python Implementation Options

### Option A: Flask-Dance with Session Storage (Recommended)

Flask-Dance is a mature library that handles OAuth flows with minimal boilerplate. **Use session storage (encrypted cookies) instead of SQLAlchemy** to avoid database dependency.

#### Installation

```bash
pip install Flask-Dance  # Basic installation - session storage only, no SQLAlchemy required
```

**DO NOT install**: `Flask-Dance[sqla]` - This adds SQLAlchemy dependency which is unnecessary for session-based storage

#### Configuration

**app/config.py**:
```python
import os

class Config:
    # Existing config...

    # OAuth configuration
    GOOGLE_OAUTH_CLIENT_ID = os.getenv('GOOGLE_OAUTH_CLIENT_ID')
    GOOGLE_OAUTH_CLIENT_SECRET = os.getenv('GOOGLE_OAUTH_CLIENT_SECRET')
    OAUTHLIB_RELAX_TOKEN_SCOPE = True  # Allow scope changes
    OAUTHLIB_INSECURE_TRANSPORT = os.getenv('FLASK_ENV') == 'development'  # HTTP for local dev
```

#### Implementation

**app/auth/__init__.py**:
```python
from flask import Blueprint
from flask_dance.contrib.google import make_google_blueprint

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# Create Google OAuth blueprint
google_bp = make_google_blueprint(
    client_id=None,  # Set from config at runtime
    client_secret=None,
    scope=[
        'https://www.googleapis.com/auth/documents',
        'https://www.googleapis.com/auth/drive.file',
        'openid',
        'email',
        'profile'
    ],
    redirect_to='index'  # Redirect to home after login
)

from app.auth import routes
```

**app/auth/routes.py**:
```python
from flask import redirect, url_for, flash, session
from flask_login import login_user, logout_user, current_user, login_required
from flask_dance.contrib.google import google

from app.auth import auth_bp

@auth_bp.route('/login')
def login():
    """Redirect to Google OAuth login."""
    if not google.authorized:
        return redirect(url_for('google.login'))
    return redirect(url_for('index'))

@auth_bp.route('/logout')
@login_required
def logout():
    """Log out user and revoke token."""
    # Clear Flask-Dance token
    if google.authorized:
        token = google.token['access_token']
        # Optionally revoke token
        # requests.post('https://oauth2.googleapis.com/revoke',
        #               params={'token': token},
        #               headers={'content-type': 'application/x-www-form-urlencoded'})

    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@auth_bp.route('/profile')
@login_required
def profile():
    """Display user profile."""
    if not google.authorized:
        return redirect(url_for('google.login'))

    resp = google.get('/oauth2/v2/userinfo')
    if resp.ok:
        user_info = resp.json()
        return {
            'email': user_info['email'],
            'name': user_info['name'],
            'picture': user_info['picture']
        }
    return {'error': 'Failed to fetch user info'}, 400
```

**app/__init__.py** (register blueprints):
```python
from flask import Flask
from app.auth import auth_bp, google_bp

def create_app(config_name='production'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Configure Google OAuth
    google_bp.client_id = app.config['GOOGLE_OAUTH_CLIENT_ID']
    google_bp.client_secret = app.config['GOOGLE_OAUTH_CLIENT_SECRET']

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(google_bp, url_prefix='/auth/google')

    # ... rest of app initialization

    return app
```

#### Using OAuth Token for API Calls

```python
from flask_dance.contrib.google import google
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

@login_required
def create_user_document(title: str, content: str):
    """Create document in user's Google Drive using OAuth token."""
    if not google.authorized:
        return None

    # Get OAuth token from Flask-Dance
    token = google.token['access_token']

    # Create credentials object
    credentials = Credentials(token=token)

    # Build services
    docs_service = build('docs', 'v1', credentials=credentials)
    drive_service = build('drive', 'v3', credentials=credentials)

    # Create document
    document = docs_service.documents().create(body={'title': title}).execute()
    document_id = document.get('documentId')

    # Add content (example)
    requests = [{
        'insertText': {
            'location': {'index': 1},
            'text': content
        }
    }]
    docs_service.documents().batchUpdate(
        documentId=document_id,
        body={'requests': requests}
    ).execute()

    # Get document URL
    file = drive_service.files().get(fileId=document_id, fields='webViewLink').execute()

    return {
        'documentId': document_id,
        'webViewLink': file.get('webViewLink')
    }
```

### Option B: google-auth-oauthlib (More Control)

For more control over the OAuth flow:

#### Installation

```bash
pip install google-auth google-auth-oauthlib google-auth-httplib2
```

#### Implementation

**app/utils/oauth_flow.py**:
```python
import os
import json
from flask import session, url_for
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials

SCOPES = [
    'https://www.googleapis.com/auth/documents',
    'https://www.googleapis.com/auth/drive.file',
    'openid',
    'email',
    'profile'
]

def create_flow():
    """Create OAuth flow instance."""
    client_config = {
        'web': {
            'client_id': os.getenv('GOOGLE_OAUTH_CLIENT_ID'),
            'client_secret': os.getenv('GOOGLE_OAUTH_CLIENT_SECRET'),
            'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
            'token_uri': 'https://oauth2.googleapis.com/token',
            'redirect_uris': [url_for('auth.oauth_callback', _external=True)]
        }
    }

    flow = Flow.from_client_config(
        client_config=client_config,
        scopes=SCOPES
    )
    flow.redirect_uri = url_for('auth.oauth_callback', _external=True)

    return flow

def get_credentials_from_session():
    """Retrieve user credentials from session."""
    if 'credentials' not in session:
        return None

    return Credentials(**session['credentials'])

def save_credentials_to_session(credentials):
    """Save credentials to session."""
    session['credentials'] = {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }
```

**app/auth/routes.py**:
```python
from flask import redirect, request, session, url_for
from app.auth import auth_bp
from app.utils.oauth_flow import create_flow, save_credentials_to_session

@auth_bp.route('/login')
def login():
    """Initiate OAuth flow."""
    flow = create_flow()
    authorization_url, state = flow.authorization_url(
        access_type='offline',  # Get refresh token
        include_granted_scopes='true',
        prompt='consent'  # Force consent to ensure refresh token
    )

    # Store state in session for CSRF protection
    session['state'] = state

    return redirect(authorization_url)

@auth_bp.route('/oauth/callback')
def oauth_callback():
    """Handle OAuth callback."""
    # Verify state for CSRF protection
    state = session.get('state')
    if not state or state != request.args.get('state'):
        return 'Invalid state parameter', 400

    flow = create_flow()
    flow.fetch_token(authorization_response=request.url)

    credentials = flow.credentials
    save_credentials_to_session(credentials)

    return redirect(url_for('index'))
```

---

## Step 4: Token Storage (Session-Based - No Database)

### Recommended Approach: Encrypted Session Cookies

**This is the PRIMARY and RECOMMENDED approach** for the markdown converter application. No database required.

**Advantages**:
- **No database needed** - Simplifies deployment and reduces infrastructure
- **Privacy-first** - No persistent user data storage, fully GDPR-compliant
- **Survives server restarts** - Tokens stored client-side in encrypted cookies
- **Scalable across workers** - Works seamlessly with Railway's auto-scaling
- **Stateless architecture** - Each request contains all needed authentication data

**Trade-offs** (all acceptable for this use case):
- Cookie size limits (4KB) - OAuth tokens easily fit within this limit
- Security depends on Flask SECRET_KEY - Use strong, stable secret (Railway sealed variable)
- Users can clear cookies - Acceptable, just requires re-authentication

**Why No Database**:
1. **User Privacy**: No need to store user data long-term
2. **Simplified Architecture**: Fewer components to maintain and secure
3. **Cost Efficiency**: No database hosting costs
4. **GDPR Compliance**: Session expiration automatically deletes user data
5. **Scalability**: Stateless design scales horizontally without session synchronization

### Implementation

**app/config.py**:
```python
import os
import secrets

class Config:
    """Base configuration."""
    # Session security (CRITICAL for OAuth token storage)
    SECRET_KEY = os.getenv('SECRET_KEY')  # Must be set in Railway
    if not SECRET_KEY:
        # Generate secret for development only
        SECRET_KEY = secrets.token_hex(32)
        print("WARNING: Using generated SECRET_KEY. Set SECRET_KEY env var in production!")

    # Session cookie security
    SESSION_COOKIE_HTTPONLY = True  # Prevent JavaScript access
    SESSION_COOKIE_SECURE = True  # HTTPS only (enforced in production)
    SESSION_COOKIE_SAMESITE = 'Lax'  # CSRF protection
    SESSION_PERMANENT = False  # Session expires when browser closes
    PERMANENT_SESSION_LIFETIME = 3600  # 1 hour if session made permanent

    # Flask-Dance will use these session settings automatically
    # No SQLAlchemy or database configuration needed!

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    SESSION_COOKIE_SECURE = True  # Enforce HTTPS

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    SESSION_COOKIE_SECURE = False  # Allow HTTP for localhost
```

**Flask-Dance Default Behavior**:
```python
# Flask-Dance uses session storage by default!
# No additional configuration needed for session storage
# Simply don't set the .storage attribute on the blueprint

from flask_dance.contrib.google import make_google_blueprint

google_bp = make_google_blueprint(
    client_id=os.getenv('GOOGLE_OAUTH_CLIENT_ID'),
    client_secret=os.getenv('GOOGLE_OAUTH_CLIENT_SECRET'),
    scope=[
        'https://www.googleapis.com/auth/documents',
        'https://www.googleapis.com/auth/drive.file'
    ]
)
# That's it! Tokens automatically stored in Flask session (encrypted cookie)
```

### Session Security Checklist

- [ ] `SECRET_KEY` is strong (32+ bytes, cryptographically random)
- [ ] `SECRET_KEY` is stable across deployments (stored in Railway sealed variable)
- [ ] `SECRET_KEY` is never committed to version control
- [ ] `SESSION_COOKIE_HTTPONLY=True` (prevent XSS attacks)
- [ ] `SESSION_COOKIE_SECURE=True` in production (HTTPS only)
- [ ] `SESSION_COOKIE_SAMESITE='Lax'` (CSRF protection)
- [ ] HTTPS enforced in production (Railway provides this automatically)

### Alternative: Database Storage (NOT RECOMMENDED for this project)

**Only consider database storage if**:
- You need user accounts with persistent profiles
- You want to track user conversion history
- You need to associate documents with user records
- You have compliance requirements for audit trails

For the markdown converter use case, **session storage is superior** because:
- No user accounts needed - just OAuth authentication
- No need to track conversion history
- Documents belong to user's Google Drive (not app database)
- Simpler architecture, lower maintenance burden

---

## Step 5: Frontend Integration

### HTML Template (Login Button)

**templates/index.html**:
```html
{% if current_user.is_authenticated and google.authorized %}
    <!-- User is logged in -->
    <div class="user-info">
        <img src="{{ user_picture }}" alt="{{ user_name }}" class="user-avatar">
        <span>{{ user_name }}</span>
        <a href="{{ url_for('auth.logout') }}" class="btn btn-secondary">Sign Out</a>
    </div>

    <!-- Show option to save to user's Drive -->
    <form action="/api/convert" method="post" enctype="multipart/form-data">
        <input type="file" name="file" required>
        <select name="format">
            <option value="docx">Word (DOCX)</option>
            <option value="pdf">PDF</option>
            <option value="gdocs">Google Docs (My Drive)</option>
        </select>
        <button type="submit">Convert</button>
    </form>
{% else %}
    <!-- User not logged in -->
    <div class="auth-prompt">
        <p>Sign in with Google to save conversions to your Drive</p>
        <a href="{{ url_for('google.login') }}" class="btn btn-primary">
            <img src="/static/google-icon.svg" alt="Google"> Sign in with Google
        </a>
    </div>

    <!-- Show basic conversion without login -->
    <form action="/api/convert" method="post" enctype="multipart/form-data">
        <input type="file" name="file" required>
        <select name="format">
            <option value="docx">Word (DOCX)</option>
            <option value="pdf">PDF</option>
            <option value="gdocs">Google Docs (Public Link)</option>
        </select>
        <button type="submit">Convert</button>
    </form>
{% endif %}
```

### JavaScript (Optional - Better UX)

**static/js/auth.js**:
```javascript
// Check OAuth status on page load
document.addEventListener('DOMContentLoaded', function() {
    const formatSelect = document.querySelector('select[name="format"]');
    const gdocsOption = formatSelect.querySelector('option[value="gdocs"]');

    // Check if user is authenticated
    fetch('/auth/status')
        .then(res => res.json())
        .then(data => {
            if (data.authenticated) {
                gdocsOption.textContent = 'Google Docs (My Drive)';
            } else {
                gdocsOption.textContent = 'Google Docs (Public Link)';
            }
        });
});
```

**app/auth/routes.py** (add status endpoint):
```python
@auth_bp.route('/status')
def status():
    """Check if user is authenticated with Google."""
    return {
        'authenticated': google.authorized,
        'user': google.get('/oauth2/v2/userinfo').json() if google.authorized else None
    }
```

---

## Step 6: Conversion Logic with OAuth

### Modified Convert Endpoint

**app/api/routes.py**:
```python
from flask import request, current_app
from flask_dance.contrib.google import google
from app.utils.google_auth import get_google_services, create_public_document
from app.converters.markdown_converter import MarkdownConverter

@api_bp.route('/convert', methods=['POST'])
def convert():
    """Convert markdown to specified format(s)."""
    # ... existing validation ...

    format_type = request.form.get('format', 'both')

    # Handle Google Docs format
    if format_type == 'gdocs' or format_type == 'both':
        if google.authorized:
            # User is logged in - save to their Drive
            result = create_user_owned_document(
                title=f"{original_filename} - Converted",
                markdown_content=content
            )
        else:
            # User not logged in - use service account (public link)
            result = create_public_document(
                title=f"{original_filename} - Converted",
                markdown_content=content
            )

        # ... return result with webViewLink ...
```

### Helper Function

```python
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from flask_dance.contrib.google import google

def create_user_owned_document(title: str, markdown_content: str) -> dict:
    """
    Create Google Doc in user's Drive using OAuth token.

    Args:
        title: Document title
        markdown_content: Markdown text to convert

    Returns:
        dict with documentId and webViewLink
    """
    if not google.authorized:
        raise PermissionError("User not authenticated with Google")

    # Get OAuth credentials
    token = google.token['access_token']
    credentials = Credentials(token=token)

    # Build services
    docs_service = build('docs', 'v1', credentials=credentials)
    drive_service = build('drive', 'v3', credentials=credentials)

    # Create document
    document = docs_service.documents().create(body={'title': title}).execute()
    document_id = document.get('documentId')

    # Convert markdown to Docs API requests
    from app.converters.google_docs_converter import convert_markdown_to_requests
    requests = convert_markdown_to_requests(markdown_content)

    # Apply content
    if requests:
        docs_service.documents().batchUpdate(
            documentId=document_id,
            body={'requests': requests}
        ).execute()

    # Get shareable link
    file = drive_service.files().get(
        fileId=document_id,
        fields='webViewLink'
    ).execute()

    return {
        'documentId': document_id,
        'webViewLink': file.get('webViewLink'),
        'ownership': 'user'
    }
```

---

## Security Considerations

### 1. CSRF Protection

Always validate state parameter:
```python
@auth_bp.route('/oauth/callback')
def callback():
    if request.args.get('state') != session.get('state'):
        abort(400, 'Invalid state parameter')
    # ... rest of callback logic
```

### 2. Token Security

**DO**:
- Store tokens encrypted in database
- Use HTTPS for all OAuth redirects
- Set `httpOnly` and `secure` flags on session cookies
- Regenerate session ID after login

**DON'T**:
- Log tokens in plain text
- Send tokens to client-side JavaScript
- Store tokens in localStorage
- Share tokens across users

### 3. Scope Minimization

Only request necessary scopes:
```python
# Good - minimal scopes
SCOPES = [
    'https://www.googleapis.com/auth/documents',
    'https://www.googleapis.com/auth/drive.file'  # Only app-created files
]

# Bad - excessive scopes
SCOPES = [
    'https://www.googleapis.com/auth/drive'  # Full Drive access (unnecessary)
]
```

### 4. Token Refresh

Implement automatic token refresh:
```python
from google.auth.transport.requests import Request

def get_valid_credentials():
    """Get credentials, refreshing if expired."""
    credentials = get_credentials_from_session()

    if credentials and credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())
        save_credentials_to_session(credentials)

    return credentials
```

---

## Testing OAuth Flow

### Local Testing

1. **Set environment variables**:
```bash
export GOOGLE_OAUTH_CLIENT_ID='your-client-id.apps.googleusercontent.com'
export GOOGLE_OAUTH_CLIENT_SECRET='your-client-secret'
export OAUTHLIB_INSECURE_TRANSPORT=1  # Allow HTTP for localhost
export FLASK_ENV=development
```

2. **Run application**:
```bash
python wsgi.py
```

3. **Test flow**:
   - Visit http://localhost:8080
   - Click "Sign in with Google"
   - Authorize application
   - Verify redirect to callback
   - Check session contains token
   - Create test document

### Production Testing

1. Deploy to Railway with HTTPS
2. Update redirect URIs in Google Cloud Console
3. Test with production URLs
4. Verify state parameter validation
5. Test token refresh after 1 hour

---

## Deployment Considerations

### Environment Variables

```bash
# OAuth credentials
GOOGLE_OAUTH_CLIENT_ID=123456789-abc.apps.googleusercontent.com
GOOGLE_OAUTH_CLIENT_SECRET=GOCSPX-xyz789

# Flask secret (must be stable across deploys)
SECRET_KEY=your-long-random-secret-key

# OAuth settings
OAUTHLIB_RELAX_TOKEN_SCOPE=true
OAUTHLIB_INSECURE_TRANSPORT=false  # HTTPS only in production
```

### Railway Configuration

In Railway dashboard:
1. Go to your project
2. Variables tab
3. Add variables above
4. Seal sensitive values (CLIENT_SECRET, SECRET_KEY)

### Session Persistence

For Railway with multiple workers:
- Use database session storage, OR
- Use sticky sessions (single worker), OR
- Use Redis for session storage

---

## Implementation Priorities

### Primary Implementation Path (Recommended)

1. **Set up OAuth2 infrastructure** (see Steps 1-2 above)
   - Google Cloud Project setup
   - OAuth consent screen configuration
   - OAuth client credentials
   - Test users for development

2. **Implement Flask-Dance OAuth flow** (see Step 3, Option A)
   - Session-based storage (no database)
   - "Sign in with Google" button
   - Authentication endpoints
   - Token management

3. **Implement conversion with OAuth** (see Step 6)
   - User-owned document creation
   - OAuth-authenticated API calls
   - Error handling for token expiration

4. **Deploy to production**
   - Railway environment variables
   - HTTPS enforcement
   - Session security configuration

5. **Submit for Google verification** (parallel with development)
   - Plan 4-6 weeks for approval
   - Use test users during verification period
   - Prepare demo video and privacy policy

### Optional Future Enhancement

**Service account as fallback** (for users who don't want to sign in):
- Implement service account authentication (see `service-account-setup.md`)
- Create public shared docs with "anyone with link" permission
- Add UI toggle: "Sign in" vs "Convert without sign-in"

**Estimated Implementation Time**:
- OAuth2 primary implementation: 20-30 hours
- Optional service account addition: 8-12 hours

**Recommended Approach**: Start with OAuth2 only. User ownership and natural quota scaling make it the superior choice for this application. Service account can be added later if there's demand from users who prefer not to sign in.
