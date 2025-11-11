# Google Cloud Service Account Setup Guide (Optional Alternative)

**Last Updated**: November 1, 2025
**Target Platform**: Google Cloud Platform
**Purpose**: Enable server-to-server authentication for Google Docs/Drive APIs
**Status**: Optional Alternative to OAuth2
**Priority**: Low (implement only if needed as fallback)

---

## Executive Summary

**NOTE**: This document describes an **optional alternative** to the primary OAuth2 authentication approach. OAuth2 "Sign in with Google" is the recommended primary implementation for user-owned documents with session-based storage.

Service accounts are a secondary authentication method for automated applications that need to access Google APIs without user interaction. Unlike OAuth2 user authentication, service accounts use cryptographic keys and don't require browser-based consent flows.

**When to Use Service Accounts** (for this application):
- As a fallback for users who don't want to sign in with Google
- For creating public shared documents via "anyone with link"
- For automated batch conversions (future enhancement)
- For API-only usage without browser interaction

**Why OAuth2 is Preferred**:
- Documents owned by user (not application)
- Natural quota scaling (per-user limits vs centralized limits)
- No persistent credential storage needed
- Better user experience
- Users can manage their own documents

**When Service Accounts Make Sense**:
- Users who prefer not to sign in
- Quick one-off conversions
- Anonymous usage scenarios
- Applications that create temporary/ephemeral documents

For the markdown converter use case, **OAuth2 is the primary approach** because:
1. Users want documents in their own Google Drive
2. User ownership eliminates sharing complexity
3. Quotas scale naturally with user base (60 writes/min per user vs 600/min total)
4. No database required for OAuth with session storage
5. Better long-term document management for users

---

## Prerequisites

Before starting, ensure you have:
- [ ] Google account (any Gmail or Workspace account)
- [ ] Access to Google Cloud Console
- [ ] Billing account (optional for basic usage, required for production quotas)
- [ ] Basic understanding of JSON and environment variables

**Cost Note**: Google Docs and Drive APIs are free to use. A billing account may be required to increase default quotas, but basic usage has no charges.

---

## Step 1: Create Google Cloud Project

### 1.1 Access Cloud Console

Navigate to: https://console.cloud.google.com/

### 1.2 Create New Project

1. Click the project dropdown in the top navigation bar
2. Click "New Project" button
3. Fill in project details:
   - **Project name**: `markdown-converter-prod` (or your preferred name)
   - **Organization**: Leave as "No organization" (for personal projects)
   - **Location**: Leave as "No organization"
4. Click "Create"

**Wait**: Project creation takes 30-60 seconds

### 1.3 Note Project ID

After creation, note your **Project ID** (not project name):
- Example: `markdown-converter-prod-437219`
- This ID is globally unique and immutable
- You'll use this in API calls and monitoring

---

## Step 2: Enable Required APIs

### 2.1 Navigate to API Library

1. From Cloud Console, open navigation menu (☰)
2. Go to: **APIs & Services** → **Library**

### 2.2 Enable Google Docs API

1. Search for "Google Docs API"
2. Click on "Google Docs API" from results
3. Click "Enable" button
4. Wait for activation (10-30 seconds)

### 2.3 Enable Google Drive API

1. Return to API Library
2. Search for "Google Drive API"
3. Click on "Google Drive API" from results
4. Click "Enable" button
5. Wait for activation

**Verification**:
- Navigate to **APIs & Services** → **Dashboard**
- Confirm both APIs appear in "Enabled APIs" list

---

## Step 3: Create Service Account

### 3.1 Navigate to Service Accounts

1. Open navigation menu (☰)
2. Go to: **IAM & Admin** → **Service Accounts**
3. Ensure correct project is selected in top dropdown

### 3.2 Create Account

1. Click "+ CREATE SERVICE ACCOUNT" button
2. Fill in service account details:

**Step 1: Service account details**
- **Service account name**: `markdown-converter-sa`
- **Service account ID**: Auto-generated (e.g., `markdown-converter-sa`)
- **Description**: `Service account for automated Google Docs creation in markdown converter application`
- Click "CREATE AND CONTINUE"

**Step 2: Grant access to project** (Optional)
- Skip this step (click "CONTINUE")
- Note: We'll grant specific API scopes during authentication, not IAM roles

**Step 3: Grant users access to service account** (Optional)
- Skip this step (click "DONE")

### 3.3 Note Service Account Email

After creation, you'll see your service account listed with an email address:
```
markdown-converter-sa@markdown-converter-prod-437219.iam.gserviceaccount.com
```

**Important**: Save this email address for reference

---

## Step 4: Create Service Account Key

### 4.1 Generate Key

1. Click on the service account email you just created
2. Navigate to the "KEYS" tab
3. Click "ADD KEY" → "Create new key"
4. Select key type: **JSON** (recommended)
5. Click "CREATE"

### 4.2 Download Credentials File

- File downloads automatically to your computer
- Default filename: `markdown-converter-prod-437219-1a2b3c4d5e6f.json`
- **CRITICAL**: This file contains private key material

**Security Warning**:
```
⚠️ NEVER commit this file to version control
⚠️ NEVER share this file publicly
⚠️ NEVER hardcode credentials in your application
```

### 4.3 Understand Credential File Structure

**Example credentials.json**:
```json
{
  "type": "service_account",
  "project_id": "markdown-converter-prod-437219",
  "private_key_id": "a1b2c3d4e5f6...",
  "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvQIBA...\n-----END PRIVATE KEY-----\n",
  "client_email": "markdown-converter-sa@markdown-converter-prod-437219.iam.gserviceaccount.com",
  "client_id": "123456789012345678901",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/markdown-converter-sa%40markdown-converter-prod-437219.iam.gserviceaccount.com",
  "universe_domain": "googleapis.com"
}
```

**Key Fields**:
- `client_email`: Service account identifier
- `private_key`: RSA private key for signing JWTs (keep secret!)
- `project_id`: Your GCP project
- `token_uri`: Where to exchange JWT for access token

---

## Step 5: Secure Credential Storage

### Local Development

#### 5.1 Create Credentials Directory

```bash
# In your project root
mkdir -p config
cd config
```

#### 5.2 Move Downloaded Credentials

```bash
# Rename to standard name
mv ~/Downloads/markdown-converter-prod-437219-*.json credentials.json
```

#### 5.3 Update .gitignore

Add to your `.gitignore`:
```
# Google Cloud credentials
config/credentials.json
credentials.json
**/service-account-*.json
```

**Verify**: Run `git status` and ensure credentials.json doesn't appear

### Production Deployment (Railway)

For Railway deployment, see `deployment-configuration.md` for detailed instructions. Summary:

**Option A: Environment Variable (Recommended)**
```bash
# Set entire JSON as sealed environment variable
GOOGLE_CREDENTIALS='{"type":"service_account",...}'
```

**Option B: File Path**
- Upload credentials.json to Railway volume
- Set environment variable to file path
- Ensure file permissions are secure (600)

---

## Step 6: Python Authentication Implementation

### 6.1 Install Required Libraries

```bash
pip install google-auth google-auth-oauthlib google-api-python-client
```

### 6.2 Basic Authentication Code

**app/utils/google_auth.py**:
```python
import os
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from typing import Tuple

# Define required scopes
SCOPES = [
    'https://www.googleapis.com/auth/documents',
    'https://www.googleapis.com/auth/drive'
]

def get_google_services() -> Tuple:
    """
    Create authenticated Google Docs and Drive service clients.

    Returns:
        Tuple of (docs_service, drive_service)

    Raises:
        FileNotFoundError: If credentials file not found
        ValueError: If credentials are invalid
    """
    # Try to load credentials from environment variable first
    creds_json = os.getenv('GOOGLE_CREDENTIALS')

    if creds_json:
        # Parse JSON from environment variable
        try:
            creds_info = json.loads(creds_json)
            credentials = service_account.Credentials.from_service_account_info(
                creds_info, scopes=SCOPES
            )
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid GOOGLE_CREDENTIALS JSON: {e}")
    else:
        # Fall back to file path
        creds_file = os.getenv('GOOGLE_CREDENTIALS_FILE', 'config/credentials.json')

        if not os.path.exists(creds_file):
            raise FileNotFoundError(
                f"Credentials file not found: {creds_file}. "
                "Set GOOGLE_CREDENTIALS or GOOGLE_CREDENTIALS_FILE environment variable."
            )

        credentials = service_account.Credentials.from_service_account_file(
            creds_file, scopes=SCOPES
        )

    # Build service clients
    docs_service = build('docs', 'v1', credentials=credentials)
    drive_service = build('drive', 'v3', credentials=credentials)

    return docs_service, drive_service


def create_public_document(title: str) -> dict:
    """
    Create a new Google Doc and make it publicly shareable.

    Args:
        title: Document title

    Returns:
        dict with keys: documentId, webViewLink
    """
    docs_service, drive_service = get_google_services()

    # Create document
    document = docs_service.documents().create(body={'title': title}).execute()
    document_id = document.get('documentId')

    # Set "anyone with link" permission
    permission = {
        'type': 'anyone',
        'role': 'reader'
    }
    drive_service.permissions().create(
        fileId=document_id,
        body=permission
    ).execute()

    # Get shareable link
    file_metadata = drive_service.files().get(
        fileId=document_id,
        fields='webViewLink'
    ).execute()

    return {
        'documentId': document_id,
        'webViewLink': file_metadata.get('webViewLink')
    }
```

### 6.3 Usage Example

```python
from app.utils.google_auth import create_public_document

# Create and share a document
result = create_public_document("My Markdown Conversion")
print(f"Document created: {result['webViewLink']}")
```

---

## Step 7: Test Authentication

### 7.1 Create Test Script

**scripts/test_google_auth.py**:
```python
#!/usr/bin/env python3
"""Test script for Google service account authentication."""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.utils.google_auth import get_google_services, create_public_document

def test_authentication():
    """Test basic authentication and API access."""
    print("Testing Google Cloud service account authentication...")

    try:
        # Test service creation
        print("\n1. Creating service clients...")
        docs_service, drive_service = get_google_services()
        print("✓ Successfully authenticated")

        # Test document creation
        print("\n2. Creating test document...")
        result = create_public_document("Auth Test Document")
        print(f"✓ Document created: {result['documentId']}")
        print(f"✓ Shareable link: {result['webViewLink']}")

        # Test document cleanup (optional)
        print("\n3. Cleaning up test document...")
        drive_service.files().delete(fileId=result['documentId']).execute()
        print("✓ Test document deleted")

        print("\n✅ All authentication tests passed!")
        return True

    except FileNotFoundError as e:
        print(f"\n❌ Credentials file not found: {e}")
        return False
    except ValueError as e:
        print(f"\n❌ Invalid credentials: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_authentication()
    sys.exit(0 if success else 1)
```

### 7.2 Run Test

```bash
# Set credentials path (if not using default location)
export GOOGLE_CREDENTIALS_FILE=config/credentials.json

# Run test
python scripts/test_google_auth.py
```

**Expected Output**:
```
Testing Google Cloud service account authentication...

1. Creating service clients...
✓ Successfully authenticated

2. Creating test document...
✓ Document created: 1a2b3c4d5e6f7g8h9i
✓ Shareable link: https://docs.google.com/document/d/1a2b3c4d5e6f7g8h9i/edit

3. Cleaning up test document...
✓ Test document deleted

✅ All authentication tests passed!
```

---

## Security Best Practices

### 1. Principle of Least Privilege

**DO**:
- Grant only required scopes (documents, drive)
- Use dedicated service account per application
- Avoid reusing service accounts across projects

**DON'T**:
- Grant owner or editor roles at project level
- Use default Compute Engine service account
- Share service accounts between environments (dev/prod)

### 2. Key Management

#### Rotation Schedule

**Recommended**: Rotate service account keys every 90 days

**Rotation Process**:
1. Create new key for service account
2. Update application configuration with new key
3. Deploy and verify new key works
4. Wait 24-48 hours for caches to clear
5. Delete old key from Cloud Console

**Automation**:
```python
# Check key age and warn
from datetime import datetime, timedelta
import json

def check_key_age(credentials_file: str) -> None:
    """Warn if service account key is older than 90 days."""
    with open(credentials_file) as f:
        creds = json.load(f)

    key_id = creds.get('private_key_id')

    # Note: Key creation timestamp not in JSON file
    # Query via Cloud Asset API or manually track in deployment docs
    # This is a placeholder for the concept

    print(f"Service account key ID: {key_id}")
    print("⚠️  Remember to rotate keys every 90 days")
```

#### Key Detection and Auto-Disable

Enable automatic key disabling for leaked credentials:

1. Navigate to: **IAM & Admin** → **Organization Policies**
2. Search for: "Disable service account key upload"
3. Enable policy
4. Configure: "Automatic disabling for leaked keys"

### 3. Monitoring and Auditing

#### Enable Cloud Audit Logs

1. Navigate to: **IAM & Admin** → **Audit Logs**
2. Find "Google Docs API" and "Google Drive API"
3. Enable "Admin Read" and "Data Read" logs
4. Save configuration

#### Monitor Service Account Usage

**Query recent authentication events**:
```bash
# Using gcloud CLI
gcloud logging read "protoPayload.authenticationInfo.principalEmail=markdown-converter-sa@PROJECT_ID.iam.gserviceaccount.com" \
    --limit 50 \
    --format json
```

**Set up alerts**:
1. Navigate to: **Logging** → **Logs Explorer**
2. Create query for service account usage
3. Click "Create alert" to set up notifications for unusual activity

### 4. Credential Storage in Code

**DO**:
```python
# Load from environment
creds_json = os.getenv('GOOGLE_CREDENTIALS')

# Load from secure file
with open('/secure/path/credentials.json') as f:
    creds = json.load(f)
```

**DON'T**:
```python
# Hardcoded credentials
credentials = {
    "private_key": "-----BEGIN PRIVATE KEY-----\nMIIE..."
}

# Committed to git
CREDS_FILE = '/app/config/credentials.json'  # File checked into repo
```

### 5. Network Security

Service account authentication happens server-side, so:

**DO**:
- Keep credentials on server only
- Use HTTPS for all API calls (built into client libraries)
- Restrict firewall rules to necessary outbound Google API endpoints

**DON'T**:
- Send credentials to client browser
- Expose credentials in API responses
- Log full credential contents (log key IDs only)

---

## Troubleshooting

### Error: "Credentials file not found"

**Cause**: Application can't locate credentials.json

**Solutions**:
1. Verify file path: `ls -la config/credentials.json`
2. Check environment variable: `echo $GOOGLE_CREDENTIALS_FILE`
3. Ensure file is readable: `chmod 600 config/credentials.json`

### Error: "Permission denied" (HTTP 403)

**Cause**: Service account lacks necessary permissions

**Solutions**:
1. Verify APIs are enabled:
   - Google Docs API
   - Google Drive API
2. Check scopes in code match required operations
3. Ensure service account hasn't been disabled

**Check API enablement**:
```bash
gcloud services list --enabled --project=PROJECT_ID | grep -E 'docs|drive'
```

### Error: "Invalid credentials" (HTTP 401)

**Cause**: Credentials are malformed or expired

**Solutions**:
1. Verify JSON is valid: `python -m json.tool credentials.json`
2. Check for extra whitespace or truncation
3. Regenerate key if file was corrupted

### Error: "Quota exceeded" (HTTP 429)

**Cause**: Exceeded API rate limits

**Solutions**:
1. Implement exponential backoff (see google-docs-api.md)
2. Request quota increase in Cloud Console
3. Optimize batch operations to reduce API calls

### Error: "Service account key expired"

**Cause**: Keys don't expire automatically, but may be disabled

**Solutions**:
1. Check Cloud Console → IAM → Service Accounts → Keys tab
2. Verify key status is "Active"
3. Create new key if disabled or deleted

---

## Advanced Configuration

### Domain-Wide Delegation (G Suite Only)

If you need service account to impersonate G Suite users:

#### 1. Enable Domain-Wide Delegation

1. Cloud Console → IAM & Admin → Service Accounts
2. Click on service account
3. Click "Show domain-wide delegation"
4. Click "Enable G Suite Domain-wide Delegation"
5. Note the Client ID

#### 2. Authorize in G Suite Admin Console

1. Navigate to: admin.google.com
2. Security → API Controls → Domain-wide Delegation
3. Click "Add new"
4. Enter Client ID from step 1
5. Add OAuth scopes (comma-separated):
   ```
   https://www.googleapis.com/auth/documents,https://www.googleapis.com/auth/drive
   ```
6. Click "Authorize"

#### 3. Use Delegation in Code

```python
from google.oauth2 import service_account

credentials = service_account.Credentials.from_service_account_file(
    'credentials.json',
    scopes=SCOPES,
    subject='user@example.com'  # G Suite user to impersonate
)
```

**Note**: For markdown converter, domain-wide delegation is NOT needed (documents owned by service account).

### Multiple Service Accounts

For production, consider separate service accounts for:
- **Production**: Live user conversions
- **Staging**: Testing and QA
- **Development**: Local development

**Benefits**:
- Isolate quota limits
- Separate audit logs
- Independent key rotation
- Environment-specific permissions

---

## Production Checklist

Before deploying to production:

- [ ] Service account created with descriptive name
- [ ] Google Docs API enabled
- [ ] Google Drive API enabled
- [ ] Service account key generated and downloaded
- [ ] Credentials stored securely (not in git)
- [ ] Environment variable configured in Railway
- [ ] Authentication tested successfully
- [ ] Cloud Audit Logs enabled
- [ ] Monitoring and alerts configured
- [ ] Key rotation schedule documented
- [ ] Backup of credential file stored securely
- [ ] Team members know how to access credentials in emergency
- [ ] Quota limits reviewed and increased if needed

---

## Cost Considerations

### Free Tier

Google Docs and Drive APIs have no per-request costs. You pay only for:
- Cloud Storage (minimal for credentials)
- Cloud Logging (if extensive auditing enabled)
- Cloud Monitoring (if alerts configured)

**Estimated monthly cost**: $0-5 for typical usage

### Quota Limits

Default quotas are generous for most applications:
- 600 write requests/min = 36,000/hour = 864,000/day
- At 1 document per request = 864K documents/day (free)

### Billing Requirements

A billing account may be required to:
- Request quota increases
- Access enterprise support
- Enable certain Cloud features

For basic API usage, billing is optional.

---

## Next Steps

**Recommended Primary Path**:
1. **Implement OAuth2 first**: See `oauth2-implementation.md` for primary implementation
2. **Review API patterns**: Read `google-docs-api.md` for API usage
3. **Implement conversion**: Follow `markdown-to-docs-conversion.md` for conversion logic
4. **Deploy with OAuth**: See `deployment-configuration.md` for Railway OAuth setup

**Optional Service Account Path** (implement later if needed):
1. Follow this guide to set up service account
2. Implement as fallback for non-authenticated users
3. Add UI toggle for "Sign in" vs "Convert without sign-in"

**Current Status**: Service account is an optional alternative. OAuth2 with session storage is the recommended primary implementation for user-owned documents.
