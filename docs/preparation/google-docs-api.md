# Google Docs API and Google Drive API Documentation

**Last Updated**: November 1, 2025
**API Versions**: Google Docs API v1, Google Drive API v3
**Official Documentation**:
- Docs API: https://developers.google.com/docs/api/reference/rest
- Drive API: https://developers.google.com/drive/api/v3/reference

---

## Executive Summary

The Google Docs API enables programmatic creation and modification of Google Docs documents. Combined with the Google Drive API for permission management, these APIs provide complete functionality for creating professionally formatted documents and making them shareable via public links. Both APIs are mature, well-documented, and actively maintained with the latest updates from October 2025.

**Key Capabilities**:
- Create new documents programmatically
- Insert and format text with rich styling
- Add structural elements (tables, lists, images)
- Batch operations for efficient multi-step modifications
- Fine-grained permission control via Drive API
- Public sharing with "anyone with link" access

---

## Google Docs API Overview

### Service Endpoint

All API calls use the base endpoint:
```
https://docs.googleapis.com
```

### Document Structure

Google Docs documents are composed of hierarchical structural elements:

#### Core Components

1. **Body**: Main document content container
   - Contains all structural elements (paragraphs, tables, section breaks)
   - Uses a flat index system (each character has an index position)

2. **DocumentStyle**: Overall document formatting
   - Page size and margins
   - Default paragraph and text styles
   - Background color

3. **Headers and Footers**: Repeating sections
   - Can have different headers for first page, even/odd pages
   - Support all content types (text, images, tables)

4. **Footnotes**: Reference elements
   - Automatically numbered
   - Can contain formatted content

5. **Lists**: Structured list elements
   - Supports nested lists with multiple levels
   - Customizable bullet/numbering styles

6. **Tables**: Tabular data containers
   - Dynamic row/column structure
   - Cells contain their own content elements

#### Document Identification

**Document ID**: Unique identifier extracted from the document URL
```
https://docs.google.com/document/d/{DOCUMENT_ID}/edit
```

The document ID remains stable even when the document is renamed or moved.

#### Indexing System

All content uses zero-based indexing from the document start:

- **Index 1**: First character in a new document (index 0 is reserved)
- **startIndex**: Beginning of a range (inclusive)
- **endIndex**: End of a range (exclusive)

Example: Text "Hello" at index 1-6 means:
- startIndex: 1
- endIndex: 6 (not included, so last character is at index 5)

**Important**: Indexes shift as content is added or removed. Use batch updates to apply multiple changes atomically.

---

## Core API Operations

### Document Creation

**Endpoint**: `POST https://docs.googleapis.com/v1/documents`

**Request Body**:
```json
{
  "title": "My New Document"
}
```

**Response**:
```json
{
  "documentId": "1a2b3c4d5e6f7g8h9i",
  "title": "My New Document",
  "body": {
    "content": [...]
  },
  "revisionId": "ALm37WX8...",
  "suggestionsViewMode": "SUGGESTIONS_INLINE"
}
```

**Python Example**:
```python
from googleapiclient.discovery import build
from google.oauth2 import service_account

SCOPES = ['https://www.googleapis.com/auth/documents']
SERVICE_ACCOUNT_FILE = 'path/to/credentials.json'

credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)

docs_service = build('docs', 'v1', credentials=credentials)

document = docs_service.documents().create(body={'title': 'My New Document'}).execute()
document_id = document.get('documentId')
print(f'Created document with ID: {document_id}')
```

### Batch Update Operations

**Endpoint**: `POST https://docs.googleapis.com/v1/documents/{documentId}:batchUpdate`

The batchUpdate method is the primary way to modify documents. It accepts an array of requests that are executed atomically (all succeed or all fail).

**Request Structure**:
```json
{
  "requests": [
    {
      "insertText": {
        "location": {"index": 1},
        "text": "Hello World"
      }
    },
    {
      "updateTextStyle": {
        "range": {"startIndex": 1, "endIndex": 6},
        "textStyle": {"bold": true},
        "fields": "bold"
      }
    }
  ]
}
```

**Response**:
```json
{
  "documentId": "1a2b3c4d5e6f7g8h9i",
  "replies": [
    {},
    {}
  ],
  "writeControl": {
    "requiredRevisionId": "ALm37WX9..."
  }
}
```

#### Available Request Types

**Text Operations**:
- `InsertTextRequest`: Add text at specific index
- `DeleteContentRangeRequest`: Remove content range
- `ReplaceAllTextRequest`: Find and replace text

**Formatting**:
- `UpdateTextStyleRequest`: Apply text formatting (bold, italic, font, color)
- `UpdateParagraphStyleRequest`: Format paragraphs (alignment, spacing, indentation)
- `CreateParagraphBulletsRequest`: Convert paragraphs to lists
- `DeleteParagraphBulletsRequest`: Remove list formatting

**Structural Elements**:
- `InsertTableRequest`: Add table with specified rows/columns
- `InsertTableRowRequest`: Add row to existing table
- `InsertTableColumnRequest`: Add column to existing table
- `DeleteTableRowRequest`: Remove table row
- `DeleteTableColumnRequest`: Remove table column
- `InsertInlineImageRequest`: Add image from URL
- `InsertPageBreakRequest`: Add page break
- `InsertSectionBreakRequest`: Create new section

**Document Structure**:
- `CreateHeaderRequest`: Add header section
- `CreateFooterRequest`: Add footer section
- `CreateFootnoteRequest`: Insert footnote
- `CreateNamedRangeRequest`: Label document region
- `UpdateDocumentStyleRequest`: Modify document-level styles

### Reading Document Content

**Endpoint**: `GET https://docs.googleapis.com/v1/documents/{documentId}`

**Query Parameters**:
- `suggestionsViewMode`: How to render suggestions (SUGGESTIONS_INLINE, PREVIEW_SUGGESTIONS_ACCEPTED, PREVIEW_WITHOUT_SUGGESTIONS)

**Response**: Returns complete document structure including all content and formatting

**Python Example**:
```python
document = docs_service.documents().get(documentId=document_id).execute()
title = document.get('title')
body_content = document.get('body').get('content')

# Iterate through structural elements
for element in body_content:
    if 'paragraph' in element:
        paragraph = element['paragraph']
        for text_run in paragraph.get('elements', []):
            if 'textRun' in text_run:
                print(text_run['textRun']['content'])
```

---

## Text Formatting Capabilities

### Text Style Properties

The `TextStyle` object supports:

| Property | Type | Description | Example Values |
|----------|------|-------------|----------------|
| `bold` | boolean | Bold text | `true`, `false` |
| `italic` | boolean | Italic text | `true`, `false` |
| `underline` | boolean | Underlined text | `true`, `false` |
| `strikethrough` | boolean | Strikethrough text | `true`, `false` |
| `fontSize` | object | Font size | `{"magnitude": 12, "unit": "PT"}` |
| `foregroundColor` | object | Text color | `{"color": {"rgbColor": {"red": 1.0}}}` |
| `backgroundColor` | object | Highlight color | Same as foregroundColor |
| `weightedFontFamily` | object | Font family | `{"fontFamily": "Arial", "weight": 400}` |
| `baselineOffset` | enum | Superscript/subscript | `SUPERSCRIPT`, `SUBSCRIPT`, `NONE` |
| `link` | object | Hyperlink | `{"url": "https://example.com"}` |

### Formatting Example

```python
requests = [
    {
        'insertText': {
            'location': {'index': 1},
            'text': 'This is bold and this is italic.'
        }
    },
    {
        'updateTextStyle': {
            'range': {'startIndex': 1, 'endIndex': 12},
            'textStyle': {'bold': True},
            'fields': 'bold'
        }
    },
    {
        'updateTextStyle': {
            'range': {'startIndex': 21, 'endIndex': 32},
            'textStyle': {'italic': True},
            'fields': 'italic'
        }
    }
]

result = docs_service.documents().batchUpdate(
    documentId=document_id,
    body={'requests': requests}
).execute()
```

**Important**: The `fields` parameter specifies which style properties to update using FieldMask syntax (e.g., `"bold"`, `"bold,italic"`, `"fontSize"`).

---

## Working with Tables

### Creating Tables

```python
requests = [{
    'insertTable': {
        'rows': 3,
        'columns': 4,
        'location': {'index': 1}
    }
}]

result = docs_service.documents().batchUpdate(
    documentId=document_id,
    body={'requests': requests}
).execute()
```

### Populating Table Cells

Tables are structured with nested indexes. To find a cell's index, you must read the document structure:

```python
# Read document to get table structure
document = docs_service.documents().get(documentId=document_id).execute()

# Find table in content
for element in document.get('body').get('content', []):
    if 'table' in element:
        table = element['table']
        # Access first row, first cell
        first_cell = table['tableRows'][0]['tableCells'][0]
        cell_content = first_cell['content']
        # Get start index of cell content
        cell_index = cell_content[0]['startIndex']

        # Insert text at cell location
        requests = [{
            'insertText': {
                'location': {'index': cell_index},
                'text': 'Cell content'
            }
        }]
        docs_service.documents().batchUpdate(
            documentId=document_id,
            body={'requests': requests}
        ).execute()
```

### Modifying Table Structure

```python
# Add row
requests = [{
    'insertTableRow': {
        'tableCellLocation': {
            'tableStartLocation': {'index': table_start_index},
            'rowIndex': 1,
            'columnIndex': 0
        },
        'insertBelow': True
    }
}]

# Add column
requests = [{
    'insertTableColumn': {
        'tableCellLocation': {
            'tableStartLocation': {'index': table_start_index},
            'rowIndex': 0,
            'columnIndex': 1
        },
        'insertRight': True
    }
}]

# Update cell style
requests = [{
    'updateTableCellStyle': {
        'tableCellLocation': {
            'tableStartLocation': {'index': table_start_index},
            'rowIndex': 0,
            'columnIndex': 0
        },
        'tableCellStyle': {
            'backgroundColor': {
                'color': {
                    'rgbColor': {
                        'red': 0.9,
                        'green': 0.9,
                        'blue': 0.9
                    }
                }
            }
        },
        'fields': 'backgroundColor'
    }
}]
```

---

## Working with Lists

### Creating Bulleted Lists

```python
# First, insert text with newlines for each item
requests = [
    {
        'insertText': {
            'location': {'index': 1},
            'text': 'First item\nSecond item\nThird item\n'
        }
    },
    {
        'createParagraphBullets': {
            'range': {
                'startIndex': 1,
                'endIndex': 40  # Covers all items
            },
            'bulletPreset': 'BULLET_DISC_CIRCLE_SQUARE'
        }
    }
]

result = docs_service.documents().batchUpdate(
    documentId=document_id,
    body={'requests': requests}
).execute()
```

### Available Bullet Presets

- `BULLET_DISC_CIRCLE_SQUARE`: • ○ ■
- `BULLET_DIAMONDX_ARROW3D_SQUARE`: ♦ ➔ ■
- `BULLET_CHECKBOX`: ☐ unchecked boxes
- `BULLET_ARROW_DIAMOND_DISC`: → ◆ •
- `BULLET_STAR_CIRCLE_SQUARE`: ★ ● ■
- `BULLET_ARROW3D_CIRCLE_SQUARE`: ➔ ● ■
- `BULLET_LEFTTRIANGLE_DIAMOND_DISC`: ◄ ◆ •
- `BULLET_DIAMONDX_HOLLOWDIAMOND_SQUARE`: ♦ ◇ ■
- `BULLET_DIAMOND_CIRCLE_SQUARE`: ♦ ● ■
- `NUMBERED_DECIMAL_ALPHA_ROMAN`: 1. a. i.
- `NUMBERED_DECIMAL_ALPHA_ROMAN_PARENS`: 1) a) i)
- `NUMBERED_DECIMAL_NESTED`: 1. 1.1. 1.1.1.
- `NUMBERED_UPPERALPHA_ALPHA_ROMAN`: A. a. i.
- `NUMBERED_UPPERROMAN_UPPERALPHA_DECIMAL`: I. A. 1.

### Nested Lists

Nesting is controlled by tab characters before text:

```python
requests = [{
    'insertText': {
        'location': {'index': 1},
        'text': 'Level 1\n\tLevel 2\n\t\tLevel 3\n'
    }
}, {
    'createParagraphBullets': {
        'range': {'startIndex': 1, 'endIndex': 30},
        'bulletPreset': 'BULLET_DISC_CIRCLE_SQUARE'
    }
}]
```

Each tab character increases nesting level.

---

## Google Drive API for Permissions

### Making Documents Publicly Shareable

After creating a document, use Drive API to set permissions:

**Endpoint**: `POST https://www.googleapis.com/drive/v3/files/{fileId}/permissions`

**Python Example**:
```python
from googleapiclient.discovery import build

SCOPES = [
    'https://www.googleapis.com/auth/documents',
    'https://www.googleapis.com/auth/drive'
]

credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)

drive_service = build('drive', 'v3', credentials=credentials)

# Create "anyone with link can view" permission
permission = {
    'type': 'anyone',
    'role': 'reader'
}

drive_service.permissions().create(
    fileId=document_id,
    body=permission
).execute()

# Get shareable link
file = drive_service.files().get(
    fileId=document_id,
    fields='webViewLink'
).execute()

print(f"Shareable link: {file.get('webViewLink')}")
```

### Permission Types

| Type | Description | Use Case |
|------|-------------|----------|
| `user` | Specific Google account | Share with individual user |
| `group` | Google Group | Share with team/organization |
| `domain` | All users in G Suite domain | Internal company sharing |
| `anyone` | Public access | "Anyone with link" sharing |

### Permission Roles

| Role | Capabilities |
|------|--------------|
| `owner` | Full control, can delete (only for user/group types) |
| `organizer` | Manage shared drive (shared drives only) |
| `fileOrganizer` | Manage files in shared drive folders |
| `writer` | Edit, comment, share |
| `commenter` | Comment only (cannot edit) |
| `reader` | View only |

### Important: September 2025 Permission Update

As of September 22, 2025, Google Drive enforces permission inheritance:
- **You cannot set document permissions more restrictive than parent folder**
- Items inherit folder permissions automatically
- You can still add or upgrade permissions
- Cannot remove or restrict below folder level

**Implication for Service Accounts**: If documents are created in a specific folder, that folder's permissions will cascade down. Create documents in root or dedicated folder with appropriate base permissions.

---

## Rate Limits and Quotas

### Current Quotas (as of October 2025)

| Quota Type | Limit | Scope |
|------------|-------|-------|
| Read requests | 3,000 per minute | Per project |
| Read requests (per user) | 300 per minute | Per user per project |
| Write requests | 600 per minute | Per project |
| Write requests (per user) | 60 per minute | Per user per project |

### Quota Exceeded Response

When you exceed a quota, the API returns:
```
HTTP 429 Too Many Requests
```

**Response Body**:
```json
{
  "error": {
    "code": 429,
    "message": "Quota exceeded for quota metric 'Write requests' and limit 'Write requests per minute per user' of service 'docs.googleapis.com'",
    "status": "RESOURCE_EXHAUSTED"
  }
}
```

### Exponential Backoff Strategy

**Recommended Algorithm**:
```
wait_time = min(((2^n) + random_milliseconds), maximum_backoff)
```

Where:
- `n` = retry attempt number (starts at 0)
- `random_milliseconds` = random(0, 1000)
- `maximum_backoff` = 32 or 64 seconds

**Python Implementation**:
```python
import time
import random
from googleapiclient.errors import HttpError

def create_document_with_retry(docs_service, body, max_retries=5):
    for n in range(max_retries):
        try:
            return docs_service.documents().create(body=body).execute()
        except HttpError as error:
            if error.resp.status == 429:
                if n == max_retries - 1:
                    raise  # Last attempt, re-raise error

                wait_time = min((2 ** n) + random.uniform(0, 1), 32)
                print(f"Rate limited. Waiting {wait_time:.2f} seconds...")
                time.sleep(wait_time)
            else:
                raise  # Non-rate-limit error, re-raise immediately
```

### Requesting Higher Quotas

1. Navigate to Google Cloud Console → IAM & Admin → Quotas
2. Filter by "Google Docs API"
3. Select quota to increase
4. Click "Edit Quotas"
5. Submit request with justification

**Note**: Approval is not guaranteed and may take several days.

---

## Error Handling

### Common Error Codes

| HTTP Code | Status | Meaning | Action |
|-----------|--------|---------|--------|
| 400 | INVALID_ARGUMENT | Malformed request | Fix request format |
| 401 | UNAUTHENTICATED | Missing/invalid credentials | Check authentication |
| 403 | PERMISSION_DENIED | Insufficient permissions | Verify scopes/IAM roles |
| 404 | NOT_FOUND | Document doesn't exist | Check document ID |
| 429 | RESOURCE_EXHAUSTED | Quota exceeded | Implement backoff retry |
| 500 | INTERNAL | Google server error | Retry with backoff |
| 503 | UNAVAILABLE | Service temporarily unavailable | Retry with backoff |

### Python Error Handling Example

```python
from googleapiclient.errors import HttpError
import logging

logger = logging.getLogger(__name__)

try:
    result = docs_service.documents().batchUpdate(
        documentId=document_id,
        body={'requests': requests}
    ).execute()
except HttpError as error:
    if error.resp.status == 400:
        logger.error(f"Invalid request: {error.content}")
        raise ValueError("Malformed API request") from error
    elif error.resp.status == 403:
        logger.error(f"Permission denied: {error.content}")
        raise PermissionError("Insufficient API permissions") from error
    elif error.resp.status == 404:
        logger.error(f"Document not found: {document_id}")
        raise FileNotFoundError(f"Document {document_id} does not exist") from error
    elif error.resp.status == 429:
        logger.warning(f"Rate limit exceeded, implement retry logic")
        raise  # Let retry logic handle
    else:
        logger.error(f"Google API error: {error.content}", exc_info=True)
        raise
```

---

## API Scopes

### Required Scopes for Different Operations

| Scope | Permission Level | Use Case |
|-------|------------------|----------|
| `https://www.googleapis.com/auth/documents` | Read/write documents | Full document operations |
| `https://www.googleapis.com/auth/documents.readonly` | Read-only documents | Reading without modification |
| `https://www.googleapis.com/auth/drive` | Full Drive access | Creating docs + managing permissions |
| `https://www.googleapis.com/auth/drive.file` | Access to files created by app | Limited Drive access |
| `https://www.googleapis.com/auth/drive.readonly` | Read-only Drive | Viewing files and metadata |

**Recommendation for Markdown Converter**:
```python
SCOPES = [
    'https://www.googleapis.com/auth/documents',
    'https://www.googleapis.com/auth/drive'
]
```

This provides full document creation and permission management capabilities.

---

## Best Practices

### 1. Batch Operations

**DO**:
```python
# Single batchUpdate with multiple requests
requests = [
    {'insertText': {'location': {'index': 1}, 'text': 'Title\n'}},
    {'updateTextStyle': {'range': {'startIndex': 1, 'endIndex': 6},
                         'textStyle': {'bold': True}, 'fields': 'bold'}},
    {'insertText': {'location': {'index': 7}, 'text': 'Body text\n'}}
]
docs_service.documents().batchUpdate(documentId=doc_id, body={'requests': requests}).execute()
```

**DON'T**:
```python
# Multiple separate API calls
docs_service.documents().batchUpdate(documentId=doc_id,
    body={'requests': [{'insertText': {'location': {'index': 1}, 'text': 'Title\n'}}]}).execute()
docs_service.documents().batchUpdate(documentId=doc_id,
    body={'requests': [{'updateTextStyle': {...}}]}).execute()
docs_service.documents().batchUpdate(documentId=doc_id,
    body={'requests': [{'insertText': {...}}]}).execute()
```

**Reason**: Each API call counts against quotas and adds latency. Batching is more efficient and atomic.

### 2. Index Management

Always work in reverse order when deleting or inserting at multiple locations:

```python
# Inserting at indices 1, 10, 20
# Work backwards to avoid index shifts
requests = [
    {'insertText': {'location': {'index': 20}, 'text': 'Third'}},
    {'insertText': {'location': {'index': 10}, 'text': 'Second'}},
    {'insertText': {'location': {'index': 1}, 'text': 'First'}}
]
```

### 3. Error Handling

Always implement retry logic for transient errors (429, 500, 503):

```python
from google.api_core import retry

@retry.Retry(predicate=retry.if_exception_type(HttpError))
def create_document(docs_service, title):
    return docs_service.documents().create(body={'title': title}).execute()
```

### 4. Field Masks

Always specify the `fields` parameter when updating styles to avoid overwriting unintended properties:

```python
# Good: Only updates bold
{'updateTextStyle': {'textStyle': {'bold': True}, 'fields': 'bold'}}

# Bad: May clear other formatting
{'updateTextStyle': {'textStyle': {'bold': True}}}
```

### 5. Document Access Patterns

For public conversions (markdown converter use case):
1. Create document with service account
2. Immediately set "anyone with link" permission
3. Return webViewLink to user
4. Optionally clean up old documents periodically

---

## Recent API Updates (2025)

### Tab Support (Generally Available)
As of 2025, you can create and organize documents with tabs using the Google Docs API. This allows multi-section documents with improved navigation.

**Creating Tabs**:
```python
requests = [{
    'createTab': {
        'documentTab': {
            'title': 'Introduction'
        }
    }
}]
```

### API Endpoints Updated
Last documentation refresh: **October 13, 2025 UTC**

All code examples and endpoint specifications in this document reflect the latest API version.

---

## Additional Resources

### Official Documentation
- **API Reference**: https://developers.google.com/docs/api/reference/rest/v1
- **How-to Guides**: https://developers.google.com/docs/api/how-tos/overview
- **Release Notes**: https://developers.google.com/docs/release-notes
- **Drive API Reference**: https://developers.google.com/drive/api/v3/reference
- **Drive Sharing Guide**: https://developers.google.com/drive/api/v3/manage-sharing

### Python Client Libraries
- **google-api-python-client**: https://github.com/googleapis/google-api-python-client
- **google-auth**: https://github.com/googleapis/google-auth-library-python
- **API Core (Retry Logic)**: https://googleapis.dev/python/google-api-core/latest/retry.html

### Community Resources
- **Stack Overflow**: Tag `google-docs-api` for questions
- **Issue Tracker**: https://issuetracker.google.com/issues?q=componentid:191640
- **Google Workspace Updates Blog**: https://workspaceupdates.googleblog.com/

---

## Summary Checklist

For implementing Google Docs conversion in the markdown converter:

- [ ] Understand document structure (Body, DocumentStyle, structural elements)
- [ ] Know how to create documents and get document IDs
- [ ] Master batchUpdate for efficient multi-step operations
- [ ] Implement text insertion and formatting
- [ ] Handle tables and lists creation
- [ ] Set up Drive API permissions for public sharing
- [ ] Implement rate limiting and exponential backoff
- [ ] Handle common errors (400, 403, 404, 429)
- [ ] Use appropriate scopes (documents + drive)
- [ ] Follow best practices (batching, field masks, index management)

**Next Steps**: Review `service-account-setup.md` for authentication configuration.
