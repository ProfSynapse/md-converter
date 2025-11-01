# Deployment Configuration for Google Docs Integration

**Last Updated**: November 1, 2025
**Platform**: Railway
**Environment**: Production

---

## Executive Summary

Deploying Google Docs conversion to Railway requires secure credential management, environment variable configuration, and production-ready error handling. This document covers Railway-specific deployment strategies, secrets management, and monitoring setup.

**Key Considerations**:
- Service account credentials must be stored securely
- Railway provides "sealed" variables for sensitive data
- Environment variables can be injected as JSON or file paths
- Health checks and logging are critical for production monitoring

---

## Required Environment Variables

### Core Application Variables (Existing)

```bash
# Flask configuration
FLASK_ENV=production
LOG_LEVEL=INFO
SECRET_KEY=your-long-random-secret-key  # CRITICAL for session-based OAuth storage

# File handling
MAX_FILE_SIZE=10485760  # 10MB in bytes
CONVERTED_FOLDER=/tmp/converted

# Server configuration
PORT=8080  # Railway injects this automatically
```

### OAuth2 Variables (Primary - Required for User Authentication)

```bash
# OAuth2 Client Credentials (PRIMARY METHOD)
GOOGLE_OAUTH_CLIENT_ID=123456789-abc.apps.googleusercontent.com
GOOGLE_OAUTH_CLIENT_SECRET=GOCSPX-xyz789  # SEAL THIS in Railway

# OAuth2 Settings
OAUTHLIB_RELAX_TOKEN_SCOPE=true
OAUTHLIB_INSECURE_TRANSPORT=false  # Must be false in production (HTTPS only)

# Google Cloud Project (for reference/monitoring)
GOOGLE_CLOUD_PROJECT_ID=markdown-converter-prod-437219
```

### Service Account Credentials (Optional - Only if implementing fallback)

```bash
# Service Account Authentication (OPTIONAL ALTERNATIVE)
# Only set these if you want to support non-authenticated users
GOOGLE_CREDENTIALS='{"type":"service_account","project_id":"...",...}'

# Alternative: File path (if using mounted credentials)
GOOGLE_CREDENTIALS_FILE=/app/config/credentials.json
```

### Session Security Variables (Critical for OAuth)

```bash
# Session cookie security (automatically configured by Flask config)
# These are set in app/config.py, but can be overridden:
SESSION_COOKIE_HTTPONLY=true   # Prevent JavaScript access
SESSION_COOKIE_SECURE=true     # HTTPS only in production
SESSION_COOKIE_SAMESITE=Lax    # CSRF protection
```

---

## Railway Configuration

### Primary Method: OAuth2 Environment Variables (Recommended)

**Advantages**:
- No credential files to manage
- Railway sealed variables protect sensitive data
- Session-based token storage (no database needed)
- Easy to update without redeployment
- Works with Railway's horizontal scaling
- Privacy-first (no persistent user data)

**Setup Steps**:

1. **Generate strong SECRET_KEY**:
   ```bash
   # Generate cryptographically secure secret key
   python3 -c "import secrets; print(secrets.token_hex(32))"
   # Example output: e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
   ```

2. **Add OAuth variables to Railway**:
   - Navigate to project in Railway dashboard
   - Click "Variables" tab
   - Add the following variables:

   | Variable Name | Example Value | Seal? |
   |--------------|---------------|-------|
   | `GOOGLE_OAUTH_CLIENT_ID` | `123456789-abc.apps.googleusercontent.com` | No |
   | `GOOGLE_OAUTH_CLIENT_SECRET` | `GOCSPX-xyz789` | **YES** |
   | `SECRET_KEY` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | **YES** |
   | `OAUTHLIB_RELAX_TOKEN_SCOPE` | `true` | No |
   | `OAUTHLIB_INSECURE_TRANSPORT` | `false` | No |
   | `GOOGLE_CLOUD_PROJECT_ID` | `markdown-converter-prod-437219` | No |

3. **Verify configuration**:
   - All sealed variables should show "•••••" in Railway UI
   - SECRET_KEY must be stable (never regenerate on deploy)
   - HTTPS automatically enabled by Railway

**Application Code** (Flask-Dance handles everything):
```python
# app/config.py
import os

class Config:
    # Session security (CRITICAL for OAuth)
    SECRET_KEY = os.getenv('SECRET_KEY')  # Must be set in Railway
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = True  # HTTPS only
    SESSION_COOKIE_SAMESITE = 'Lax'

    # OAuth2 configuration
    GOOGLE_OAUTH_CLIENT_ID = os.getenv('GOOGLE_OAUTH_CLIENT_ID')
    GOOGLE_OAUTH_CLIENT_SECRET = os.getenv('GOOGLE_OAUTH_CLIENT_SECRET')

# app/__init__.py
from flask_dance.contrib.google import make_google_blueprint

google_bp = make_google_blueprint(
    client_id=app.config['GOOGLE_OAUTH_CLIENT_ID'],
    client_secret=app.config['GOOGLE_OAUTH_CLIENT_SECRET'],
    scope=[
        'https://www.googleapis.com/auth/documents',
        'https://www.googleapis.com/auth/drive.file'
    ]
)
# Flask-Dance automatically uses session storage - no database needed!
app.register_blueprint(google_bp, url_prefix='/auth/google')
```

### Alternative Method: Service Account Credentials (Optional)

**NOTE**: Only use this if implementing service account as a fallback for non-authenticated users. OAuth2 is the primary method.

**Advantages**:
- No user authentication required
- Good for automated/batch processing
- Works for anonymous users

**Disadvantages**:
- Centralized quota limits (600 writes/min for all users)
- Requires credential file management
- Documents not owned by users
- More complex permission model

**Setup Steps** (only if implementing service account fallback):

1. **Prepare credentials JSON**:
   ```bash
   cat config/credentials.json | jq -c . | pbcopy  # macOS
   ```

2. **Add to Railway**:
   - Variable name: `GOOGLE_CREDENTIALS`
   - Value: Paste entire JSON (minified)
   - Click "Seal" button

**Application Code**:
```python
# app/utils/google_auth.py (service account fallback only)
import os
import json
from google.oauth2 import service_account

def get_service_account_credentials():
    """Load service account credentials (fallback for non-authenticated users)."""
    creds_json = os.getenv('GOOGLE_CREDENTIALS')
    if not creds_json:
        return None  # Service account not configured

    try:
        creds_dict = json.loads(creds_json)
        return service_account.Credentials.from_service_account_info(
            creds_dict,
            scopes=[
                'https://www.googleapis.com/auth/documents',
                'https://www.googleapis.com/auth/drive'
            ]
        )
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid GOOGLE_CREDENTIALS JSON: {e}")
```

---

## Railway Deployment Process

### 1. Update requirements.txt

```txt
# Add to existing requirements.txt

# Google API libraries
google-api-python-client>=2.149.0
google-auth>=2.35.0
google-auth-oauthlib>=1.2.3

# OAuth2 integration (session-based, no SQLAlchemy needed)
Flask-Dance>=7.0.0

# Optional: Markdown to Google Docs conversion
markgdoc>=1.0.1
```

**Important**: Install `Flask-Dance` (basic), NOT `Flask-Dance[sqla]` to avoid unnecessary SQLAlchemy dependency

### 2. Update Dockerfile (No Changes Needed)

Your existing Dockerfile already works. Railway will:
- Install dependencies from requirements.txt
- Use PORT environment variable
- Start Gunicorn on $PORT

### 3. Configure Environment Variables

In Railway dashboard:

```bash
# Existing variables (keep these)
FLASK_ENV=production
LOG_LEVEL=INFO
MAX_FILE_SIZE=10485760
CONVERTED_FOLDER=/tmp/converted

# New variables for OAuth2 (PRIMARY - add these)
SECRET_KEY=<generated-secret-key>  # SEAL THIS! Must be stable across deploys
GOOGLE_OAUTH_CLIENT_ID=<your-client-id>.apps.googleusercontent.com
GOOGLE_OAUTH_CLIENT_SECRET=<your-client-secret>  # SEAL THIS!
OAUTHLIB_RELAX_TOKEN_SCOPE=true
OAUTHLIB_INSECURE_TRANSPORT=false
GOOGLE_CLOUD_PROJECT_ID=<your-project-id>

# Optional: Service account fallback (only if implementing)
# GOOGLE_CREDENTIALS=<paste-json-credentials>  # SEAL THIS!
```

**Critical**:
- `SECRET_KEY` must be sealed and stable (never change after initial deploy)
- `GOOGLE_OAUTH_CLIENT_SECRET` must be sealed
- Generate SECRET_KEY with: `python3 -c "import secrets; print(secrets.token_hex(32))"`

### 4. Deploy

```bash
# Push to git (Railway auto-deploys)
git add .
git commit -m "Add Google Docs conversion support"
git push origin main

# Or use Railway CLI
railway up
```

### 5. Verify Deployment

```bash
# Check logs
railway logs

# Test health endpoint
curl https://your-app.railway.app/health

# Test OAuth flow (browser-based)
# 1. Visit: https://your-app.railway.app
# 2. Click "Sign in with Google"
# 3. Authorize application
# 4. Test Google Docs conversion with authenticated user

# Test conversion API (after authentication)
curl -X POST https://your-app.railway.app/api/convert \
  -F "file=@test.md" \
  -F "format=gdocs" \
  -b "session=<cookie-from-browser>"  # Include session cookie
```

### 6. Update Google OAuth Redirect URIs

**Important**: After deploying to Railway, update your OAuth client configuration:

1. Navigate to Google Cloud Console → APIs & Services → Credentials
2. Click on your OAuth client ID
3. Add production redirect URI:
   ```
   https://your-app.railway.app/auth/google/authorized
   ```
4. Save changes
5. Test OAuth flow again to verify

---

## Configuration Management

### app/config.py Updates

```python
import os
import secrets

class Config:
    """Base configuration."""
    # Existing config
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_FILE_SIZE', 10 * 1024 * 1024))
    CONVERTED_FOLDER = os.getenv('CONVERTED_FOLDER', '/tmp/converted')

    # Session security (CRITICAL for OAuth2 token storage)
    SECRET_KEY = os.getenv('SECRET_KEY')
    if not SECRET_KEY:
        SECRET_KEY = secrets.token_hex(32)
        print("WARNING: Using generated SECRET_KEY. Set SECRET_KEY env var in production!")

    SESSION_COOKIE_HTTPONLY = True   # Prevent JavaScript access to cookies
    SESSION_COOKIE_SECURE = True     # HTTPS only (enforced in production)
    SESSION_COOKIE_SAMESITE = 'Lax'  # CSRF protection
    SESSION_PERMANENT = False         # Session expires when browser closes

    # OAuth2 configuration (PRIMARY)
    GOOGLE_OAUTH_CLIENT_ID = os.getenv('GOOGLE_OAUTH_CLIENT_ID')
    GOOGLE_OAUTH_CLIENT_SECRET = os.getenv('GOOGLE_OAUTH_CLIENT_SECRET')
    GOOGLE_CLOUD_PROJECT_ID = os.getenv('GOOGLE_CLOUD_PROJECT_ID')

    # Feature flags
    ENABLE_OAUTH = bool(GOOGLE_OAUTH_CLIENT_ID and GOOGLE_OAUTH_CLIENT_SECRET)
    ENABLE_GOOGLE_DOCS_CONVERSION = ENABLE_OAUTH  # Requires OAuth for user-owned docs

    # Service account configuration (OPTIONAL - fallback only)
    GOOGLE_CREDENTIALS_JSON = os.getenv('GOOGLE_CREDENTIALS')
    ENABLE_SERVICE_ACCOUNT = bool(GOOGLE_CREDENTIALS_JSON)


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    TESTING = False

    # Enforce HTTPS for OAuth in production
    OAUTHLIB_INSECURE_TRANSPORT = False


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    TESTING = False

    # Allow HTTP for local OAuth testing
    OAUTHLIB_INSECURE_TRANSPORT = bool(os.getenv('OAUTHLIB_INSECURE_TRANSPORT'))


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': Config,
}
```

---

## Error Handling for Missing Credentials

### Graceful Degradation

```python
# app/__init__.py
from flask import Flask
import logging

logger = logging.getLogger(__name__)

def create_app(config_name='production'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Check Google Docs feature availability
    if app.config['ENABLE_GOOGLE_DOCS_CONVERSION']:
        logger.info("Google Docs conversion: ENABLED")
        try:
            from app.utils.google_auth import get_credentials
            get_credentials()  # Test credentials on startup
            logger.info("✓ Google Cloud credentials validated")
        except Exception as e:
            logger.error(f"✗ Google Cloud credentials invalid: {e}")
            app.config['ENABLE_GOOGLE_DOCS_CONVERSION'] = False
    else:
        logger.warning("Google Docs conversion: DISABLED (no credentials)")

    # Register routes
    from app.api import routes
    app.register_blueprint(routes.api_bp, url_prefix='/api')

    return app
```

### API Endpoint Validation

```python
# app/api/routes.py
from flask import current_app, jsonify

@api_bp.route('/convert', methods=['POST'])
def convert():
    """Convert markdown to specified format."""
    format_type = request.form.get('format', 'both')

    # Validate Google Docs availability
    if format_type in ('gdocs', 'both'):
        if not current_app.config['ENABLE_GOOGLE_DOCS_CONVERSION']:
            return jsonify({
                'error': 'Google Docs conversion not available',
                'code': 'FEATURE_DISABLED',
                'message': 'Server not configured for Google Docs conversion'
            }), 503

    # ... rest of conversion logic
```

---

## Monitoring and Logging

### Enhanced Logging

```python
# app/utils/google_auth.py
import logging

logger = logging.getLogger(__name__)

def get_google_services():
    """Create authenticated Google services with logging."""
    logger.info("Initializing Google API services")

    try:
        credentials = get_credentials()
        logger.debug(f"Credentials loaded for project: {credentials.project_id}")

        docs_service = build('docs', 'v1', credentials=credentials)
        drive_service = build('drive', 'v3', credentials=credentials)

        logger.info("✓ Google API services initialized successfully")
        return docs_service, drive_service

    except Exception as e:
        logger.error(f"✗ Failed to initialize Google API services: {e}",
                     exc_info=True)
        raise
```

### Request Logging

```python
# app/converters/google_docs_converter.py
import logging
import time

logger = logging.getLogger(__name__)

class GoogleDocsConverter:
    def convert(self, markdown_content: str, title: str) -> dict:
        """Convert markdown to Google Docs with detailed logging."""
        start_time = time.time()

        logger.info(f"Starting Google Docs conversion: {title}")
        logger.debug(f"Markdown content length: {len(markdown_content)} bytes")

        try:
            # Create document
            doc_id = self._create_document(title)
            logger.info(f"Document created: {doc_id}")

            # Apply content
            self._apply_content(doc_id, markdown_content)
            logger.info(f"Content applied to document: {doc_id}")

            # Set permissions
            link = self._make_public(doc_id)
            logger.info(f"Document published: {link}")

            elapsed = time.time() - start_time
            logger.info(f"Conversion completed in {elapsed:.2f}s")

            return {'documentId': doc_id, 'webViewLink': link}

        except Exception as e:
            logger.error(f"Conversion failed: {e}", exc_info=True)
            raise
```

### Railway Log Monitoring

View logs in real-time:
```bash
# Railway CLI
railway logs --follow

# Filter for Google Docs logs
railway logs | grep "Google"

# Check for errors
railway logs | grep "ERROR"
```

---

## Health Check Endpoint

### Update Existing Health Check

```python
# app/api/routes.py
from flask import jsonify, current_app

@api_bp.route('/health', methods=['GET'])
def health():
    """
    Enhanced health check including Google Docs status.

    Returns:
        JSON with service status
    """
    health_status = {
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'features': {
            'docx_conversion': True,
            'pdf_conversion': True,
            'google_docs_conversion': current_app.config['ENABLE_GOOGLE_DOCS_CONVERSION'],
            'oauth_authentication': current_app.config['ENABLE_OAUTH']
        }
    }

    # Test Google API connectivity (optional)
    if current_app.config['ENABLE_GOOGLE_DOCS_CONVERSION']:
        try:
            from app.utils.google_auth import get_google_services
            docs_service, drive_service = get_google_services()
            health_status['google_api'] = 'connected'
        except Exception as e:
            health_status['google_api'] = 'error'
            health_status['status'] = 'degraded'
            logger.warning(f"Google API health check failed: {e}")

    status_code = 200 if health_status['status'] == 'healthy' else 503

    return jsonify(health_status), status_code
```

---

## Rate Limiting Configuration

### Environment Variables

```bash
# Rate limiting (optional)
GOOGLE_DOCS_RATE_LIMIT=60  # Max conversions per minute
ENABLE_RATE_LIMITING=true
```

### Implementation

```python
# app/utils/rate_limiter.py
from flask import current_app, g
import time
from collections import deque

class RateLimiter:
    """Simple in-memory rate limiter."""

    def __init__(self):
        self.requests = deque()
        self.limit = int(os.getenv('GOOGLE_DOCS_RATE_LIMIT', 60))
        self.window = 60  # seconds

    def is_allowed(self) -> bool:
        """Check if request is within rate limit."""
        now = time.time()

        # Remove old requests outside window
        while self.requests and self.requests[0] < now - self.window:
            self.requests.popleft()

        # Check limit
        if len(self.requests) >= self.limit:
            return False

        # Record request
        self.requests.append(now)
        return True


# Usage in route
@api_bp.before_request
def check_rate_limit():
    """Check rate limit for Google Docs conversions."""
    if request.endpoint == 'api.convert' and \
       request.form.get('format') in ('gdocs', 'both'):

        if not g.rate_limiter.is_allowed():
            return jsonify({
                'error': 'Rate limit exceeded',
                'code': 'RATE_LIMIT_EXCEEDED',
                'retry_after': 60
            }), 429
```

---

## Security Checklist

### Production Security

- [ ] `GOOGLE_CREDENTIALS` marked as sealed in Railway
- [ ] `SECRET_KEY` is strong and stable (not regenerated on deploy)
- [ ] `OAUTHLIB_INSECURE_TRANSPORT=false` in production
- [ ] Credentials never logged in plain text
- [ ] HTTPS enforced for all endpoints
- [ ] Rate limiting enabled
- [ ] Error messages don't expose sensitive info
- [ ] Health check doesn't expose credentials
- [ ] Service account key rotated within last 90 days

### Code Security

```python
# Good: Safe logging
logger.info(f"Using service account: {credentials.service_account_email}")

# Bad: Exposing secrets
logger.debug(f"Credentials: {credentials}")  # Don't do this!
```

---

## Backup and Recovery

### Credential Backup

1. **Store credentials securely outside Railway**:
   - Password manager (1Password, LastPass)
   - Secure cloud storage (encrypted)
   - Company secrets vault

2. **Document credential locations**:
   ```markdown
   # Credential Locations
   - Railway: GOOGLE_CREDENTIALS (sealed)
   - Backup: company-vault/markdown-converter/credentials.json
   - Emergency contact: devops-team@company.com
   ```

### Disaster Recovery

**If credentials lost**:
1. Generate new service account key in Google Cloud Console
2. Update Railway environment variable
3. Redeploy (automatic if using environment variable)

**If service account deleted**:
1. Create new service account
2. Generate new key
3. Update Railway environment variable
4. Redeploy

---

## Performance Optimization

### Connection Pooling

```python
# app/utils/google_auth.py
from functools import lru_cache

@lru_cache(maxsize=1)
def get_google_services():
    """
    Get Google API services with caching.

    Services are expensive to create, cache them.
    """
    credentials = get_credentials()
    docs_service = build('docs', 'v1', credentials=credentials, cache_discovery=False)
    drive_service = build('drive', 'v3', credentials=credentials, cache_discovery=False)
    return docs_service, drive_service
```

**Note**: `cache_discovery=False` disables API discovery document caching, reducing memory usage in containers.

---

## Testing in Production

### Smoke Test Script

```bash
#!/bin/bash
# scripts/test-production.sh

APP_URL="https://your-app.railway.app"

echo "Testing production deployment..."

# Test health endpoint
echo "1. Health check..."
curl -sf "$APP_URL/health" | jq .

# Test Google Docs conversion
echo "2. Google Docs conversion..."
curl -sf -X POST "$APP_URL/api/convert" \
  -F "file=@test/fixtures/sample.md" \
  -F "format=gdocs" | jq .

echo "✓ Production tests passed"
```

---

## Rollback Strategy

If deployment fails:

1. **Railway automatic rollback**:
   - Railway keeps previous deployments
   - Rollback via dashboard or CLI

2. **Manual rollback**:
   ```bash
   # Railway CLI
   railway rollback
   ```

3. **Disable feature temporarily**:
   ```bash
   # Remove GOOGLE_CREDENTIALS variable
   railway variables delete GOOGLE_CREDENTIALS

   # Redeploy
   railway up
   ```

---

## Cost Monitoring

### Google Cloud Costs

Monitor in Google Cloud Console:
- Navigation → Billing → Reports
- Filter by project ID
- Expected cost: $0-5/month for typical usage

### Railway Costs

Railway pricing based on:
- Build minutes
- Runtime (CPU + memory)
- Network egress

**Google API impact**: Minimal (libraries add ~30s build time, ~20MB memory)

---

## Summary

**Minimum Configuration**:
```bash
GOOGLE_CREDENTIALS='{"type":"service_account",...}'
```

**Recommended Configuration**:
```bash
GOOGLE_CREDENTIALS='{"type":"service_account",...}'  # Sealed
GOOGLE_CLOUD_PROJECT_ID=your-project-id
LOG_LEVEL=INFO
ENABLE_GOOGLE_DOCS_CONVERSION=true
```

**With OAuth2**:
```bash
GOOGLE_CREDENTIALS='{"type":"service_account",...}'  # Sealed
GOOGLE_OAUTH_CLIENT_ID=123-abc.apps.googleusercontent.com  # Sealed
GOOGLE_OAUTH_CLIENT_SECRET=GOCSPX-xyz  # Sealed
```

**Next Steps**: Deploy to Railway, test conversion, monitor logs, set up alerting.

---

**Documentation Complete**: All preparation files created. Ready for Architecture phase.
