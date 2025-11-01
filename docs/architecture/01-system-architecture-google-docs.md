# System Architecture: Google Docs Integration

**Document Version**: 1.0
**Date**: 2025-11-01
**Phase**: PACT Architecture
**Status**: Ready for Implementation

---

## Executive Summary

This document defines the high-level architecture for integrating Google Docs conversion capability with OAuth2 authentication into the existing markdown converter application. The design prioritizes user data privacy through session-based authentication, maintains backward compatibility with existing DOCX/PDF conversion, and introduces a modern multi-select UI for format selection.

**Key Architectural Decisions**:

1. **OAuth2 as Primary Authentication**: Session-based token storage eliminates database dependency
2. **No Persistent User Data**: Fully stateless design compliant with GDPR
3. **Backward Compatible API**: Existing DOCX/PDF functionality unchanged
4. **Progressive UI Enhancement**: Works without JavaScript, enhanced with JS
5. **Service Account Optional**: Future addition for non-authenticated users

---

## System Context

### External Dependencies

```
┌─────────────────────────────────────────────────────────────┐
│                     External Systems                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────┐   ┌──────────────┐   ┌────────────────┐  │
│  │   Google    │   │   Google     │   │    Google      │  │
│  │   OAuth2    │   │   Docs API   │   │   Drive API    │  │
│  │  (Consent)  │   │    (v1)      │   │    (v3)        │  │
│  └──────┬──────┘   └──────┬───────┘   └────────┬───────┘  │
│         │                 │                      │          │
└─────────┼─────────────────┼──────────────────────┼──────────┘
          │                 │                      │
          ▼                 ▼                      ▼
┌─────────────────────────────────────────────────────────────┐
│              Markdown Converter Application                  │
│                                                              │
│  ┌────────────────┐  ┌────────────────┐  ┌───────────────┐ │
│  │  Flask Web App │  │ OAuth2 Handler │  │  Google Docs  │ │
│  │  (Gunicorn)    │──│  (Flask-Dance) │──│   Converter   │ │
│  └────────────────┘  └────────────────┘  └───────────────┘ │
│           │                  │                    │          │
│  ┌────────▼──────────────────▼────────────────────▼───────┐ │
│  │        Existing Converters (DOCX, PDF)                 │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
└─────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────┐
│                   Browser (User Agent)                       │
└─────────────────────────────────────────────────────────────┘
```

### System Boundaries

**In Scope**:
- OAuth2 user authentication flow
- Session-based token management
- Google Docs conversion via Docs API v1
- Multi-format selection UI
- Backward-compatible API endpoints

**Out of Scope**:
- User account management (no database)
- Conversion history tracking
- Document storage/archival
- Advanced document editing features
- Service account implementation (Phase 2)

---

## Component Architecture

### High-Level Component Diagram

```
┌────────────────────────────────────────────────────────────────┐
│                      Presentation Layer                        │
│                                                                 │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────────┐   │
│  │   Upload    │  │   Format     │  │   Authentication   │   │
│  │  Component  │  │  Selection   │  │    Status Badge    │   │
│  │   (HTML)    │  │   (Tiles)    │  │  (Sign In/Out)     │   │
│  └──────┬──────┘  └──────┬───────┘  └────────┬───────────┘   │
│         │                │                    │                │
└─────────┼────────────────┼────────────────────┼────────────────┘
          │                │                    │
          ▼                ▼                    ▼
┌────────────────────────────────────────────────────────────────┐
│                      Application Layer                         │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │               Flask Application Factory                   │ │
│  │                    (app/__init__.py)                      │ │
│  └───────────┬────────────────┬──────────────┬──────────────┘ │
│              │                │              │                 │
│  ┌───────────▼──────┐ ┌──────▼──────┐ ┌────▼──────────────┐  │
│  │  API Blueprint   │ │   Auth      │ │  Error Handlers   │  │
│  │  (/api/convert)  │ │ Blueprint   │ │  (Custom Errors)  │  │
│  │  (/api/download) │ │ (/auth/*)   │ │                   │  │
│  └───────────┬──────┘ └──────┬──────┘ └───────────────────┘  │
│              │                │                                │
└──────────────┼────────────────┼────────────────────────────────┘
               │                │
               ▼                ▼
┌────────────────────────────────────────────────────────────────┐
│                       Service Layer                            │
│                                                                 │
│  ┌───────────────┐  ┌──────────────┐  ┌───────────────────┐  │
│  │   Markdown    │  │    OAuth2    │  │   Google Docs     │  │
│  │   Converter   │  │   Service    │  │   Converter       │  │
│  │  (Existing)   │  │ (Flask-Dance)│  │    (NEW)          │  │
│  └───────────────┘  └──────────────┘  └───────────────────┘  │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
               │                │                    │
               ▼                ▼                    ▼
┌────────────────────────────────────────────────────────────────┐
│                     Integration Layer                          │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────────┐ │
│  │   Pandoc     │  │  Google API  │  │   Google Docs API   │ │
│  │  (pypandoc)  │  │   Client     │  │  (googleapiclient)  │ │
│  └──────────────┘  └──────────────┘  └─────────────────────┘ │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

#### 1. Frontend Components

**Upload Component** (`static/index.html`)
- File input with validation
- MIME type checking (.md, .markdown)
- File size validation

**Format Selection Tiles** (`static/index.html`)
- Multi-select checkbox cards
- Visual states (default, hover, selected, disabled)
- Authentication status integration
- Accessibility (ARIA, keyboard navigation)

**Authentication Status Badge**
- Display current auth state
- "Sign in with Google" button
- User profile display (when authenticated)
- "Sign out" functionality

#### 2. Application Layer

**Flask Application Factory** (`app/__init__.py`)
- Configure OAuth2 blueprints
- Register error handlers
- Apply security headers
- Session cookie configuration

**API Blueprint** (`app/api/routes.py`)
- `/api/convert` - Multi-format conversion endpoint
- `/api/download/<job_id>/<format>` - File download endpoint
- Request validation and error handling
- Multi-format response construction

**Auth Blueprint** (`app/auth/routes.py`) *NEW*
- `/auth/google` - Initiate OAuth flow
- `/auth/google/authorized` - OAuth callback handler
- `/auth/logout` - Clear session and revoke tokens
- `/auth/status` - Check authentication state (AJAX endpoint)

#### 3. Service Layer

**MarkdownConverter** (`app/converters/markdown_converter.py`) *Existing*
- DOCX conversion via pypandoc
- PDF conversion via weasyprint
- Front matter parsing
- No changes required

**GoogleDocsConverter** (`app/converters/google_docs_converter.py`) *NEW*
- Parse markdown content
- Map to Docs API requests
- Create document in user's Drive
- Apply formatting via batchUpdate API
- Set document permissions
- Return shareable link

**OAuth2 Service** (Flask-Dance)
- Manage OAuth flow state
- Token storage in session
- Automatic token refresh
- Error handling for auth failures

#### 4. Integration Layer

**Google API Client** (`google-api-python-client`)
- Docs API v1 service builder
- Drive API v3 service builder
- Credentials management
- Retry logic for rate limits

---

## Data Flow Architecture

### OAuth2 Authentication Flow

```
┌──────┐                ┌──────────┐                ┌──────────┐
│ User │                │   Flask  │                │  Google  │
│      │                │   App    │                │  OAuth2  │
└───┬──┘                └────┬─────┘                └────┬─────┘
    │                        │                           │
    │  1. Click "Sign in"    │                           │
    ├───────────────────────>│                           │
    │                        │                           │
    │                        │  2. Redirect to Google    │
    │                        │  (with client_id, scopes) │
    │                        ├──────────────────────────>│
    │                        │                           │
    │  3. Google consent screen                         │
    │<──────────────────────────────────────────────────┤
    │                        │                           │
    │  4. User approves      │                           │
    ├───────────────────────────────────────────────────>│
    │                        │                           │
    │                        │  5. Redirect with code    │
    │                        │<──────────────────────────┤
    │                        │                           │
    │                        │  6. Exchange code for     │
    │                        │  access + refresh tokens  │
    │                        ├──────────────────────────>│
    │                        │                           │
    │                        │<──────────────────────────┤
    │                        │  7. Return tokens         │
    │                        │                           │
    │                        │  8. Store in session      │
    │                        │  (encrypted cookie)       │
    │                        │                           │
    │  9. Redirect to app    │                           │
    │<───────────────────────┤                           │
    │                        │                           │
```

**Session Storage**:
- Tokens encrypted in Flask session cookie (client-side)
- No database required
- Automatic expiration on browser close
- HTTPS-only, httpOnly, SameSite=Lax flags

### Multi-Format Conversion Flow

```
┌──────┐              ┌──────────┐              ┌──────────┐
│ User │              │   Flask  │              │  Google  │
│      │              │   App    │              │   APIs   │
└───┬──┘              └────┬─────┘              └────┬─────┘
    │                      │                         │
    │  1. Upload .md       │                         │
    │  + Select formats    │                         │
    │  [DOCX, PDF, GDocs]  │                         │
    ├─────────────────────>│                         │
    │                      │                         │
    │                      │  2. Validate request    │
    │                      │  - Check auth for GDocs │
    │                      │  - Validate file        │
    │                      │                         │
    │                      │  3. Parse front matter  │
    │                      │  & markdown content     │
    │                      │                         │
    │                      │  4. Convert to DOCX     │
    │                      │  (pypandoc)             │
    │                      │                         │
    │                      │  5. Convert to PDF      │
    │                      │  (weasyprint)           │
    │                      │                         │
    │                      │  6. Convert to GDocs    │
    │                      │  (if selected)          │
    │                      │                         │
    │                      │  6a. Create document    │
    │                      ├────────────────────────>│
    │                      │                         │
    │                      │<────────────────────────┤
    │                      │  documentId             │
    │                      │                         │
    │                      │  6b. Apply content      │
    │                      │  (batchUpdate)          │
    │                      ├────────────────────────>│
    │                      │                         │
    │                      │<────────────────────────┤
    │                      │  success                │
    │                      │                         │
    │                      │  6c. Get share link     │
    │                      ├────────────────────────>│
    │                      │                         │
    │                      │<────────────────────────┤
    │                      │  webViewLink            │
    │                      │                         │
    │  7. Return results   │                         │
    │  {                   │                         │
    │    docx: {url},      │                         │
    │    pdf: {url},       │                         │
    │    gdocs: {link}     │                         │
    │  }                   │                         │
    │<─────────────────────┤                         │
    │                      │                         │
```

### Token Refresh Flow

```
┌──────────┐              ┌──────────┐
│   Flask  │              │  Google  │
│   App    │              │  OAuth2  │
└────┬─────┘              └────┬─────┘
     │                         │
     │  1. User makes request  │
     │  with expired token     │
     │                         │
     │  2. Check token expiry  │
     │  (Flask-Dance automatic)│
     │                         │
     │  3. Use refresh_token   │
     │  to get new access_token│
     ├────────────────────────>│
     │                         │
     │<────────────────────────┤
     │  4. New access_token    │
     │                         │
     │  5. Update session      │
     │  (automatic)            │
     │                         │
     │  6. Retry original      │
     │  request with new token │
     ├────────────────────────>│
     │                         │
     │<────────────────────────┤
     │  7. Success response    │
     │                         │
```

**Token Lifecycle**:
- Access token: 1 hour lifetime
- Refresh token: No expiration (until revoked)
- Automatic refresh handled by Flask-Dance
- Manual token revocation on logout

---

## Security Architecture

### Authentication Security

**Session Cookie Security**:
```python
# Configuration in app/config.py
SESSION_COOKIE_HTTPONLY = True   # Prevent XSS attacks
SESSION_COOKIE_SECURE = True     # HTTPS only
SESSION_COOKIE_SAMESITE = 'Lax'  # CSRF protection
SESSION_PERMANENT = False         # Expires on browser close
```

**OAuth2 Security**:
- State parameter validation (CSRF protection)
- PKCE flow for public clients (optional enhancement)
- Scope limitation (only `documents`, `drive.file`)
- HTTPS enforced in production
- Client secret sealed in Railway

**Secret Management**:
- `SECRET_KEY`: Strong, stable, sealed in Railway
- `GOOGLE_OAUTH_CLIENT_SECRET`: Sealed in Railway
- Never logged in plain text
- Rotated every 6 months (recommended)

### API Security

**Request Validation**:
- File type validation (`.md`, `.markdown`)
- File size limits (10MB default)
- UTF-8 encoding validation
- Content sanitization
- Path traversal protection

**Rate Limiting**:
- Google Docs: 60 writes/min per user (enforced by Google)
- Application-level rate limiting (optional future enhancement)
- Graceful degradation on quota exceeded

**Error Handling**:
- No sensitive data in error messages
- Generic errors to clients
- Detailed logging server-side
- Monitoring for auth failures

---

## Deployment Architecture

### Railway Platform Integration

```
┌─────────────────────────────────────────────────────────┐
│                    Railway Platform                      │
│                                                          │
│  ┌────────────────────────────────────────────────────┐ │
│  │              HTTPS Load Balancer                    │ │
│  └─────────────────────┬──────────────────────────────┘ │
│                        │                                 │
│  ┌─────────────────────▼──────────────────────────────┐ │
│  │         Gunicorn (2 workers, 2 threads)            │ │
│  │                                                     │ │
│  │  ┌─────────────────────────────────────────────┐  │ │
│  │  │  Flask Application                          │  │ │
│  │  │  - OAuth2 session management                │  │ │
│  │  │  - Google API clients (cached)              │  │ │
│  │  │  - Conversion services                      │  │ │
│  │  └─────────────────────────────────────────────┘  │ │
│  └─────────────────────────────────────────────────────┘ │
│                        │                                 │
│  ┌─────────────────────▼──────────────────────────────┐ │
│  │          Environment Variables (Sealed)            │ │
│  │  - SECRET_KEY                                      │ │
│  │  - GOOGLE_OAUTH_CLIENT_SECRET                     │ │
│  │  - GOOGLE_OAUTH_CLIENT_ID                         │ │
│  └────────────────────────────────────────────────────┘ │
│                                                          │
│  ┌────────────────────────────────────────────────────┐ │
│  │          Ephemeral File System                     │ │
│  │  /tmp/converted/<job_id>/                          │ │
│  │  - DOCX files (24hr expiration)                    │ │
│  │  - PDF files (24hr expiration)                     │ │
│  └────────────────────────────────────────────────────┘ │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

**Deployment Characteristics**:
- **Horizontal Scaling**: Session-based auth works across workers
- **Stateless Design**: No sticky sessions required
- **HTTPS**: Automatic via Railway
- **Health Checks**: `/health` endpoint monitors dependencies
- **Logging**: Stdout/stderr to Railway logs

### Environment Configuration

**Required Variables**:
```bash
# Core Flask
FLASK_ENV=production
SECRET_KEY=<64-char-hex-string>  # SEALED
LOG_LEVEL=INFO

# OAuth2 (Primary Authentication)
GOOGLE_OAUTH_CLIENT_ID=<client-id>.apps.googleusercontent.com
GOOGLE_OAUTH_CLIENT_SECRET=<client-secret>  # SEALED
GOOGLE_CLOUD_PROJECT_ID=<project-id>

# OAuth2 Settings
OAUTHLIB_RELAX_TOKEN_SCOPE=true
OAUTHLIB_INSECURE_TRANSPORT=false  # Must be false in production

# File Handling
MAX_FILE_SIZE=10485760
CONVERTED_FOLDER=/tmp/converted
```

**Optional Variables** (Future Service Account Support):
```bash
GOOGLE_CREDENTIALS='{"type":"service_account",...}'  # SEALED
```

---

## Scalability Considerations

### User Quota Scaling

**Advantage of OAuth2**:
- Each user gets 60 writes/min (Google's user quota)
- 100 concurrent users = 6,000 writes/min capacity
- Scales naturally with user base
- No centralized bottleneck

**Comparison to Service Account**:
- Service account: 600 writes/min total (shared across all users)
- OAuth2: 60 writes/min × number of users
- **OAuth2 scales 10x better with user growth**

### Session Management at Scale

**Session Storage** (Encrypted Cookies):
- No server-side session storage needed
- No Redis/database dependency
- Works across multiple Gunicorn workers
- Cookie size: ~1-2KB (well within 4KB limit)

**Scaling Strategy**:
1. Railway auto-scales workers based on load
2. Each worker independently validates sessions
3. No inter-worker communication required
4. Stateless design enables infinite horizontal scaling

### API Client Caching

```python
# Cache Google API service clients per worker
from functools import lru_cache

@lru_cache(maxsize=10)  # Cache up to 10 different credential sets
def get_google_services(token_hash):
    """
    Build Google API services with LRU caching.

    Args:
        token_hash: Hash of access token (for cache key)

    Returns:
        Tuple of (docs_service, drive_service)
    """
    credentials = Credentials(token=get_token_from_hash(token_hash))

    docs_service = build('docs', 'v1', credentials=credentials,
                        cache_discovery=False)
    drive_service = build('drive', 'v3', credentials=credentials,
                         cache_discovery=False)

    return docs_service, drive_service
```

**Benefits**:
- Reduces API client initialization time (200-300ms → 0ms)
- Improves response time for subsequent requests
- Memory efficient (bounded cache)

---

## Performance Targets

### Response Time Targets

| Operation | Target | Notes |
|-----------|--------|-------|
| OAuth login redirect | < 500ms | Flask-Dance handles efficiently |
| OAuth callback processing | < 1s | Token exchange with Google |
| DOCX conversion | < 3s | Existing performance |
| PDF conversion | < 5s | Existing performance |
| Google Docs creation | < 4s | API latency + formatting |
| Multi-format (all 3) | < 8s | Parallel processing opportunity |

### Optimization Strategies

**Parallel Conversion** (Future Enhancement):
```python
from concurrent.futures import ThreadPoolExecutor

def convert_to_all_formats(content, job_id):
    """Convert to multiple formats in parallel."""
    with ThreadPoolExecutor(max_workers=3) as executor:
        docx_future = executor.submit(convert_to_docx, content, job_id)
        pdf_future = executor.submit(convert_to_pdf, content, job_id)
        gdocs_future = executor.submit(convert_to_gdocs, content, job_id)

        return {
            'docx': docx_future.result(),
            'pdf': pdf_future.result(),
            'gdocs': gdocs_future.result()
        }
```

**Expected Improvement**:
- Sequential: 3s + 5s + 4s = 12s
- Parallel: max(3s, 5s, 4s) = 5s
- **60% reduction** in total conversion time

---

## Monitoring and Observability

### Health Check Enhancement

```python
@app.route('/health')
def health_check():
    """
    Enhanced health check including OAuth and Google API status.
    """
    health = {
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'features': {
            'docx_conversion': True,
            'pdf_conversion': True,
            'google_docs_conversion': app.config['ENABLE_GOOGLE_DOCS'],
            'oauth_configured': bool(app.config['GOOGLE_OAUTH_CLIENT_ID'])
        },
        'dependencies': {}
    }

    # Check Google API connectivity (lightweight)
    if app.config['ENABLE_GOOGLE_DOCS']:
        try:
            # Verify OAuth client config (doesn't make API call)
            client_id = app.config['GOOGLE_OAUTH_CLIENT_ID']
            health['dependencies']['google_oauth'] = 'configured'
        except Exception as e:
            health['dependencies']['google_oauth'] = 'error'
            health['status'] = 'degraded'

    status_code = 200 if health['status'] == 'healthy' else 503
    return jsonify(health), status_code
```

### Logging Strategy

**OAuth Events**:
```python
logger.info(f"OAuth login initiated for session {session_id}")
logger.info(f"OAuth callback successful, user authenticated")
logger.warning(f"OAuth token expired, refreshing for session {session_id}")
logger.error(f"OAuth authentication failed: {error_code}", exc_info=True)
```

**Conversion Events**:
```python
logger.info(f"Google Docs conversion started: job_id={job_id}, size={file_size}")
logger.info(f"Google Docs document created: doc_id={doc_id}")
logger.warning(f"Rate limit approaching: {requests_remaining} requests left")
logger.error(f"Google API error: {error}", exc_info=True)
```

**Security Events**:
```python
logger.warning(f"Authentication required for Google Docs conversion")
logger.warning(f"Invalid OAuth state parameter detected")
logger.error(f"Session validation failed: possible CSRF attack")
```

---

## Risk Mitigation

### Identified Risks and Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|-----------|------------|
| OAuth token expiration during conversion | Medium | Medium | Automatic refresh before API calls |
| User revokes OAuth mid-session | Medium | Low | Graceful error handling, clear messaging |
| Google API rate limits exceeded | Medium | Low | Per-user quotas, retry logic, user feedback |
| Session cookie size limits | Low | Very Low | OAuth tokens fit within 4KB limit |
| SECRET_KEY regeneration | High | Low | Sealed Railway variable, documentation |
| Google API deprecation | Medium | Very Low | Version pinning, monitoring release notes |

### Error Recovery Strategies

**Token Refresh Failure**:
```python
try:
    credentials = get_valid_credentials()
except RefreshError:
    # Clear invalid session
    session.clear()
    # Redirect to login
    return redirect(url_for('google.login'))
```

**API Rate Limit**:
```python
try:
    result = docs_service.documents().create(...).execute()
except HttpError as e:
    if e.resp.status == 429:
        # Quota exceeded
        return jsonify({
            'error': 'Google Docs conversion temporarily unavailable',
            'code': 'QUOTA_EXCEEDED',
            'retry_after': 60
        }), 429
```

**Network Timeout**:
```python
from google.api_core import retry

@retry.Retry(predicate=retry.if_transient_error, deadline=30.0)
def create_document_with_retry(docs_service, title):
    return docs_service.documents().create(body={'title': title}).execute()
```

---

## Testing Strategy

### Unit Testing

**Components to Test**:
- OAuth flow state management
- Token refresh logic
- Multi-format request validation
- Google Docs converter markdown parsing
- API request construction

**Example Test**:
```python
def test_multiformat_conversion():
    """Test conversion with multiple formats selected."""
    response = client.post('/api/convert', data={
        'file': (io.BytesIO(b'# Test\nContent'), 'test.md'),
        'formats': ['docx', 'pdf']  # Note: getlist behavior
    })

    assert response.status_code == 200
    data = response.get_json()
    assert 'docx' in data['formats']
    assert 'pdf' in data['formats']
    assert 'gdocs' not in data['formats']
```

### Integration Testing

**OAuth Flow Testing**:
```python
def test_oauth_redirect():
    """Test OAuth login redirect."""
    response = client.get('/auth/google')
    assert response.status_code == 302
    assert 'accounts.google.com' in response.location

def test_oauth_callback():
    """Test OAuth callback with mock token."""
    with mock.patch('flask_dance.contrib.google.google.authorized', True):
        response = client.get('/auth/google/authorized?code=test')
        assert response.status_code == 302
```

**Google Docs Conversion Testing**:
```python
@mock.patch('app.converters.google_docs_converter.build')
def test_gdocs_conversion(mock_build):
    """Test Google Docs conversion with mocked API."""
    mock_docs = mock.Mock()
    mock_docs.documents().create().execute.return_value = {'documentId': 'test-id'}
    mock_build.return_value = mock_docs

    converter = GoogleDocsConverter(mock_docs, mock.Mock())
    result = converter.convert('# Test', 'Test Doc')

    assert result['documentId'] == 'test-id'
```

### End-to-End Testing

**Manual Test Plan**:
1. Upload markdown file
2. Click "Sign in with Google"
3. Complete OAuth consent
4. Select Google Docs format
5. Submit conversion
6. Verify document created in Drive
7. Verify document formatting
8. Sign out
9. Verify Google Docs option disabled

---

## Migration and Rollout Plan

### Phase 1: Infrastructure Setup (Week 1)

- [ ] Install dependencies (`Flask-Dance`, `google-api-python-client`)
- [ ] Configure OAuth client in Google Cloud Console
- [ ] Set up Railway environment variables
- [ ] Update OAuth redirect URIs

### Phase 2: Backend Implementation (Week 2-3)

- [ ] Implement OAuth blueprints
- [ ] Create GoogleDocsConverter class
- [ ] Update `/api/convert` endpoint for multi-format
- [ ] Add authentication status endpoint
- [ ] Unit tests for new components

### Phase 3: Frontend Implementation (Week 3-4)

- [ ] Design format selection tiles
- [ ] Implement authentication UI
- [ ] Add JavaScript for auth checking
- [ ] Responsive design testing
- [ ] Accessibility audit

### Phase 4: Integration Testing (Week 4)

- [ ] OAuth flow end-to-end testing
- [ ] Multi-format conversion testing
- [ ] Error handling validation
- [ ] Performance testing
- [ ] Security audit

### Phase 5: Deployment (Week 5)

- [ ] Deploy to Railway staging
- [ ] Update Google OAuth redirect URIs
- [ ] Test in production environment
- [ ] Monitor logs and metrics
- [ ] Deploy to production

### Phase 6: Monitoring (Ongoing)

- [ ] Monitor OAuth success/failure rates
- [ ] Track Google API quota usage
- [ ] Monitor conversion performance
- [ ] Collect user feedback
- [ ] Plan service account implementation (optional Phase 2)

---

## Success Criteria

### Functional Criteria

- [ ] Users can sign in with Google OAuth2
- [ ] OAuth tokens stored securely in sessions
- [ ] Markdown converts to Google Docs with proper formatting
- [ ] Documents created in user's Drive (not shared from service account)
- [ ] Multi-format selection allows DOCX + PDF + Google Docs
- [ ] Backward compatibility: existing DOCX/PDF conversions work unchanged
- [ ] Google Docs option disabled when not authenticated

### Non-Functional Criteria

- [ ] OAuth login completes in < 5 seconds
- [ ] Google Docs conversion completes in < 4 seconds
- [ ] Session cookies < 4KB
- [ ] Zero persistent user data stored
- [ ] WCAG 2.2 AA accessibility compliance
- [ ] Mobile-responsive UI
- [ ] Security headers properly configured

### Business Criteria

- [ ] No additional infrastructure costs (no database)
- [ ] Scales with user growth (per-user quotas)
- [ ] Privacy-compliant (GDPR)
- [ ] No Google verification required for initial launch (test users)

---

## Appendix

### Technology Stack Summary

**New Dependencies**:
```
Flask-Dance==7.0.0
google-api-python-client>=2.149.0
google-auth>=2.35.0
google-auth-oauthlib>=1.2.3
```

**Existing Dependencies** (No Changes):
```
Flask==3.0.3
gunicorn==22.0.0
pypandoc-binary==1.13
python-frontmatter==1.0.1
markdown==3.6
weasyprint==62.3
```

### API Endpoint Summary

**New Endpoints**:
- `GET /auth/google` - Initiate OAuth login
- `GET /auth/google/authorized` - OAuth callback
- `GET /auth/logout` - Sign out and revoke tokens
- `GET /auth/status` - Check authentication state (AJAX)

**Modified Endpoints**:
- `POST /api/convert` - Now accepts `formats` array instead of `format` string

**Unchanged Endpoints**:
- `GET /api/download/<job_id>/<format>` - Download converted files
- `POST /api/cleanup` - Cleanup old files
- `GET /health` - Health check (enhanced with OAuth status)

### Configuration Reference

**Session Security** (`app/config.py`):
```python
SECRET_KEY = os.getenv('SECRET_KEY')  # 64-char hex, sealed
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_PERMANENT = False
```

**OAuth Configuration** (`app/config.py`):
```python
GOOGLE_OAUTH_CLIENT_ID = os.getenv('GOOGLE_OAUTH_CLIENT_ID')
GOOGLE_OAUTH_CLIENT_SECRET = os.getenv('GOOGLE_OAUTH_CLIENT_SECRET')
OAUTHLIB_RELAX_TOKEN_SCOPE = True
OAUTHLIB_INSECURE_TRANSPORT = False  # Production only
```

---

**Architecture Document Status**: COMPLETE
**Ready for Implementation**: YES
**Next Phase**: Detailed component design documents
