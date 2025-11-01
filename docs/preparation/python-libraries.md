# Python Libraries for Google Docs Integration

**Last Updated**: November 1, 2025
**Python Version**: 3.7-3.14 supported

---

## Executive Summary

Integrating Google Docs conversion requires several Python libraries for authentication, API access, and markdown processing. All libraries are actively maintained with recent updates in October 2025.

**Core Dependencies**:
- `google-api-python-client` - Google API client library
- `google-auth` - Authentication and authorization
- `google-auth-oauthlib` - OAuth2 flows (if implementing user auth)
- `markgdoc` - Optional helper for markdown conversion

---

## Required Libraries

### 1. google-api-python-client

**Purpose**: Core library for accessing Google APIs (Docs, Drive, etc.)

**Latest Version**: Actively maintained (check PyPI for latest)

**Installation**:
```bash
pip install google-api-python-client
```

**Key Features**:
- Discovery-based API client (auto-generates methods from API schema)
- Supports all Google APIs
- Built-in retry logic
- HTTP/2 support

**Usage Example**:
```python
from googleapiclient.discovery import build
from google.oauth2 import service_account

credentials = service_account.Credentials.from_service_account_file(
    'credentials.json',
    scopes=['https://www.googleapis.com/auth/documents']
)

# Build Docs service
docs_service = build('docs', 'v1', credentials=credentials)

# Create document
document = docs_service.documents().create(body={'title': 'My Doc'}).execute()
```

**Documentation**: https://googleapis.github.io/google-api-python-client/docs/

**GitHub**: https://github.com/googleapis/google-api-python-client

---

### 2. google-auth

**Purpose**: Authentication and credential management

**Latest Version**: 1.2.3 (Released October 30, 2025)

**Installation**:
```bash
pip install google-auth
```

**Key Features**:
- Service account authentication
- User credential management
- Automatic token refresh
- Multiple credential types support

**Usage Example**:
```python
from google.oauth2 import service_account

SCOPES = [
    'https://www.googleapis.com/auth/documents',
    'https://www.googleapis.com/auth/drive'
]

# From file
credentials = service_account.Credentials.from_service_account_file(
    'credentials.json',
    scopes=SCOPES
)

# From JSON dict (environment variable)
import json
creds_dict = json.loads(os.getenv('GOOGLE_CREDENTIALS'))
credentials = service_account.Credentials.from_service_account_info(
    creds_dict,
    scopes=SCOPES
)
```

**Documentation**: https://google-auth.readthedocs.io/

**GitHub**: https://github.com/googleapis/google-auth-library-python

---

### 3. google-auth-oauthlib

**Purpose**: OAuth2 authentication flows for user login

**Latest Version**: 1.2.3 (Released October 30, 2025)

**Installation**:
```bash
pip install google-auth-oauthlib
```

**Key Features**:
- OAuth2 web server flow
- OAuth2 installed app flow
- Token management
- Integration with google-auth

**Usage Example**:
```python
from google_auth_oauthlib.flow import Flow

flow = Flow.from_client_secrets_file(
    'client_secrets.json',
    scopes=['https://www.googleapis.com/auth/documents']
)

flow.redirect_uri = 'https://your-app.com/oauth/callback'

# Get authorization URL
authorization_url, state = flow.authorization_url(
    access_type='offline',
    include_granted_scopes='true'
)
```

**Documentation**: https://google-auth-oauthlib.readthedocs.io/

**GitHub**: https://github.com/googleapis/google-auth-library-python-oauthlib

**Note**: Only required if implementing OAuth2 user authentication (optional feature)

---

### 4. markgdoc (Optional)

**Purpose**: Simplified markdown to Google Docs conversion

**Latest Version**: 1.0.1 (Released August 27, 2024)

**Installation**:
```bash
pip install markgdoc
```

**Key Features**:
- Pre-built markdown element handlers
- Automatic API request generation
- Support for common markdown syntax
- GPL v3 licensed

**Supported Syntax**:
- Headers (H1-H6)
- Bold, italic, strikethrough
- Lists (ordered/unordered)
- Tables
- Horizontal lines
- Hyperlinks
- Paragraphs

**Usage Example**:
```python
from markgdoc import convert_to_google_docs

result = convert_to_google_docs(
    markdown_content="# Hello\n\nThis is **bold**",
    title="My Document",
    docs_service=docs_service,
    credentials_file='credentials.json',
    scopes=SCOPES
)

print(result['url'])  # Document URL
```

**Limitations**:
- No code block formatting
- No image support
- Limited table styling
- GPL v3 license may be restrictive

**Documentation**: https://github.com/awesomeadi00/MarkGDoc

**PyPI**: https://pypi.org/project/markgdoc/

---

## Existing Project Dependencies

Your markdown converter already uses these libraries:

### 5. python-frontmatter

**Current**: Already in requirements.txt

**Purpose**: Parse YAML front matter from markdown files

**Usage in Google Docs conversion**:
```python
import frontmatter

post = frontmatter.loads(markdown_content)
metadata = post.metadata  # {'title': 'My Doc', 'author': 'John'}
content = post.content    # Markdown without front matter
```

**No changes needed** - continue using existing dependency

---

### 6. markdown

**Current**: Already in requirements.txt

**Purpose**: Convert markdown to HTML (used for PDF conversion)

**Potential use for Google Docs**:
```python
import markdown

md = markdown.Markdown(extensions=['extra', 'codehilite', 'toc'])
html = md.convert(markdown_text)
# Parse HTML tree to generate Docs API requests
```

**Note**: Direct API approach is more reliable than HTML parsing

---

## Version Compatibility Matrix

| Library | Minimum Python | Latest Python | Latest Version | Release Date |
|---------|---------------|---------------|----------------|--------------|
| google-api-python-client | 3.7 | 3.14 | Latest | Active |
| google-auth | 3.7 | 3.14 | 1.2.3 | Oct 30, 2025 |
| google-auth-oauthlib | 3.7 | 3.14 | 1.2.3 | Oct 30, 2025 |
| markgdoc | 3.7 | 3.14 | 1.0.1 | Aug 27, 2024 |
| python-frontmatter | 2.7+ | 3.14 | 1.1.0 | Existing |
| markdown | 3.6+ | 3.14 | 3.7 | Existing |

**Project Python Version**: 3.11 (based on Dockerfile)
**Compatibility**: All libraries fully compatible ✅

---

## Updated requirements.txt

Add these lines to your existing `requirements.txt`:

```txt
# Existing dependencies
Flask==3.1.0
gunicorn==23.0.0
pypandoc-binary==1.15
python-frontmatter==1.1.0
markdown==3.7
weasyprint==63.1
# ... other existing dependencies

# Google Docs integration
google-api-python-client>=2.149.0
google-auth>=2.35.0
google-auth-oauthlib>=1.2.3  # Only if implementing OAuth2

# Optional: Markdown to Docs helper
markgdoc==1.0.1
```

**Installation**:
```bash
pip install -r requirements.txt
```

---

## Installation and Setup

### Development Environment

```bash
# Activate virtual environment
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows

# Install new dependencies
pip install google-api-python-client google-auth

# Optional: OAuth2 support
pip install google-auth-oauthlib

# Optional: markgdoc helper
pip install markgdoc

# Freeze updated requirements
pip freeze > requirements.txt
```

### Railway Deployment

Railway automatically installs from `requirements.txt` during build:

1. Update `requirements.txt` with new dependencies
2. Commit and push to git
3. Railway detects changes and rebuilds
4. New packages installed automatically

**Build Time Impact**:
- `google-api-python-client`: ~15 seconds
- `google-auth`: ~5 seconds
- `markgdoc`: ~3 seconds
- **Total increase**: ~25-30 seconds

---

## Code Examples

### Basic Document Creation

```python
"""
Simple example: Create Google Doc with service account
"""
from googleapiclient.discovery import build
from google.oauth2 import service_account
import os
import json

# Load credentials
creds_json = os.getenv('GOOGLE_CREDENTIALS')
creds_dict = json.loads(creds_json)

credentials = service_account.Credentials.from_service_account_info(
    creds_dict,
    scopes=[
        'https://www.googleapis.com/auth/documents',
        'https://www.googleapis.com/auth/drive'
    ]
)

# Build services
docs = build('docs', 'v1', credentials=credentials)
drive = build('drive', 'v3', credentials=credentials)

# Create document
doc = docs.documents().create(body={'title': 'Test Document'}).execute()
doc_id = doc['documentId']

# Add content
requests = [{
    'insertText': {
        'location': {'index': 1},
        'text': 'Hello from Python!'
    }
}]

docs.documents().batchUpdate(
    documentId=doc_id,
    body={'requests': requests}
).execute()

# Make public
drive.permissions().create(
    fileId=doc_id,
    body={'type': 'anyone', 'role': 'reader'}
).execute()

# Get link
file = drive.files().get(fileId=doc_id, fields='webViewLink').execute()
print(f"Document: {file['webViewLink']}")
```

### Retry Logic with google-api-core

```python
"""
Implement retry logic for API calls
"""
from google.api_core import retry
from googleapiclient.errors import HttpError

# Define custom retry predicate
def is_retryable(exception):
    """Check if exception is retryable."""
    if isinstance(exception, HttpError):
        return exception.resp.status in [429, 500, 502, 503, 504]
    return False

# Create retry decorator
retry_policy = retry.Retry(
    predicate=is_retryable,
    initial=1.0,  # Initial delay
    maximum=32.0,  # Max delay
    multiplier=2.0,  # Exponential backoff
    deadline=120.0  # Total timeout
)

# Apply to function
@retry_policy
def create_document(title):
    return docs.documents().create(body={'title': title}).execute()

# Use with automatic retry
doc = create_document("My Document")
```

### Token Refresh (OAuth2)

```python
"""
Automatic token refresh for OAuth2
"""
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

def get_refreshed_credentials(token_dict):
    """
    Get valid credentials, refreshing if expired.

    Args:
        token_dict: Dict with token, refresh_token, client_id, client_secret

    Returns:
        Valid Credentials object
    """
    credentials = Credentials(
        token=token_dict['token'],
        refresh_token=token_dict['refresh_token'],
        token_uri='https://oauth2.googleapis.com/token',
        client_id=token_dict['client_id'],
        client_secret=token_dict['client_secret']
    )

    # Refresh if expired
    if credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())

    return credentials
```

---

## Troubleshooting

### Import Errors

**Error**: `ImportError: No module named 'googleapiclient'`

**Solution**:
```bash
pip install google-api-python-client
# Note: Package name is different from import name
```

**Error**: `ImportError: No module named 'google.auth'`

**Solution**:
```bash
pip install google-auth
```

### Version Conflicts

**Error**: `ERROR: pip's dependency resolver does not currently take into account all the packages that are installed`

**Solution**:
```bash
# Upgrade pip
pip install --upgrade pip

# Install with --upgrade flag
pip install --upgrade google-api-python-client google-auth
```

### Railway Build Failures

**Error**: Build fails installing google-api-python-client

**Solution**:
1. Check Python version in Dockerfile (should be 3.7+)
2. Ensure pip is up to date in Dockerfile:
   ```dockerfile
   RUN pip install --upgrade pip
   ```
3. Pin specific versions in requirements.txt if needed

---

## Performance Considerations

### Library Size

| Library | Installed Size | Impact on Build |
|---------|---------------|-----------------|
| google-api-python-client | ~15 MB | Moderate |
| google-auth | ~2 MB | Minimal |
| google-auth-oauthlib | ~1 MB | Minimal |
| markgdoc | ~50 KB | Negligible |

**Total additional size**: ~18 MB (acceptable for Railway)

### Import Time

First import of `googleapiclient` adds ~200-300ms to cold start time. Subsequent imports are cached.

**Optimization**: Import at module level, not in functions:
```python
# Good - import once at module level
from googleapiclient.discovery import build

def create_doc():
    service = build('docs', 'v1', credentials=creds)

# Bad - import in function (slower)
def create_doc():
    from googleapiclient.discovery import build
    service = build('docs', 'v1', credentials=creds)
```

---

## Security Considerations

### Dependency Scanning

Monitor dependencies for vulnerabilities:

```bash
# Install safety
pip install safety

# Check for known vulnerabilities
safety check

# Check specific packages
safety check --json | jq '.vulnerabilities[] | select(.package_name == "google-api-python-client")'
```

### Keeping Dependencies Updated

```bash
# Check for outdated packages
pip list --outdated

# Update specific packages
pip install --upgrade google-api-python-client google-auth

# Update all
pip install --upgrade -r requirements.txt
```

### License Compliance

| Library | License | Commercial Use | Notes |
|---------|---------|----------------|-------|
| google-api-python-client | Apache 2.0 | ✅ Yes | Permissive |
| google-auth | Apache 2.0 | ✅ Yes | Permissive |
| google-auth-oauthlib | Apache 2.0 | ✅ Yes | Permissive |
| markgdoc | GPL v3 | ⚠️ Limited | Copyleft - may require source disclosure |

**Recommendation**: If using `markgdoc`, understand GPL v3 implications or implement custom converter.

---

## Alternative Libraries

### Not Recommended

1. **PyDrive** - Older Drive API wrapper, not maintained
2. **gspread** - Sheets-specific, not for Docs
3. **python-docx** - Word files only, not Google Docs

### Future Considerations

1. **google-cloud-storage** - If implementing document caching
2. **celery** - If adding background job processing
3. **redis** - If adding request queuing for rate limiting

---

## Testing Dependencies

For development and testing:

```txt
# requirements-dev.txt
pytest==8.3.3
pytest-cov==6.0.0
pytest-mock==3.14.0
responses==0.25.3  # Mock HTTP responses
```

**Mock Google API Responses**:
```python
import responses
import json

@responses.activate
def test_create_document():
    """Test document creation with mocked API."""
    # Mock create endpoint
    responses.add(
        responses.POST,
        'https://docs.googleapis.com/v1/documents',
        json={'documentId': 'fake-doc-id'},
        status=200
    )

    # Test code
    result = docs.documents().create(body={'title': 'Test'}).execute()
    assert result['documentId'] == 'fake-doc-id'
```

---

## Summary

**Minimal Installation** (Service Account Only):
```bash
pip install google-api-python-client google-auth
```

**With OAuth2 Support**:
```bash
pip install google-api-python-client google-auth google-auth-oauthlib
```

**With markgdoc Helper**:
```bash
pip install google-api-python-client google-auth markgdoc
```

**Recommended for Production**:
```bash
pip install google-api-python-client>=2.149.0 google-auth>=2.35.0
```

**Next Steps**: Review `deployment-configuration.md` for Railway setup and environment configuration.
