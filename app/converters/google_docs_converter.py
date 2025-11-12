"""
Google Docs Converter
Location: /Users/jrosenbaum/Documents/Code/md-converter/app/converters/google_docs_converter.py

Converts markdown and HTML content to Google Docs format
using the Google Docs API v1.

Dependencies:
    - google-api-python-client: Google API client
    - markgdoc: Markdown to Google Docs conversion (optional)
    - python-frontmatter: YAML front matter parsing
    - beautifulsoup4: HTML parsing
    - requests: Image downloading

Used by: app/api/routes.py for Google Docs conversion requests
"""
import frontmatter
import logging
import time
import io
import requests
from typing import Dict, Tuple, Optional, List
from googleapiclient.discovery import Resource
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseUpload
from bs4 import BeautifulSoup
from app.utils.security import validate_image_url

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

    def _create_first_page_header(self, doc_id: str, metadata: Dict) -> None:
        """
        Create a header on the first page with front matter content.

        Args:
            doc_id: Document ID
            metadata: Front matter metadata dict

        Raises:
            HttpError: If header creation fails
        """
        self.logger.debug("Creating header with front matter")

        # Create default header (appears on all pages including first)
        requests = [{
            'createHeader': {
                'type': 'DEFAULT'
            }
        }]

        # Execute to get header ID
        response = self.docs_service.documents().batchUpdate(
            documentId=doc_id,
            body={'requests': requests}
        ).execute()

        # Get the header ID from the response
        header_id = response['replies'][0]['createHeader']['headerId']
        self.logger.debug(f"Created header with ID: {header_id}")

        # Step 4: Build front matter content for header
        header_text = self._format_front_matter_for_header(metadata)

        # Step 5: Insert text into header
        insert_requests = [{
            'insertText': {
                'location': {
                    'segmentId': header_id,
                    'index': 0
                },
                'text': header_text
            }
        }]

        # Apply text formatting to header
        # Apply bold to the entire header text
        if len(header_text) > 0:
            insert_requests.append({
                'updateTextStyle': {
                    'range': {
                        'segmentId': header_id,
                        'startIndex': 0,
                        'endIndex': len(header_text)
                    },
                    'textStyle': {
                        'fontSize': {
                            'magnitude': 10,
                            'unit': 'PT'
                        }
                    },
                    'fields': 'fontSize'
                }
            })

        self.docs_service.documents().batchUpdate(
            documentId=doc_id,
            body={'requests': insert_requests}
        ).execute()

        self.logger.debug("Front matter added to header")

    def _format_front_matter_for_header(self, metadata: Dict) -> str:
        """
        Format front matter as plain text for header.

        Args:
            metadata: Front matter key-value pairs

        Returns:
            str: Formatted header text
        """
        lines = []

        # Add title if present
        if 'title' in metadata:
            lines.append(metadata['title'])

        # Add other metadata
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

                lines.append(f"{key_display}: {value_str}")

        return '\n'.join(lines)

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

        # If we have front matter, add it to the first page header
        if metadata:
            self._create_first_page_header(doc_id, metadata)

        # Build list of batchUpdate requests for markdown body
        requests = self._build_requests(markdown_body, metadata=None)  # No metadata in body anymore

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

    def _build_requests(self, markdown_body: str, metadata: Optional[Dict] = None) -> list:
        """
        Build Docs API batchUpdate requests from markdown.

        Args:
            markdown_body: Markdown content string
            metadata: Front matter metadata (optional, used for body insertion - deprecated)

        Returns:
            list: Docs API request dicts

        Note: Front matter is now added to the header, not the body.
        """
        requests = []
        start_index = 1

        # Convert markdown to API requests (starting from index 1)
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

    def convert_html(
        self,
        html_content: str,
        title: str,
        make_public: bool = False
    ) -> Dict[str, str]:
        """
        Convert HTML to Google Docs.

        Args:
            html_content: HTML content string
            title: Document title
            make_public: Whether to make document publicly viewable (default False)

        Returns:
            dict with:
                - documentId: Google Docs document ID
                - webViewLink: URL to view document
                - title: Final document title

        Raises:
            GoogleDocsConversionError: If conversion fails

        Example:
            >>> result = converter.convert_html("<h1>Hello</h1>", "Test Doc")
            >>> doc_url = result['webViewLink']
        """
        self.logger.info(f"Starting Google Docs HTML conversion: {title}")
        start_time = time.time()

        try:
            # Step 1: Create empty document
            doc_id = self._create_document(title)
            self.logger.info(f"Document created: {doc_id}")

            # Step 2: Parse HTML and apply content
            self._apply_html_content(doc_id, html_content)
            self.logger.info(f"HTML content applied to document: {doc_id}")

            # Step 3: Set permissions if requested
            if make_public:
                self._make_public(doc_id)
                self.logger.info(f"Document made publicly viewable: {doc_id}")

            # Step 4: Get shareable link
            web_link = self._get_share_link(doc_id)
            self.logger.info(f"Shareable link generated: {web_link}")

            elapsed = time.time() - start_time
            self.logger.info(f"HTML conversion completed in {elapsed:.2f}s")

            return {
                'documentId': doc_id,
                'webViewLink': web_link,
                'title': title
            }

        except HttpError as e:
            error_msg = f"Google API error during HTML conversion: {e.content}"
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
                    f"Failed to convert HTML to Google Docs: {e.resp.status}"
                ) from e

        except Exception as e:
            error_msg = f"Unexpected error during HTML conversion: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            raise GoogleDocsConversionError(error_msg) from e

    def _apply_html_content(self, doc_id: str, html_content: str) -> None:
        """
        Apply HTML content to document via batchUpdate.

        Args:
            doc_id: Document ID
            html_content: HTML content string

        Raises:
            HttpError: If batchUpdate fails
        """
        self.logger.debug(f"Building API requests for HTML document: {doc_id}")

        # Build list of batchUpdate requests from HTML
        requests = self._parse_html_to_requests(html_content, start_index=1)

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

    def _parse_html_to_requests(self, html_content: str, start_index: int = 1) -> List[dict]:
        """
        Parse HTML and convert to Google Docs API requests.

        Supports: headings, paragraphs, bold, italic, links, images, lists, tables.

        Args:
            html_content: HTML content string
            start_index: Starting index position in document (default: 1)

        Returns:
            List of Google Docs API request dicts

        Example:
            >>> requests = converter._parse_html_to_requests('<h1>Title</h1><p>Text</p>')
        """
        self.logger.debug("Parsing HTML with BeautifulSoup")

        try:
            soup = BeautifulSoup(html_content, 'html.parser')
        except Exception as e:
            self.logger.error(f"Failed to parse HTML: {e}")
            raise GoogleDocsConversionError(f"Invalid HTML content: {e}")

        requests = []
        current_index = start_index

        # Process body content (or entire soup if no body tag)
        body = soup.find('body') or soup

        for element in body.descendants:
            # Skip text nodes that are just whitespace
            if element.name is None and not str(element).strip():
                continue

            # Process elements
            if element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                # Heading
                level = int(element.name[1])
                text = element.get_text() + '\n'

                requests.append({
                    'insertText': {
                        'location': {'index': current_index},
                        'text': text
                    }
                })

                heading_type = f'HEADING_{level}' if level <= 6 else 'HEADING_6'
                requests.append({
                    'updateParagraphStyle': {
                        'range': {
                            'startIndex': current_index,
                            'endIndex': current_index + len(text) - 1
                        },
                        'paragraphStyle': {
                            'namedStyleType': heading_type
                        },
                        'fields': 'namedStyleType'
                    }
                })

                current_index += len(text)
                # Consume children
                for child in element.descendants:
                    if child != element:
                        child.extract()

            elif element.name == 'p':
                # Paragraph
                text = element.get_text() + '\n'

                requests.append({
                    'insertText': {
                        'location': {'index': current_index},
                        'text': text
                    }
                })

                current_index += len(text)
                # Consume children
                for child in element.descendants:
                    if child != element:
                        child.extract()

            elif element.name == 'img':
                # Image - fetch and upload to Drive
                img_url = element.get('src')
                if img_url:
                    try:
                        image_request = self._create_image_request(img_url, current_index)
                        if image_request:
                            requests.append(image_request)
                            current_index += 1  # Images take 1 index position
                    except Exception as e:
                        self.logger.warning(f"Failed to insert image {img_url}: {e}")
                        # Insert placeholder text instead
                        placeholder = f"[Image: {img_url}]\n"
                        requests.append({
                            'insertText': {
                                'location': {'index': current_index},
                                'text': placeholder
                            }
                        })
                        current_index += len(placeholder)

            elif element.name == 'br':
                # Line break
                requests.append({
                    'insertText': {
                        'location': {'index': current_index},
                        'text': '\n'
                    }
                })
                current_index += 1

        # If no requests were created, insert the plain text
        if not requests:
            text = body.get_text()
            if text.strip():
                requests.append({
                    'insertText': {
                        'location': {'index': 1},
                        'text': text
                    }
                })

        return requests

    def _create_image_request(self, image_url: str, index: int) -> Optional[dict]:
        """
        Fetch image from URL, upload to Drive, and create insert request.

        Args:
            image_url: URL of image to fetch
            index: Index position to insert image

        Returns:
            Google Docs API request dict for inserting image, or None if failed

        Raises:
            Exception: If image fetch or upload fails
        """
        # Validate URL (SSRF prevention)
        if not validate_image_url(image_url):
            self.logger.warning(f"Skipping unsafe image URL: {image_url}")
            return None

        self.logger.debug(f"Fetching image: {image_url}")

        try:
            # Fetch image
            response = requests.get(
                image_url,
                timeout=10,
                headers={'User-Agent': 'MD-Converter/1.0'}
            )
            response.raise_for_status()

            # Get content type
            content_type = response.headers.get('content-type', 'image/png')
            if not content_type.startswith('image/'):
                self.logger.warning(f"URL is not an image: {content_type}")
                return None

            # Check size (max 10MB)
            if len(response.content) > 10 * 1024 * 1024:
                self.logger.warning(f"Image too large: {len(response.content)} bytes")
                return None

            # Upload to Drive
            media = MediaIoBaseUpload(
                io.BytesIO(response.content),
                mimetype=content_type,
                resumable=True
            )

            file_metadata = {
                'name': f'image_{int(time.time())}.{content_type.split("/")[1]}',
                'mimeType': content_type
            }

            file = self.drive_service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id,webContentLink'
            ).execute()

            file_id = file.get('id')
            self.logger.debug(f"Image uploaded to Drive: {file_id}")

            # Create insertInlineImage request
            return {
                'insertInlineImage': {
                    'uri': f"https://drive.google.com/uc?id={file_id}",
                    'location': {'index': index}
                }
            }

        except requests.RequestException as e:
            self.logger.error(f"Failed to fetch image {image_url}: {e}")
            raise
        except HttpError as e:
            self.logger.error(f"Failed to upload image to Drive: {e}")
            raise

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
