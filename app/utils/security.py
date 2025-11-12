"""
Security Utilities
Location: /mnt/c/Users/Joseph/Documents/Code/md-converter/app/utils/security.py

This module provides security utilities including:
- Filename sanitization
- Content validation
- Input sanitization for metadata
- HTML sanitization (XSS prevention)
- Image URL validation (SSRF prevention)

Used by: app/api/validators.py and app/converters/markdown_converter.py
"""
import re
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from werkzeug.utils import secure_filename as werkzeug_secure_filename
import bleach


logger = logging.getLogger(__name__)


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent directory traversal and other attacks.

    Args:
        filename: Original filename

    Returns:
        Sanitized filename safe for storage

    Example:
        >>> sanitize_filename("../../etc/passwd")
        'passwd'
        >>> sanitize_filename("my document.md")
        'my_document.md'
    """
    # Use werkzeug's secure_filename as base
    safe_name = werkzeug_secure_filename(filename)

    # Additional sanitization
    # Remove any remaining path separators
    safe_name = safe_name.replace('/', '').replace('\\', '')

    # Remove special characters that could cause issues
    safe_name = re.sub(r'[^\w\s.-]', '', safe_name)

    # Replace multiple spaces/underscores with single underscore
    safe_name = re.sub(r'[\s_]+', '_', safe_name)

    # Limit length to 255 characters (filesystem limit)
    if len(safe_name) > 255:
        base, ext = Path(safe_name).stem, Path(safe_name).suffix
        max_base_len = 255 - len(ext)
        safe_name = base[:max_base_len] + ext

    # Ensure not empty after sanitization
    if not safe_name or safe_name == '.':
        safe_name = 'unnamed.md'

    logger.debug(f'Sanitized filename: {filename} -> {safe_name}')
    return safe_name


def sanitize_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitize metadata fields to prevent injection attacks.

    Args:
        metadata: Dictionary of metadata fields

    Returns:
        Sanitized metadata dictionary

    Example:
        >>> metadata = {'title': '<script>alert("xss")</script>'}
        >>> sanitized = sanitize_metadata(metadata)
        >>> print(sanitized['title'])
        'alert("xss")'
    """
    sanitized = {}

    for key, value in metadata.items():
        # Sanitize key (alphanumeric, underscore, hyphen only)
        clean_key = re.sub(r'[^\w-]', '_', str(key))[:50]

        # Sanitize value based on type
        if isinstance(value, str):
            # Remove HTML/script tags
            clean_value = re.sub(r'<[^>]+>', '', value)
            # Remove potential JavaScript
            clean_value = re.sub(r'javascript:', '', clean_value, flags=re.IGNORECASE)
            # Limit length
            clean_value = clean_value[:500]

        elif isinstance(value, (int, float, bool)):
            clean_value = value

        elif isinstance(value, list):
            # Sanitize list items
            clean_value = []
            for item in value[:10]:  # Limit list size
                if isinstance(item, str):
                    item_clean = re.sub(r'<[^>]+>', '', str(item))[:100]
                    clean_value.append(item_clean)
                else:
                    clean_value.append(str(item)[:100])

        elif isinstance(value, dict):
            # Recursively sanitize nested dicts
            clean_value = sanitize_metadata(value)

        else:
            # Convert other types to string and sanitize
            clean_value = re.sub(r'<[^>]+>', '', str(value))[:500]

        if clean_key:
            sanitized[clean_key] = clean_value

    return sanitized


def validate_file_content(content: str, max_size: int = 10 * 1024 * 1024) -> bool:
    """
    Validate file content for safety.

    Args:
        content: File content string
        max_size: Maximum allowed size in bytes

    Returns:
        True if valid, False otherwise

    Raises:
        ValueError: If content is invalid with reason
    """
    # Check size
    content_size = len(content.encode('utf-8'))
    if content_size > max_size:
        raise ValueError(f'Content too large: {content_size} bytes (max: {max_size})')

    # Check for null bytes (binary file indicator)
    if '\x00' in content:
        raise ValueError('Binary content detected in text file')

    # Check for suspicious patterns (log but don't block)
    suspicious_patterns = [
        r'<script[^>]*>',
        r'javascript:',
        r'onerror=',
        r'onload=',
        r'eval\(',
        r'exec\('
    ]

    for pattern in suspicious_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            logger.warning(f'Suspicious pattern detected in content: {pattern}')
            # Don't block - markdown rendering will escape HTML

    return True


def check_allowed_extension(filename: str, allowed_extensions: set) -> bool:
    """
    Check if file extension is allowed.

    Args:
        filename: Filename to check
        allowed_extensions: Set of allowed extensions (without dots)

    Returns:
        True if allowed, False otherwise

    Example:
        >>> check_allowed_extension('doc.md', {'md', 'markdown'})
        True
        >>> check_allowed_extension('doc.exe', {'md', 'markdown'})
        False
    """
    if '.' not in filename:
        return False

    ext = filename.rsplit('.', 1)[1].lower()
    return ext in allowed_extensions


def sanitize_path_component(component: str) -> str:
    """
    Sanitize a path component to prevent directory traversal.

    Args:
        component: Path component string

    Returns:
        Sanitized path component

    Example:
        >>> sanitize_path_component("../../../etc")
        'etc'
    """
    # Remove parent directory references
    component = component.replace('..', '')
    component = component.replace('./', '')

    # Remove leading/trailing slashes
    component = component.strip('/')
    component = component.strip('\\')

    # Remove special characters
    component = re.sub(r'[^\w.-]', '_', component)

    return component


def is_safe_redirect_url(url: str, allowed_hosts: list) -> bool:
    """
    Check if a redirect URL is safe.

    Args:
        url: URL to validate
        allowed_hosts: List of allowed hostnames

    Returns:
        True if safe, False otherwise
    """
    if not url:
        return False

    # Only allow relative URLs or URLs from allowed hosts
    if url.startswith('/'):
        return True

    # Check for allowed hosts
    from urllib.parse import urlparse
    parsed = urlparse(url)

    if not parsed.scheme or not parsed.netloc:
        return True  # Relative URL

    return parsed.netloc in allowed_hosts


def generate_csrf_token() -> str:
    """
    Generate a CSRF token.

    Returns:
        Random CSRF token string
    """
    import secrets
    return secrets.token_urlsafe(32)


def validate_csrf_token(token: str, session_token: str) -> bool:
    """
    Validate CSRF token against session token.

    Args:
        token: Token from request
        session_token: Token from session

    Returns:
        True if valid, False otherwise
    """
    import secrets
    try:
        return secrets.compare_digest(token, session_token)
    except (TypeError, ValueError):
        return False


# HTML Sanitization Functions

ALLOWED_HTML_TAGS = [
    # Text formatting
    'p', 'br', 'span', 'div',
    # Headings
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    # Text styles
    'strong', 'em', 'b', 'i', 'u', 's', 'code', 'pre',
    # Lists
    'ul', 'ol', 'li',
    # Tables
    'table', 'thead', 'tbody', 'tfoot', 'tr', 'th', 'td', 'caption',
    # Links and images
    'a', 'img',
    # Quotes and sections
    'blockquote', 'q', 'cite',
    # Horizontal rule
    'hr',
    # Definitions
    'dl', 'dt', 'dd',
]

ALLOWED_HTML_ATTRIBUTES = {
    'a': ['href', 'title', 'name'],
    'img': ['src', 'alt', 'title', 'width', 'height'],
    'table': ['border', 'cellpadding', 'cellspacing', 'width'],
    'th': ['align', 'valign', 'colspan', 'rowspan', 'scope'],
    'td': ['align', 'valign', 'colspan', 'rowspan'],
    'tr': ['align', 'valign'],
    'col': ['span', 'width'],
    'colgroup': ['span', 'width'],
    'code': ['class'],  # For syntax highlighting classes
    'pre': ['class'],
    'div': ['class'],
    'span': ['class'],
}

ALLOWED_HTML_PROTOCOLS = ['http', 'https', 'data', 'mailto']


def sanitize_html(html_content: str, strip_comments: bool = True) -> str:
    """
    Sanitize HTML content to prevent XSS attacks.

    Uses bleach library to strip dangerous tags, attributes, and protocols
    while preserving safe HTML structure and content.

    Args:
        html_content: Raw HTML string to sanitize
        strip_comments: Whether to strip HTML comments (default: True)

    Returns:
        Sanitized HTML string safe for processing

    Example:
        >>> sanitize_html('<script>alert("xss")</script><p>Hello</p>')
        '<p>Hello</p>'
        >>> sanitize_html('<a href="javascript:alert()">Click</a>')
        '<a>Click</a>'
    """
    if not html_content:
        return ""

    try:
        # Sanitize with bleach
        sanitized = bleach.clean(
            html_content,
            tags=ALLOWED_HTML_TAGS,
            attributes=ALLOWED_HTML_ATTRIBUTES,
            protocols=ALLOWED_HTML_PROTOCOLS,
            strip=True,  # Remove disallowed tags entirely
            strip_comments=strip_comments
        )

        logger.debug(f'HTML sanitized: {len(html_content)} -> {len(sanitized)} bytes')
        return sanitized

    except Exception as e:
        logger.error(f'HTML sanitization failed: {e}', exc_info=True)
        # Return empty string on error (fail secure)
        return ""


def validate_html_content(content: str, max_size: int = 10 * 1024 * 1024) -> Optional[Dict[str, Any]]:
    """
    Validate HTML content for safety and size limits.

    Args:
        content: HTML content string
        max_size: Maximum allowed size in bytes (default: 10MB)

    Returns:
        Error dictionary if invalid, None if valid

    Example:
        >>> error = validate_html_content('<html>...</html>')
        >>> if error is None:
        >>>     # Content is valid
    """
    # Check size
    content_size = len(content.encode('utf-8'))
    if content_size > max_size:
        return {
            'error': f'HTML file too large: {content_size} bytes',
            'code': 'HTML_TOO_LARGE',
            'status': 413,
            'max_size': max_size,
            'actual_size': content_size
        }

    # Check for null bytes (binary content)
    if '\x00' in content:
        return {
            'error': 'HTML file contains binary data',
            'code': 'BINARY_CONTENT',
            'status': 422
        }

    # Check minimum length
    if len(content.strip()) == 0:
        return {
            'error': 'HTML file is empty',
            'code': 'EMPTY_CONTENT',
            'status': 422
        }

    # Log suspicious patterns (but don't block - sanitization will handle)
    suspicious_patterns = [
        (r'<base\s', 'base tag'),
        (r'<iframe', 'iframe tag'),
        (r'<object', 'object tag'),
        (r'<embed', 'embed tag'),
        (r'javascript:', 'javascript protocol'),
        (r'vbscript:', 'vbscript protocol'),
    ]

    for pattern, name in suspicious_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            logger.warning(f'Suspicious pattern detected in HTML: {name}')

    # Valid
    return None


def validate_image_url(url: str) -> bool:
    """
    Validate image URL is safe to fetch (SSRF prevention).

    Blocks:
    - Non-HTTP/HTTPS protocols
    - Private IP ranges (10.x.x.x, 192.168.x.x, 172.16-31.x.x)
    - Loopback addresses (127.x.x.x, localhost)
    - Cloud metadata endpoints (169.254.169.254)
    - Link-local addresses

    Args:
        url: Image URL to validate

    Returns:
        True if safe to fetch, False otherwise

    Example:
        >>> validate_image_url('https://example.com/image.png')
        True
        >>> validate_image_url('http://192.168.1.1/private.jpg')
        False
        >>> validate_image_url('http://169.254.169.254/metadata')
        False
    """
    if not url:
        return False

    # Allow data URIs (base64 encoded images)
    if url.startswith('data:image/'):
        return True

    from urllib.parse import urlparse
    import ipaddress

    try:
        parsed = urlparse(url)

        # Only allow HTTP/HTTPS
        if parsed.scheme not in ['http', 'https']:
            logger.warning(f'Blocked non-HTTP(S) image URL: {parsed.scheme}://')
            return False

        # Must have a hostname
        if not parsed.hostname:
            logger.warning('Blocked image URL without hostname')
            return False

        hostname = parsed.hostname.lower()

        # Block localhost
        if hostname in ['localhost', 'localhost.localdomain']:
            logger.warning(f'Blocked localhost image URL: {hostname}')
            return False

        # Try to parse as IP address
        try:
            ip = ipaddress.ip_address(hostname)

            # Block private IP ranges
            if ip.is_private:
                logger.warning(f'Blocked private IP image URL: {ip}')
                return False

            # Block loopback
            if ip.is_loopback:
                logger.warning(f'Blocked loopback IP image URL: {ip}')
                return False

            # Block link-local (169.254.x.x - AWS/GCP metadata)
            if ip.is_link_local:
                logger.warning(f'Blocked link-local IP image URL: {ip}')
                return False

            # Block reserved ranges
            if ip.is_reserved:
                logger.warning(f'Blocked reserved IP image URL: {ip}')
                return False

        except ValueError:
            # Not an IP address, it's a hostname - that's fine
            pass

        # Additional hostname checks
        blocked_hostnames = [
            'metadata.google.internal',
            'metadata',
            'instance-data',
        ]

        if any(blocked in hostname for blocked in blocked_hostnames):
            logger.warning(f'Blocked suspicious hostname: {hostname}')
            return False

        return True

    except Exception as e:
        logger.error(f'Error validating image URL: {e}')
        return False


def count_html_images(html_content: str, max_images: int = 100) -> Optional[Dict[str, Any]]:
    """
    Count images in HTML and check against limit (DOS prevention).

    Args:
        html_content: HTML content string
        max_images: Maximum allowed images per document

    Returns:
        Error dictionary if too many images, None if valid

    Example:
        >>> error = count_html_images('<html><img src="1.jpg"><img src="2.jpg"></html>', max_images=1)
        >>> if error:
        >>>     # Too many images
    """
    from bs4 import BeautifulSoup

    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        img_tags = soup.find_all('img')
        count = len(img_tags)

        if count > max_images:
            return {
                'error': f'Too many images in HTML: {count} (max: {max_images})',
                'code': 'TOO_MANY_IMAGES',
                'status': 413,
                'max_images': max_images,
                'actual_count': count
            }

        logger.debug(f'HTML contains {count} images')
        return None

    except Exception as e:
        logger.error(f'Error counting HTML images: {e}')
        # Don't block on parsing errors
        return None
