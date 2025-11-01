# Markdown to Google Docs Conversion Strategy

**Last Updated**: November 1, 2025
**Purpose**: Document conversion strategies and implementation patterns

---

## Executive Summary

Converting Markdown to Google Docs requires mapping each Markdown element to corresponding Google Docs API requests. Two primary approaches exist: (1) build custom parser and API request generator, or (2) leverage existing libraries like `markgdoc`. This document provides both approaches with code examples.

**Recommendation**: Start with `markgdoc` library for rapid implementation, fall back to custom implementation for unsupported elements.

---

## Markdown Element Mapping

### Core Syntax Mapping Table

| Markdown | Google Docs API Request | Complexity |
|----------|------------------------|------------|
| `# Heading` | `insertText` + `updateParagraphStyle` (HEADING_1) | Low |
| `**bold**` | `insertText` + `updateTextStyle` (bold: true) | Low |
| `*italic*` | `insertText` + `updateTextStyle` (italic: true) | Low |
| ``` `code` ``` | `insertText` + `updateTextStyle` (monospace font) | Low |
| `[link](url)` | `insertText` + `updateTextStyle` (link) | Medium |
| `- list` | `insertText` + `createParagraphBullets` | Medium |
| `1. list` | `insertText` + `createParagraphBullets` (numbered) | Medium |
| Tables | `insertTable` + `insertText` (per cell) | High |
| Code blocks | `insertText` + `updateTextStyle` + background | High |
| Images | `insertInlineImage` (from URL) | Medium |

---

## Approach 1: Using markgdoc Library

### Installation

```bash
pip install markgdoc==1.0.1
```

### Basic Usage

```python
from markgdoc import convert_to_google_docs
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Setup credentials
SCOPES = [
    'https://www.googleapis.com/auth/documents',
    'https://www.googleapis.com/auth/drive'
]
credentials = service_account.Credentials.from_service_account_file(
    'credentials.json', scopes=SCOPES
)
docs_service = build('docs', 'v1', credentials=credentials)

# Convert markdown
markdown_content = """
# My Document

This is **bold** and this is *italic*.

## Features

- First item
- Second item
"""

result = convert_to_google_docs(
    markdown_content=markdown_content,
    title="Converted Document",
    docs_service=docs_service,
    credentials_file='credentials.json',
    scopes=SCOPES
)

print(f"Document created: {result['url']}")
```

### markgdoc Supported Elements

According to documentation, markgdoc v1.0.1 supports:
- Headers (H1-H6)
- Bold, italic, strikethrough
- Unordered lists
- Ordered lists
- Paragraphs
- Horizontal lines
- Hyperlinks
- Tables (basic)

### markgdoc Limitations

- No code block formatting (no syntax highlighting)
- Limited table styling
- No image support from local files
- No nested list handling
- No blockquotes
- GPL v3 license (may be restrictive for some projects)

---

## Approach 2: Custom Implementation

### Step 1: Parse Markdown

Use Python `markdown` library with extensions:

```bash
pip install markdown
```

**Parser Implementation**:
```python
import markdown
from markdown.extensions import extra, codehilite, toc, nl2br, sane_lists
import frontmatter
import re

def parse_markdown(md_content: str) -> dict:
    """
    Parse markdown content into structured data.

    Returns:
        dict with 'front_matter', 'html', 'plain_text'
    """
    # Parse front matter
    post = frontmatter.loads(md_content)
    metadata = post.metadata
    content = post.content

    # Convert to HTML (for structure parsing)
    md = markdown.Markdown(extensions=[
        'extra',
        'codehilite',
        'toc',
        'nl2br',
        'sane_lists'
    ])
    html = md.convert(content)

    return {
        'front_matter': metadata,
        'html': html,
        'plain_text': content,
        'toc': md.toc_tokens if hasattr(md, 'toc_tokens') else None
    }
```

### Step 2: Convert to Docs API Requests

**Request Builder**:
```python
def markdown_to_docs_requests(md_content: str) -> list:
    """
    Convert markdown string to Google Docs API batchUpdate requests.

    Returns:
        List of API request dicts
    """
    requests = []
    current_index = 1  # Document starts at index 1

    # Parse markdown into lines
    lines = md_content.split('\n')

    for line in lines:
        # Headers
        if line.startswith('#'):
            level = len(line) - len(line.lstrip('#'))
            text = line.lstrip('#').strip()

            requests.extend([
                {
                    'insertText': {
                        'location': {'index': current_index},
                        'text': text + '\n'
                    }
                },
                {
                    'updateParagraphStyle': {
                        'range': {
                            'startIndex': current_index,
                            'endIndex': current_index + len(text)
                        },
                        'paragraphStyle': {
                            'namedStyleType': f'HEADING_{level}'
                        },
                        'fields': 'namedStyleType'
                    }
                }
            ])
            current_index += len(text) + 1

        # Bold/Italic text
        elif '**' in line or '*' in line:
            # Complex parsing needed for inline formatting
            requests.extend(parse_inline_formatting(line, current_index))
            current_index += len(line) + 1

        # Lists
        elif line.strip().startswith(('-', '*', '+')):
            # Unordered list
            text = line.strip()[1:].strip()
            requests.extend([
                {
                    'insertText': {
                        'location': {'index': current_index},
                        'text': text + '\n'
                    }
                },
                {
                    'createParagraphBullets': {
                        'range': {
                            'startIndex': current_index,
                            'endIndex': current_index + len(text) + 1
                        },
                        'bulletPreset': 'BULLET_DISC_CIRCLE_SQUARE'
                    }
                }
            ])
            current_index += len(text) + 1

        # Regular paragraphs
        elif line.strip():
            requests.append({
                'insertText': {
                    'location': {'index': current_index},
                    'text': line + '\n'
                }
            })
            current_index += len(line) + 1

    return requests
```

### Step 3: Handle Inline Formatting

**Inline Formatting Parser**:
```python
import re

def parse_inline_formatting(line: str, start_index: int) -> list:
    """
    Parse inline bold, italic, code formatting.

    Returns:
        List of insertText and updateTextStyle requests
    """
    requests = []

    # Insert full text first
    requests.append({
        'insertText': {
            'location': {'index': start_index},
            'text': strip_markdown_syntax(line) + '\n'
        }
    })

    # Find bold (**text**)
    for match in re.finditer(r'\*\*(.+?)\*\*', line):
        text = match.group(1)
        offset = calculate_offset(line, match.start())

        requests.append({
            'updateTextStyle': {
                'range': {
                    'startIndex': start_index + offset,
                    'endIndex': start_index + offset + len(text)
                },
                'textStyle': {'bold': True},
                'fields': 'bold'
            }
        })

    # Find italic (*text*)
    for match in re.finditer(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', line):
        text = match.group(1)
        offset = calculate_offset(line, match.start())

        requests.append({
            'updateTextStyle': {
                'range': {
                    'startIndex': start_index + offset,
                    'endIndex': start_index + offset + len(text)
                },
                'textStyle': {'italic': True},
                'fields': 'italic'
            }
        })

    # Find code (`text`)
    for match in re.finditer(r'`(.+?)`', line):
        text = match.group(1)
        offset = calculate_offset(line, match.start())

        requests.append({
            'updateTextStyle': {
                'range': {
                    'startIndex': start_index + offset,
                    'endIndex': start_index + offset + len(text)
                },
                'textStyle': {
                    'weightedFontFamily': {
                        'fontFamily': 'Courier New',
                        'weight': 400
                    },
                    'fontSize': {
                        'magnitude': 10,
                        'unit': 'PT'
                    }
                },
                'fields': 'weightedFontFamily,fontSize'
            }
        })

    return requests

def strip_markdown_syntax(text: str) -> str:
    """Remove markdown formatting characters."""
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)  # Bold
    text = re.sub(r'\*(.+?)\*', r'\1', text)  # Italic
    text = re.sub(r'`(.+?)`', r'\1', text)  # Code
    return text

def calculate_offset(line: str, match_start: int) -> int:
    """Calculate character offset after removing markdown syntax."""
    prefix = line[:match_start]
    return len(strip_markdown_syntax(prefix))
```

---

## Advanced Features

### Tables

```python
def create_table_requests(table_data: list, start_index: int) -> list:
    """
    Create Google Docs table from markdown table data.

    Args:
        table_data: List of lists [[header1, header2], [row1col1, row1col2]]
        start_index: Document index to insert table

    Returns:
        List of API requests
    """
    rows = len(table_data)
    cols = len(table_data[0]) if table_data else 0

    requests = [
        {
            'insertTable': {
                'rows': rows,
                'columns': cols,
                'location': {'index': start_index}
            }
        }
    ]

    # Note: After inserting table, you must read document to get cell indices
    # This requires a two-phase approach:
    # 1. Create table
    # 2. Read document structure
    # 3. Populate cells

    return requests

def populate_table_cells(doc_id: str, table_data: list, table_start_index: int,
                        docs_service) -> None:
    """
    Populate table cells after table creation.

    Requires reading document structure to find cell indices.
    """
    # Read document to get table structure
    document = docs_service.documents().get(documentId=doc_id).execute()

    # Find table at start index
    table = find_table_at_index(document, table_start_index)

    if not table:
        return

    requests = []

    # Iterate through table data and cells
    for row_idx, row_data in enumerate(table_data):
        table_row = table['tableRows'][row_idx]

        for col_idx, cell_text in enumerate(row_data):
            cell = table_row['tableCells'][col_idx]
            cell_start = cell['content'][0]['startIndex']

            requests.append({
                'insertText': {
                    'location': {'index': cell_start},
                    'text': cell_text
                }
            })

            # Bold header row
            if row_idx == 0:
                requests.append({
                    'updateTextStyle': {
                        'range': {
                            'startIndex': cell_start,
                            'endIndex': cell_start + len(cell_text)
                        },
                        'textStyle': {'bold': True},
                        'fields': 'bold'
                    }
                })

    # Apply all cell updates
    if requests:
        docs_service.documents().batchUpdate(
            documentId=doc_id,
            body={'requests': requests}
        ).execute()
```

### Code Blocks

```python
def create_code_block(code_text: str, start_index: int, language: str = '') -> list:
    """
    Create formatted code block in Google Docs.

    Args:
        code_text: Source code
        start_index: Document index
        language: Programming language (for reference, no syntax highlighting available)

    Returns:
        List of API requests
    """
    requests = [
        # Insert code text
        {
            'insertText': {
                'location': {'index': start_index},
                'text': code_text + '\n'
            }
        },
        # Apply monospace font
        {
            'updateTextStyle': {
                'range': {
                    'startIndex': start_index,
                    'endIndex': start_index + len(code_text)
                },
                'textStyle': {
                    'weightedFontFamily': {
                        'fontFamily': 'Courier New',
                        'weight': 400
                    },
                    'fontSize': {
                        'magnitude': 9,
                        'unit': 'PT'
                    }
                },
                'fields': 'weightedFontFamily,fontSize'
            }
        },
        # Add background color
        {
            'updateTextStyle': {
                'range': {
                    'startIndex': start_index,
                    'endIndex': start_index + len(code_text)
                },
                'textStyle': {
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
                'fields': 'backgroundColor'
            }
        }
    ]

    return requests
```

### Images

```python
def insert_image(image_url: str, start_index: int) -> dict:
    """
    Insert image from URL into document.

    Args:
        image_url: Public URL to image
        start_index: Document index

    Returns:
        API request dict

    Note: Image must be publicly accessible via URL
    """
    return {
        'insertInlineImage': {
            'uri': image_url,
            'location': {'index': start_index}
        }
    }
```

### YAML Front Matter Handling

```python
def format_front_matter(metadata: dict, start_index: int = 1) -> list:
    """
    Format YAML front matter as document metadata section.

    Args:
        metadata: Front matter key-value pairs
        start_index: Starting index (usually 1)

    Returns:
        List of API requests
    """
    requests = []
    current_index = start_index

    # Title
    if 'title' in metadata:
        title = metadata['title']
        requests.extend([
            {
                'insertText': {
                    'location': {'index': current_index},
                    'text': title + '\n'
                }
            },
            {
                'updateParagraphStyle': {
                    'range': {
                        'startIndex': current_index,
                        'endIndex': current_index + len(title)
                    },
                    'paragraphStyle': {
                        'namedStyleType': 'TITLE'
                    },
                    'fields': 'namedStyleType'
                }
            }
        ])
        current_index += len(title) + 1

    # Other metadata as subtitle
    metadata_lines = []
    for key, value in metadata.items():
        if key != 'title':
            metadata_lines.append(f"{key.title()}: {value}")

    if metadata_lines:
        metadata_text = ' | '.join(metadata_lines) + '\n'
        requests.extend([
            {
                'insertText': {
                    'location': {'index': current_index},
                    'text': metadata_text
                }
            },
            {
                'updateParagraphStyle': {
                    'range': {
                        'startIndex': current_index,
                        'endIndex': current_index + len(metadata_text) - 1
                    },
                    'paragraphStyle': {
                        'namedStyleType': 'SUBTITLE'
                    },
                    'fields': 'namedStyleType'
                }
            }
        ])
        current_index += len(metadata_text)

    # Add separator
    requests.append({
        'insertText': {
            'location': {'index': current_index},
            'text': '\n'
        }
    })

    return requests
```

---

## Complete Conversion Function

**app/converters/google_docs_converter.py**:
```python
import frontmatter
from googleapiclient.discovery import build
from google.oauth2 import service_account
import logging

logger = logging.getLogger(__name__)

class GoogleDocsConverter:
    """Convert markdown to Google Docs using Docs API."""

    def __init__(self, docs_service, drive_service):
        self.docs_service = docs_service
        self.drive_service = drive_service

    def convert(self, markdown_content: str, title: str,
                make_public: bool = True) -> dict:
        """
        Convert markdown to Google Docs.

        Args:
            markdown_content: Markdown text with optional YAML front matter
            title: Document title
            make_public: Whether to set "anyone with link" permissions

        Returns:
            dict with documentId, webViewLink

        Raises:
            ValueError: If conversion fails
        """
        try:
            # Parse front matter
            post = frontmatter.loads(markdown_content)
            metadata = post.metadata
            content = post.content

            # Override title from front matter if present
            if 'title' in metadata:
                title = metadata['title']

            # Create empty document
            logger.info(f"Creating Google Doc: {title}")
            document = self.docs_service.documents().create(
                body={'title': title}
            ).execute()
            doc_id = document.get('documentId')

            # Build conversion requests
            requests = []

            # Add front matter
            if metadata:
                requests.extend(format_front_matter(metadata))

            # Convert markdown content
            # Option A: Use markgdoc (if installed)
            # Option B: Use custom parser
            content_requests = self._parse_markdown_content(content)
            requests.extend(content_requests)

            # Apply all changes in single batch
            if requests:
                logger.debug(f"Applying {len(requests)} requests to document")
                self.docs_service.documents().batchUpdate(
                    documentId=doc_id,
                    body={'requests': requests}
                ).execute()

            # Set permissions
            if make_public:
                logger.info(f"Making document {doc_id} publicly shareable")
                self.drive_service.permissions().create(
                    fileId=doc_id,
                    body={'type': 'anyone', 'role': 'reader'}
                ).execute()

            # Get shareable link
            file_metadata = self.drive_service.files().get(
                fileId=doc_id,
                fields='webViewLink'
            ).execute()

            logger.info(f"Document created successfully: {doc_id}")
            return {
                'documentId': doc_id,
                'webViewLink': file_metadata.get('webViewLink'),
                'title': title
            }

        except Exception as e:
            logger.error(f"Failed to convert markdown to Google Docs: {e}",
                        exc_info=True)
            raise ValueError(f"Conversion failed: {str(e)}") from e

    def _parse_markdown_content(self, content: str) -> list:
        """
        Parse markdown content into Docs API requests.

        This is a simplified implementation. For production:
        - Use markgdoc library, OR
        - Implement full markdown parser with regex/tree parsing
        """
        # Placeholder - implement full parsing logic here
        # See earlier sections for complete implementation
        return []
```

---

## Testing Strategy

### Unit Tests

```python
import unittest
from app.converters.google_docs_converter import GoogleDocsConverter

class TestGoogleDocsConverter(unittest.TestCase):

    def test_parse_headings(self):
        """Test heading conversion."""
        md = "# Heading 1\n## Heading 2"
        requests = GoogleDocsConverter._parse_markdown_content(md)

        # Verify insertText requests
        self.assertTrue(any('insertText' in r for r in requests))
        # Verify updateParagraphStyle requests
        self.assertTrue(any('updateParagraphStyle' in r for r in requests))

    def test_parse_bold_italic(self):
        """Test inline formatting."""
        md = "This is **bold** and *italic*"
        requests = GoogleDocsConverter._parse_markdown_content(md)

        # Verify text style updates
        style_requests = [r for r in requests if 'updateTextStyle' in r]
        self.assertEqual(len(style_requests), 2)

    def test_front_matter(self):
        """Test YAML front matter parsing."""
        md = """---
title: Test Document
author: John Doe
---
Content here
"""
        requests = format_front_matter({'title': 'Test Document', 'author': 'John Doe'})
        self.assertTrue(len(requests) > 0)
```

### Integration Tests

```python
def test_full_conversion(self):
    """Test complete markdown to Google Docs conversion."""
    markdown = """---
title: Integration Test
---

# Introduction

This is a test document with **bold** and *italic* text.

## Features

- Feature 1
- Feature 2

```python
def hello():
    print("Hello World")
```
"""

    converter = GoogleDocsConverter(docs_service, drive_service)
    result = converter.convert(markdown, "Test Document")

    assert 'documentId' in result
    assert 'webViewLink' in result

    # Clean up
    drive_service.files().delete(fileId=result['documentId']).execute()
```

---

## Performance Considerations

### Batch Size

Google Docs API doesn't specify explicit batch size limits, but best practices:
- Keep batch updates under 50 requests when possible
- For large documents (>1000 lines), split into multiple batches
- Monitor API response times and adjust accordingly

### Optimization Tips

1. **Combine Sequential Inserts**:
   ```python
   # Instead of multiple insertText requests
   requests = [
       {'insertText': {'location': {'index': 1}, 'text': 'Line 1\n'}},
       {'insertText': {'location': {'index': 8}, 'text': 'Line 2\n'}},
   ]

   # Combine into single insert
   requests = [
       {'insertText': {'location': {'index': 1}, 'text': 'Line 1\nLine 2\n'}}
   ]
   ```

2. **Pre-calculate Indices**: Build complete request list before API call
3. **Cache Service Clients**: Reuse `docs_service` and `drive_service` across conversions
4. **Async Processing**: For multiple documents, use async/await or threading

---

## Error Handling

```python
from googleapiclient.errors import HttpError

def safe_convert(markdown_content: str, title: str) -> dict:
    """Convert with comprehensive error handling."""
    try:
        converter = GoogleDocsConverter(docs_service, drive_service)
        return converter.convert(markdown_content, title)

    except HttpError as e:
        if e.resp.status == 429:
            logger.warning("Rate limit exceeded, retry needed")
            raise ConversionError("Service temporarily busy, please retry")
        elif e.resp.status == 403:
            logger.error("Permission denied")
            raise ConversionError("API access denied")
        else:
            logger.error(f"API error: {e.content}")
            raise ConversionError(f"Conversion failed: {e}")

    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise ConversionError("Internal conversion error")
```

---

## Summary

**For Rapid Implementation**:
- Use `markgdoc` library
- Handle unsupported elements separately
- Estimated time: 10-15 hours

**For Full Control**:
- Build custom parser
- Implement all markdown elements
- Estimated time: 25-35 hours

**Hybrid Approach** (Recommended):
- Use `markgdoc` for common elements
- Custom handlers for code blocks, complex tables
- Estimated time: 15-20 hours

**Next Steps**: Review `python-libraries.md` for dependency management and `deployment-configuration.md` for production setup.
