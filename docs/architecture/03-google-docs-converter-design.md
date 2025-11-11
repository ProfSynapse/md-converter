# Google Docs Converter Design

**Document Version**: 1.0
**Date**: 2025-11-01
**Phase**: PACT Architecture
**Status**: Ready for Implementation

---

## Executive Summary

This document specifies the detailed design for the GoogleDocsConverter class, which converts markdown content to Google Docs format using the Google Docs API v1. The design leverages the markgdoc library for rapid implementation while providing extensibility for custom formatting requirements.

**Key Design Decisions**:
1. Use `markgdoc` library for core markdown-to-Docs conversion
2. Extend with custom handlers for front matter and advanced formatting
3. Create documents in user's Google Drive (via OAuth credentials)
4. Apply batch updates for optimal API performance
5. Return shareable links for immediate access

---

## Class Architecture

### GoogleDocsConverter Class Diagram

```
┌──────────────────────────────────────────────────────────┐
│              GoogleDocsConverter                          │
├──────────────────────────────────────────────────────────┤
│  - docs_service: googleapiclient.discovery.Resource      │
│  - drive_service: googleapiclient.discovery.Resource     │
│  - logger: logging.Logger                                │
├──────────────────────────────────────────────────────────┤
│  + __init__(docs_service, drive_service)                 │
│  + convert(markdown_content, title) → dict               │
│  - _parse_markdown(content) → (metadata, body)           │
│  - _create_document(title) → str                         │
│  - _apply_content(doc_id, markdown, metadata) → None     │
│  - _get_share_link(doc_id) → str                         │
│  - _build_requests(markdown, metadata) → list            │
│  - _format_front_matter(metadata) → list                 │
└──────────────────────────────────────────────────────────┘
           │
           │ uses
           ▼
┌──────────────────────────────────────────────────────────┐
│              markgdoc Library                             │
├──────────────────────────────────────────────────────────┤
│  + convert_to_google_docs(...)                           │
│  + markdown_to_requests(...)                             │
└──────────────────────────────────────────────────────────┘
```

### Class Responsibilities

**GoogleDocsConverter**:
- Orchestrate markdown-to-Docs conversion process
- Parse YAML front matter
- Create empty document in user's Drive
- Build and apply Docs API batchUpdate requests
- Retrieve shareable link
- Handle Google API errors gracefully

**markgdoc Library**:
- Parse markdown syntax (headings, lists, tables, etc.)
- Generate Docs API request structures
- Handle common markdown elements
- Provide baseline conversion functionality

---

## Implementation Specification

### Module Structure

**File**: `app/converters/google_docs_converter.py`

```python
"""
Google Docs Converter

Converts markdown content with YAML front matter to Google Docs format
using the Google Docs API v1.

Dependencies:
    - google-api-python-client: Google API client
    - markgdoc: Markdown to Google Docs conversion
    - python-frontmatter: YAML front matter parsing

Used by: app/api/routes.py for Google Docs conversion requests
"""
import frontmatter
import logging
from typing import Dict, Tuple, Optional
from googleapiclient.discovery import Resource
from googleapiclient.errors import HttpError

# Optional: markgdoc for simplified conversion
try:
    from markgdoc import convert_to_google_docs, markdown_to_requests
    MARKGDOC_AVAILABLE = True
except ImportError:
    MARKGDOC_AVAILABLE = False
    logging.warning("markgdoc not installed - using custom conversion logic")


logger = logging.getLogger(__name__)


class GoogleDocsConversionError(Exception):
    """Raised when Google Docs conversion fails."""
    pass


class GoogleDocsConverter:
    """
    Converts markdown files with YAML front matter to Google Docs.

    This class handles:
    - Parsing YAML front matter
    - Converting markdown to Google Docs API requests
    - Creating documents in user's Google Drive
    - Applying formatting via batchUpdate API
    - Generating shareable links

    Example:
        >>> converter = GoogleDocsConverter(docs_service, drive_service)
        >>> result = converter.convert(markdown_content, "My Document")
        >>> print(result['webViewLink'])
    """

    def __init__(self, docs_service: Resource, drive_service: Resource):
        """
        Initialize converter with Google API service clients.

        Args:
            docs_service: Google Docs API v1 service
            drive_service: Google Drive API v3 service
        """
        self.docs_service = docs_service
        self.drive_service = drive_service
        self.logger = logger

    def convert(
        self,
        markdown_content: str,
        title: str,
        make_public: bool = False
    ) -> Dict[str, str]:
        """
        Convert markdown to Google Docs.

        Args:
            markdown_content: Markdown text with optional YAML front matter
            title: Document title (overridden by front matter title if present)
            make_public: Whether to make document publicly viewable (default False)

        Returns:
            dict with:
                - documentId: Google Docs document ID
                - webViewLink: URL to view document
                - title: Final document title

        Raises:
            GoogleDocsConversionError: If conversion fails

        Example:
            >>> result = converter.convert("# Hello\nWorld", "Test Doc")
            >>> doc_url = result['webViewLink']
        """
        self.logger.info(f"Starting Google Docs conversion: {title}")
        start_time = time.time()

        try:
            # Step 1: Parse front matter and content
            metadata, markdown_body = self._parse_markdown(markdown_content)

            # Override title from front matter if present
            if 'title' in metadata:
                title = metadata['title']
                self.logger.debug(f"Using title from front matter: {title}")

            # Step 2: Create empty document
            doc_id = self._create_document(title)
            self.logger.info(f"Document created: {doc_id}")

            # Step 3: Apply content to document
            self._apply_content(doc_id, markdown_body, metadata)
            self.logger.info(f"Content applied to document: {doc_id}")

            # Step 4: Set permissions if requested
            if make_public:
                self._make_public(doc_id)
                self.logger.info(f"Document made publicly viewable: {doc_id}")

            # Step 5: Get shareable link
            web_link = self._get_share_link(doc_id)
            self.logger.info(f"Shareable link generated: {web_link}")

            elapsed = time.time() - start_time
            self.logger.info(f"Conversion completed in {elapsed:.2f}s")

            return {
                'documentId': doc_id,
                'webViewLink': web_link,
                'title': title
            }

        except HttpError as e:
            error_msg = f"Google API error during conversion: {e.content}"
            self.logger.error(error_msg, exc_info=True)

            # Handle specific error codes
            if e.resp.status == 429:
                raise GoogleDocsConversionError(
                    "Rate limit exceeded. Please try again in a minute."
                ) from e
            elif e.resp.status == 403:
                raise GoogleDocsConversionError(
                    "Permission denied. Please re-authenticate."
                ) from e
            else:
                raise GoogleDocsConversionError(
                    f"Failed to convert to Google Docs: {e.resp.status}"
                ) from e

        except Exception as e:
            error_msg = f"Unexpected error during conversion: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            raise GoogleDocsConversionError(error_msg) from e

    def _parse_markdown(self, content: str) -> Tuple[Dict, str]:
        """
        Parse markdown with YAML front matter.

        Args:
            content: Raw markdown string with optional YAML front matter

        Returns:
            Tuple of (metadata dict, content string)

        Example:
            >>> metadata, body = converter._parse_markdown(md_string)
            >>> print(metadata['title'])
            'My Document'
        """
        try:
            post = frontmatter.loads(content)
            self.logger.debug(f"Parsed front matter: {post.metadata.keys()}")
            return post.metadata, post.content
        except Exception as e:
            self.logger.warning(f"Failed to parse front matter: {e}")
            # If parsing fails, treat entire content as markdown
            return {}, content

    def _create_document(self, title: str) -> str:
        """
        Create empty Google Docs document.

        Args:
            title: Document title

        Returns:
            str: Document ID

        Raises:
            HttpError: If document creation fails
        """
        self.logger.debug(f"Creating document with title: {title}")

        document = self.docs_service.documents().create(
            body={'title': title}
        ).execute()

        doc_id = document.get('documentId')
        self.logger.debug(f"Document created with ID: {doc_id}")

        return doc_id

    def _apply_content(
        self,
        doc_id: str,
        markdown_body: str,
        metadata: Dict
    ) -> None:
        """
        Apply markdown content to document via batchUpdate.

        Args:
            doc_id: Document ID
            markdown_body: Markdown content (without front matter)
            metadata: Front matter metadata dict

        Raises:
            HttpError: If batchUpdate fails
        """
        self.logger.debug(f"Building API requests for document: {doc_id}")

        # Build list of batchUpdate requests
        requests = self._build_requests(markdown_body, metadata)

        if not requests:
            self.logger.warning("No API requests generated - empty document")
            return

        self.logger.debug(f"Applying {len(requests)} requests to document")

        # Apply all requests in single batch
        self.docs_service.documents().batchUpdate(
            documentId=doc_id,
            body={'requests': requests}
        ).execute()

        self.logger.debug(f"Successfully applied {len(requests)} requests")

    def _build_requests(self, markdown_body: str, metadata: Dict) -> list:
        """
        Build Docs API batchUpdate requests from markdown.

        Args:
            markdown_body: Markdown content string
            metadata: Front matter metadata

        Returns:
            list: Docs API request dicts

        This method uses markgdoc if available, otherwise falls back
        to custom implementation.
        """
        requests = []

        # Add front matter as document header
        if metadata:
            front_matter_requests = self._format_front_matter(metadata)
            requests.extend(front_matter_requests)

        # Convert markdown to API requests
        if MARKGDOC_AVAILABLE:
            # Use markgdoc library
            self.logger.debug("Using markgdoc for conversion")
            try:
                md_requests = markdown_to_requests(markdown_body)
                requests.extend(md_requests)
            except Exception as e:
                self.logger.warning(f"markgdoc conversion failed: {e}")
                # Fall back to custom implementation
                custom_requests = self._custom_markdown_conversion(markdown_body)
                requests.extend(custom_requests)
        else:
            # Use custom implementation
            self.logger.debug("Using custom markdown conversion")
            custom_requests = self._custom_markdown_conversion(markdown_body)
            requests.extend(custom_requests)

        return requests

    def _format_front_matter(self, metadata: Dict) -> list:
        """
        Format front matter as document header.

        Args:
            metadata: Front matter key-value pairs

        Returns:
            list: Docs API requests for front matter section

        Creates a styled document information section at top of document.
        """
        requests = []
        current_index = 1  # Documents start at index 1

        # Title (styled as TITLE)
        if 'title' in metadata:
            title_text = metadata['title'] + '\n'
            requests.append({
                'insertText': {
                    'location': {'index': current_index},
                    'text': title_text
                }
            })
            requests.append({
                'updateParagraphStyle': {
                    'range': {
                        'startIndex': current_index,
                        'endIndex': current_index + len(title_text) - 1
                    },
                    'paragraphStyle': {
                        'namedStyleType': 'TITLE'
                    },
                    'fields': 'namedStyleType'
                }
            })
            current_index += len(title_text)

        # Other metadata as subtitle
        metadata_lines = []
        for key, value in metadata.items():
            if key != 'title':
                # Format key nicely
                key_display = key.replace('_', ' ').title()

                # Handle different value types
                if isinstance(value, list):
                    value_str = ', '.join(str(v) for v in value)
                elif hasattr(value, 'strftime'):  # Date object
                    value_str = value.strftime('%Y-%m-%d')
                else:
                    value_str = str(value)

                metadata_lines.append(f"{key_display}: {value_str}")

        if metadata_lines:
            subtitle_text = ' | '.join(metadata_lines) + '\n'
            requests.append({
                'insertText': {
                    'location': {'index': current_index},
                    'text': subtitle_text
                }
            })
            requests.append({
                'updateParagraphStyle': {
                    'range': {
                        'startIndex': current_index,
                        'endIndex': current_index + len(subtitle_text) - 1
                    },
                    'paragraphStyle': {
                        'namedStyleType': 'SUBTITLE'
                    },
                    'fields': 'namedStyleType'
                }
            })
            current_index += len(subtitle_text)

        # Add spacing after front matter
        requests.append({
            'insertText': {
                'location': {'index': current_index},
                'text': '\n'
            }
        })

        return requests

    def _custom_markdown_conversion(self, markdown: str) -> list:
        """
        Custom markdown to Docs API requests conversion.

        This is a fallback implementation when markgdoc is not available.

        Args:
            markdown: Markdown content string

        Returns:
            list: Docs API request dicts

        Note: This is a simplified implementation. For production use,
        consider installing markgdoc or implementing full markdown parser.
        """
        # TODO: Implement custom markdown parser
        # For MVP, this returns basic text insertion
        self.logger.warning("Using basic text insertion - advanced formatting not supported")

        return [{
            'insertText': {
                'location': {'index': 1},
                'text': markdown
            }
        }]

    def _get_share_link(self, doc_id: str) -> str:
        """
        Get shareable link for document.

        Args:
            doc_id: Document ID

        Returns:
            str: Web view link URL

        Raises:
            HttpError: If Drive API request fails
        """
        self.logger.debug(f"Fetching share link for document: {doc_id}")

        file = self.drive_service.files().get(
            fileId=doc_id,
            fields='webViewLink'
        ).execute()

        web_link = file.get('webViewLink')
        self.logger.debug(f"Share link: {web_link}")

        return web_link

    def _make_public(self, doc_id: str) -> None:
        """
        Make document publicly viewable (anyone with link).

        Args:
            doc_id: Document ID

        Raises:
            HttpError: If permission creation fails

        Note: Use with caution. User owns document and can change
        permissions later via Google Drive UI.
        """
        self.logger.debug(f"Making document public: {doc_id}")

        self.drive_service.permissions().create(
            fileId=doc_id,
            body={
                'type': 'anyone',
                'role': 'reader'
            }
        ).execute()

        self.logger.debug(f"Document {doc_id} is now publicly viewable")
```

---

## Markdown Element Mapping

### Supported Elements (via markgdoc)

| Markdown | Docs API Request | Status |
|----------|------------------|--------|
| `# Heading` | `updateParagraphStyle` (HEADING_1) | Supported |
| `## Heading` | `updateParagraphStyle` (HEADING_2) | Supported |
| `**bold**` | `updateTextStyle` (bold: true) | Supported |
| `*italic*` | `updateTextStyle` (italic: true) | Supported |
| `~~strike~~` | `updateTextStyle` (strikethrough: true) | Supported |
| `- list` | `createParagraphBullets` | Supported |
| `1. list` | `createParagraphBullets` (numbered) | Supported |
| `[link](url)` | `updateTextStyle` (link) | Supported |
| `---` | `insertPageBreak` or styled separator | Supported |
| Tables | `insertTable` + cell text | Basic support |
| `` `code` `` | `updateTextStyle` (monospace) | Partial |
| Code blocks | `insertText` (no highlighting) | Partial |
| Images | `insertInlineImage` (URL only) | Limited |

### Advanced Formatting (Future Enhancement)

**Code Blocks with Language**:
```python
def _format_code_block(code: str, language: str) -> list:
    """
    Format code block with background color and monospace font.

    Args:
        code: Source code text
        language: Programming language (for documentation, no syntax highlighting)

    Returns:
        list: API requests for formatted code block
    """
    return [
        {
            'insertText': {
                'location': {'index': index},
                'text': code + '\n'
            }
        },
        {
            'updateTextStyle': {
                'range': {'startIndex': index, 'endIndex': index + len(code)},
                'textStyle': {
                    'weightedFontFamily': {
                        'fontFamily': 'Courier New',
                        'weight': 400
                    },
                    'fontSize': {'magnitude': 10, 'unit': 'PT'},
                    'backgroundColor': {
                        'color': {
                            'rgbColor': {
                                'red': 0.95,
                                'green': 0.95,
                                'blue': 0.95
                            }
                        }
                    }
                },
                'fields': 'weightedFontFamily,fontSize,backgroundColor'
            }
        }
    ]
```

**Tables with Styling**:
```python
def _format_table(table_data: list) -> list:
    """
    Format table with header row styling.

    Args:
        table_data: List of lists [[header1, header2], [row1col1, row1col2]]

    Returns:
        list: API requests for table creation and formatting

    Note: Requires two-phase approach:
    1. Create table structure
    2. Read document to get cell indices
    3. Populate and style cells
    """
    rows = len(table_data)
    cols = len(table_data[0]) if table_data else 0

    return [{
        'insertTable': {
            'rows': rows,
            'columns': cols,
            'location': {'index': index}
        }
    }]
    # Additional requests for cell population required
```

---

## API Service Builder

### Service Factory

**Module**: `app/utils/google_services.py`

```python
"""
Google API Service Builder

Creates authenticated Google API service clients for Docs and Drive APIs.

Dependencies:
    - google-api-python-client
    - google-auth

Used by: app/api/routes.py for conversion requests
"""
from googleapiclient.discovery import build, Resource
from google.oauth2.credentials import Credentials
from functools import lru_cache
import logging
import hashlib

logger = logging.getLogger(__name__)


def build_google_services(credentials: Credentials) -> tuple[Resource, Resource]:
    """
    Build Google Docs and Drive API services.

    Args:
        credentials: OAuth2 credentials from Flask-Dance

    Returns:
        tuple: (docs_service, drive_service)

    Example:
        >>> creds = get_google_credentials()
        >>> docs, drive = build_google_services(creds)
    """
    logger.debug("Building Google API services")

    docs_service = build(
        'docs',
        'v1',
        credentials=credentials,
        cache_discovery=False  # Reduce memory usage
    )

    drive_service = build(
        'drive',
        'v3',
        credentials=credentials,
        cache_discovery=False
    )

    logger.debug("Google API services built successfully")

    return docs_service, drive_service


@lru_cache(maxsize=10)
def get_cached_services(token_hash: str, token: str) -> tuple[Resource, Resource]:
    """
    Get Google API services with caching.

    Args:
        token_hash: Hash of token (cache key)
        token: Actual OAuth access token

    Returns:
        tuple: (docs_service, drive_service)

    Note: LRU cache improves performance for repeated requests
    from same user within token lifetime.
    """
    credentials = Credentials(token=token)
    return build_google_services(credentials)


def get_services_for_user(access_token: str) -> tuple[Resource, Resource]:
    """
    Get Google API services for user with caching.

    Args:
        access_token: OAuth access token from Flask-Dance

    Returns:
        tuple: (docs_service, drive_service)

    Example:
        >>> from flask_dance.contrib.google import google
        >>> token = google.token['access_token']
        >>> docs, drive = get_services_for_user(token)
    """
    # Create hash for cache key (don't cache actual token)
    token_hash = hashlib.sha256(access_token.encode()).hexdigest()

    return get_cached_services(token_hash, access_token)
```

---

## Error Handling

### Error Scenarios

#### 1. API Rate Limit Exceeded

**Error**:
```json
{
  "error": {
    "code": 429,
    "message": "Rate Limit Exceeded"
  }
}
```

**Handling**:
```python
try:
    result = converter.convert(markdown, title)
except GoogleDocsConversionError as e:
    if "rate limit" in str(e).lower():
        return jsonify({
            'error': 'Google Docs service temporarily busy',
            'code': 'RATE_LIMIT_EXCEEDED',
            'retry_after': 60  # seconds
        }), 429
```

#### 2. Invalid Markdown Syntax

**Scenario**: Malformed markdown that markgdoc cannot parse

**Handling**:
```python
try:
    requests = markdown_to_requests(markdown_body)
except Exception as e:
    logger.warning(f"markgdoc parsing failed: {e}")
    # Fall back to plain text insertion
    requests = [{
        'insertText': {
            'location': {'index': 1},
            'text': markdown_body
        }
    }]
```

#### 3. Authentication Failure

**Scenario**: OAuth token invalid or revoked

**Handling**:
```python
try:
    docs, drive = build_google_services(credentials)
    converter = GoogleDocsConverter(docs, drive)
    result = converter.convert(markdown, title)
except google.auth.exceptions.RefreshError:
    logger.error("OAuth token refresh failed")
    session.clear()
    return jsonify({
        'error': 'Authentication expired. Please sign in again.',
        'code': 'AUTH_EXPIRED',
        'auth_url': url_for('google.login', _external=True)
    }), 401
```

---

## Performance Optimization

### Batch Request Optimization

**Combine Sequential Insertions**:
```python
# Instead of multiple insertText requests
requests = [
    {'insertText': {'location': {'index': 1}, 'text': 'Line 1\n'}},
    {'insertText': {'location': {'index': 8}, 'text': 'Line 2\n'}},
    {'insertText': {'location': {'index': 15}, 'text': 'Line 3\n'}}
]

# Combine into single request
requests = [
    {'insertText': {
        'location': {'index': 1},
        'text': 'Line 1\nLine 2\nLine 3\n'
    }}
]
```

**Benefit**: Reduces API calls from 3 to 1, improving latency

### Service Client Caching

```python
# Cache service clients per user token
@lru_cache(maxsize=10)
def get_cached_services(token_hash: str, token: str):
    # Service creation is expensive (~200-300ms)
    # Caching reduces to ~0ms for subsequent requests
    return build_google_services(Credentials(token=token))
```

**Benefit**: 200-300ms saved per request

### Expected Performance

| Operation | Time (Uncached) | Time (Cached) |
|-----------|----------------|---------------|
| Build API services | 200-300ms | ~0ms |
| Create document | 500-800ms | 500-800ms |
| Apply content (small) | 1-2s | 1-2s |
| Apply content (large) | 3-5s | 3-5s |
| Get share link | 200-400ms | 200-400ms |
| **Total (small doc)** | **3-4s** | **2.5-3.5s** |

---

## Testing Strategy

### Unit Tests

**Test Markdown Parsing**:
```python
def test_parse_markdown_with_frontmatter():
    """Test front matter extraction."""
    markdown = """---
title: Test Document
author: Test Author
---
# Content
"""
    converter = GoogleDocsConverter(Mock(), Mock())
    metadata, body = converter._parse_markdown(markdown)

    assert metadata['title'] == 'Test Document'
    assert metadata['author'] == 'Test Author'
    assert '# Content' in body
```

**Test Front Matter Formatting**:
```python
def test_format_front_matter():
    """Test front matter API request generation."""
    metadata = {
        'title': 'Test',
        'author': 'John Doe',
        'date': '2025-11-01'
    }

    converter = GoogleDocsConverter(Mock(), Mock())
    requests = converter._format_front_matter(metadata)

    # Should have insertText and updateParagraphStyle requests
    assert any('insertText' in r for r in requests)
    assert any('updateParagraphStyle' in r for r in requests)
```

### Integration Tests

**Test Full Conversion** (with mocked API):
```python
@mock.patch('app.utils.google_services.build')
def test_google_docs_conversion(mock_build):
    """Test complete conversion flow with mocked Google API."""
    # Mock Docs API
    mock_docs = Mock()
    mock_docs.documents().create().execute.return_value = {
        'documentId': 'test-doc-id'
    }
    mock_docs.documents().batchUpdate().execute.return_value = {}

    # Mock Drive API
    mock_drive = Mock()
    mock_drive.files().get().execute.return_value = {
        'webViewLink': 'https://docs.google.com/document/d/test-doc-id'
    }

    mock_build.side_effect = [mock_docs, mock_drive]

    # Create converter
    converter = GoogleDocsConverter(mock_docs, mock_drive)

    # Test conversion
    markdown = "# Test\nContent"
    result = converter.convert(markdown, "Test Document")

    assert result['documentId'] == 'test-doc-id'
    assert 'webViewLink' in result
    mock_docs.documents().create.assert_called_once()
    mock_docs.documents().batchUpdate.assert_called_once()
```

---

## Deployment Checklist

### Dependencies

- [ ] Install `google-api-python-client>=2.149.0`
- [ ] Install `google-auth>=2.35.0`
- [ ] Install `markgdoc==1.0.1` (optional but recommended)
- [ ] Install `python-frontmatter==1.0.1` (already installed)

### Configuration

- [ ] OAuth credentials configured (see OAuth2 design doc)
- [ ] Google Docs API enabled in Google Cloud Console
- [ ] Google Drive API enabled in Google Cloud Console

### Testing

- [ ] Unit tests pass
- [ ] Integration tests with mocked API pass
- [ ] Manual test with real Google account
- [ ] Verify document formatting in Google Docs UI
- [ ] Test error handling (rate limit, auth failure)

---

**Google Docs Converter Design Status**: COMPLETE
**Ready for Implementation**: YES
**Next Document**: API Endpoint Design
