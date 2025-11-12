"""
Request Validators
Location: /mnt/c/Users/Joseph/Documents/Code/md-converter/app/api/validators.py

This module provides request validation logic including:
- File upload validation
- File type checking
- Size validation
- Format parameter validation

Used by: app/api/routes.py for validating incoming requests
"""
import logging
from flask import current_app, Request
from typing import Optional, Dict, Any
from pathlib import Path
from app.utils.security import check_allowed_extension


logger = logging.getLogger(__name__)


def validate_upload(request: Request) -> Optional[Dict[str, Any]]:
    """
    Validate file upload request comprehensively.

    This is the primary validation function that checks:
    - File presence
    - Filename validity
    - File type (extension)
    - Format parameter (if provided)

    Args:
        request: Flask request object

    Returns:
        Error dictionary if validation fails, None if valid

    Example:
        >>> error = validate_upload(request)
        >>> if error:
        >>>     return jsonify(error), error['status']
    """
    # Check file presence
    if 'file' not in request.files:
        logger.warning('No file in request')
        return {
            'error': 'No file provided in request',
            'code': 'MISSING_FILE',
            'status': 400
        }

    file = request.files['file']

    # Check filename
    if not file.filename or file.filename == '':
        logger.warning('Empty filename')
        return {
            'error': 'No file selected',
            'code': 'EMPTY_FILENAME',
            'status': 400
        }

    # Validate file type
    allowed_extensions = current_app.config.get('ALLOWED_EXTENSIONS', {'md', 'markdown', 'txt', 'html', 'htm'})

    if not check_allowed_extension(file.filename, allowed_extensions):
        ext = Path(file.filename).suffix
        logger.warning(f'Invalid file type: {ext}')
        return {
            'error': 'Invalid file type. Allowed types: .md, .markdown, .txt, .html, .htm',
            'code': 'INVALID_FILE_TYPE',
            'status': 415,
            'allowed_types': ['.md', '.markdown', '.txt', '.html', '.htm'],
            'received_type': ext
        }

    # Validate format parameter if provided
    format_param = request.form.get('format', 'both')
    format_error = validate_format(format_param)
    if format_error:
        return format_error

    # File size is automatically checked by Flask's MAX_CONTENT_LENGTH
    # But we can add additional logging
    try:
        file.seek(0, 2)  # Seek to end
        file_size = file.tell()
        file.seek(0)  # Reset to start

        max_size = current_app.config.get('MAX_FILE_SIZE', 10 * 1024 * 1024)
        if file_size > max_size:
            logger.warning(f'File too large: {file_size} bytes (max: {max_size})')
            return {
                'error': f'File size exceeds maximum limit of {max_size} bytes',
                'code': 'FILE_TOO_LARGE',
                'status': 413,
                'max_size': max_size,
                'uploaded_size': file_size
            }

        logger.debug(f'File validation passed: {file.filename} ({file_size} bytes)')

    except Exception as e:
        logger.error(f'Error checking file size: {e}')

    return None  # Valid


def validate_format(format_str: str) -> Optional[Dict[str, Any]]:
    """
    Validate output format parameter.

    Args:
        format_str: Format string to validate

    Returns:
        Error dictionary if invalid, None if valid

    Example:
        >>> error = validate_format('docx')
        >>> if error is None:
        >>>     # Format is valid
    """
    allowed_formats = ['docx', 'pdf', 'both']

    if format_str not in allowed_formats:
        logger.warning(f'Invalid format: {format_str}')
        return {
            'error': 'Invalid format. Allowed formats: docx, pdf, both',
            'code': 'INVALID_FORMAT',
            'status': 400,
            'allowed_formats': allowed_formats,
            'received_format': format_str
        }

    return None


def validate_job_id(job_id: str) -> Optional[Dict[str, Any]]:
    """
    Validate job ID format (UUID).

    Args:
        job_id: Job identifier string

    Returns:
        Error dictionary if invalid, None if valid
    """
    import uuid

    try:
        uuid.UUID(job_id)
        return None  # Valid
    except (ValueError, AttributeError) as e:
        logger.warning(f'Invalid job ID format: {job_id}')
        return {
            'error': 'Invalid job ID format',
            'code': 'INVALID_JOB_ID',
            'status': 400
        }


def validate_content_encoding(file) -> Optional[Dict[str, Any]]:
    """
    Validate file content is UTF-8 encoded text.

    Args:
        file: File object from request

    Returns:
        Error dictionary if invalid, None if valid
    """
    try:
        # Try to read and decode as UTF-8
        content = file.read()
        content.decode('utf-8')
        file.seek(0)  # Reset file pointer
        return None  # Valid

    except UnicodeDecodeError:
        logger.warning('File encoding error - not UTF-8')
        file.seek(0)  # Reset file pointer
        return {
            'error': 'File must be UTF-8 encoded text',
            'code': 'INVALID_ENCODING',
            'status': 422
        }
    except Exception as e:
        logger.error(f'Error validating encoding: {e}')
        file.seek(0)  # Reset file pointer
        return {
            'error': 'Failed to read file',
            'code': 'FILE_READ_ERROR',
            'status': 500
        }


def validate_markdown_content(content: str) -> Optional[Dict[str, Any]]:
    """
    Validate markdown content is safe and parseable.

    Args:
        content: Markdown content string

    Returns:
        Error dictionary if invalid, None if valid
    """
    # Check for null bytes (binary content)
    if '\x00' in content:
        logger.warning('Binary content detected in markdown file')
        return {
            'error': 'File appears to contain binary data',
            'code': 'BINARY_CONTENT',
            'status': 422
        }

    # Check minimum length
    if len(content.strip()) == 0:
        logger.warning('Empty markdown content')
        return {
            'error': 'File is empty',
            'code': 'EMPTY_CONTENT',
            'status': 422
        }

    # Content is valid
    return None


def allowed_file(filename: str) -> bool:
    """
    Check if file extension is allowed.

    Args:
        filename: Filename to check

    Returns:
        True if allowed, False otherwise

    Example:
        >>> allowed_file('document.md')
        True
        >>> allowed_file('document.exe')
        False
    """
    allowed_extensions = current_app.config.get('ALLOWED_EXTENSIONS', {'md', 'markdown', 'txt', 'html', 'htm'})
    return check_allowed_extension(filename, allowed_extensions)
