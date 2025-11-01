"""
Google Docs Converter
Location: /Users/jrosenbaum/Documents/Code/md-converter/app/converters/google_docs_converter.py

Converts markdown content with YAML front matter to Google Docs format
using the Google Docs API v1 and markgdoc library.

Dependencies:
    - google-api-python-client: Google API client
    - markgdoc: Markdown to Google Docs conversion (optional)
    - python-frontmatter: YAML front matter parsing

Used by: app/api/routes.py for Google Docs conversion requests
"""
import frontmatter
import logging
import time
from typing import Dict, Tuple, Optional
from googleapiclient.discovery import Resource
from googleapiclient.errors import HttpError

# Optional: markgdoc for simplified conversion
try:
    import markgdoc
    MARKGDOC_AVAILABLE = True
except ImportError:
    MARKGDOC_AVAILABLE = False
    logging.warning("markgdoc not installed - using custom markdown parser")


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
        >>> from app.utils.google_services import build_google_services
        >>> from app.utils.oauth_helpers import get_google_credentials
        >>>
        >>> credentials = get_google_credentials()
        >>> docs_service, drive_service = build_google_services(credentials)
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
            >>> result = converter.convert("# Hello\\nWorld", "Test Doc")
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
            self.logger.debug(f"Parsed front matter: {list(post.metadata.keys())}")
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
        to basic text insertion.
        """
        requests = []
        start_index = 1

        # Add front matter as document header
        if metadata:
            front_matter_requests, final_index = self._format_front_matter(metadata)
            requests.extend(front_matter_requests)
            start_index = final_index

        # Convert markdown to API requests
        self.logger.debug("Using custom markdown parser")
        md_requests = self._parse_markdown_to_requests(markdown_body, start_index)
        if isinstance(md_requests, list):
            requests.extend(md_requests)
        elif md_requests:
            requests.append(md_requests)

        return requests

    def _format_front_matter(self, metadata: Dict) -> tuple:
        """
        Format front matter as document header.

        Args:
            metadata: Front matter key-value pairs

        Returns:
            tuple: (list of Docs API requests, final index position)

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
        current_index += 1

        return requests, current_index

    def _parse_markdown_to_requests(self, text: str, start_index: int = 1):
        """
        Parse markdown and convert to Google Docs API requests.

        Converts markdown syntax to properly formatted Google Docs API requests.
        Supports: headings (H1-H6), bold, italic, paragraphs, and line breaks.

        Args:
            text: Markdown text content to parse
            start_index: Starting index position in document (default: 1)

        Returns:
            list: List of Google Docs API request dicts
        """
        import re

        requests = []
        current_index = start_index

        # Split into lines and process
        lines = text.split('\n')

        for line in lines:
            if not line.strip():
                # Empty line - add paragraph break
                requests.append({
                    'insertText': {
                        'location': {'index': current_index},
                        'text': '\n'
                    }
                })
                current_index += 1
                continue

            # Check for headings (# heading)
            heading_match = re.match(r'^(#{1,6})\s+(.+)$', line)
            if heading_match:
                level = len(heading_match.group(1))
                text_content = heading_match.group(2) + '\n'

                # Insert text
                requests.append({
                    'insertText': {
                        'location': {'index': current_index},
                        'text': text_content
                    }
                })

                # Style as heading
                heading_type = f'HEADING_{level}' if level <= 6 else 'HEADING_6'
                requests.append({
                    'updateParagraphStyle': {
                        'range': {
                            'startIndex': current_index,
                            'endIndex': current_index + len(text_content) - 1
                        },
                        'paragraphStyle': {
                            'namedStyleType': heading_type
                        },
                        'fields': 'namedStyleType'
                    }
                })

                current_index += len(text_content)
                continue

            # Regular paragraph with inline formatting
            line_text = line + '\n'

            # Insert the line
            requests.append({
                'insertText': {
                    'location': {'index': current_index},
                    'text': line_text
                }
            })

            # Apply bold formatting (**text** or __text__)
            for match in re.finditer(r'\*\*(.+?)\*\*|__(.+?)__', line):
                start = current_index + match.start()
                end = current_index + match.end()
                requests.append({
                    'updateTextStyle': {
                        'range': {
                            'startIndex': start,
                            'endIndex': end
                        },
                        'textStyle': {
                            'bold': True
                        },
                        'fields': 'bold'
                    }
                })

            # Apply italic formatting (*text* or _text_)
            for match in re.finditer(r'(?<!\*)\*([^*]+?)\*(?!\*)|(?<!_)_([^_]+?)_(?!_)', line):
                start = current_index + match.start()
                end = current_index + match.end()
                requests.append({
                    'updateTextStyle': {
                        'range': {
                            'startIndex': start,
                            'endIndex': end
                        },
                        'textStyle': {
                            'italic': True
                        },
                        'fields': 'italic'
                    }
                })

            current_index += len(line_text)

        # If no requests were created, just insert the raw text
        if not requests:
            return {
                'insertText': {
                    'location': {'index': 1},
                    'text': text
                }
            }

        return requests if isinstance(requests, list) and len(requests) > 1 else requests[0] if requests else {
            'insertText': {
                'location': {'index': 1},
                'text': text
            }
        }

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
