"""
API Routes
Location: /mnt/c/Users/Joseph/Documents/Code/md-converter/app/api/routes.py

This module defines the API endpoints for the markdown converter service:
- POST /api/convert - Convert markdown to document formats
- GET /api/download/<job_id>/<format> - Download converted files

Dependencies:
    - app/api/validators: Request validation
    - app/converters/markdown_converter: Conversion logic
    - app/utils/file_handler: File management
    - app/utils/helpers: Response formatting

Used by: app/__init__.py via blueprint registration
"""
from flask import request, jsonify, send_file, current_app
from werkzeug.utils import secure_filename
from pathlib import Path
from datetime import datetime
import logging
import os

from app.api import api_blueprint
from app.api.validators import validate_upload, validate_job_id, validate_content_encoding, validate_markdown_content
from app.converters import MarkdownConverter
from app.utils.file_handler import (
    generate_job_id,
    get_job_directory,
    get_file_path,
    get_file_info,
    is_job_expired,
    cleanup_old_files
)
from app.utils.helpers import (
    format_error_response,
    get_mime_type,
    calculate_processing_time,
    format_file_size
)
from app.utils.security import sanitize_filename


logger = logging.getLogger(__name__)


@api_blueprint.route('/convert', methods=['POST'])
def convert():
    """
    Convert markdown file to document format(s).

    Accepts:
        - multipart/form-data with 'file' field (markdown file)
        - form parameter 'formats': array of format strings (new style)
        - form parameter 'format': single format string (legacy style)

    Returns:
        - If multiple formats: JSON with download URLs and metadata
        - If single format (legacy): Direct file download

    Status Codes:
        200: Success
        400: Invalid request (no formats, invalid format)
        401: Authentication required (for Google Docs)
        413: File too large
        415: Invalid file type
        422: Invalid content
        429: Rate limit exceeded
        500: Conversion error
    """
    start_time = datetime.utcnow()

    # Validate request
    validation_error = validate_upload(request)
    if validation_error:
        return jsonify(validation_error), validation_error['status']

    try:
        # Extract file
        file = request.files['file']
        original_filename = secure_filename(file.filename)
        base_name = Path(original_filename).stem

        # Get formats (support both new array and legacy single param)
        formats = request.form.getlist('formats')  # New style: ['docx', 'pdf', 'gdocs']

        # Backward compatibility: support legacy 'format' parameter
        if not formats:
            legacy_format = request.form.get('format', '').lower()
            if legacy_format == 'both':
                formats = ['docx', 'pdf']
            elif legacy_format in ['docx', 'pdf']:
                # Legacy single format - return file directly
                return handle_legacy_single_format(file, legacy_format, base_name)
            else:
                error = format_error_response(
                    'NO_FORMAT_SELECTED',
                    'No output format selected',
                    400
                )
                return jsonify(error), 400

        # Validate formats
        valid_formats = {'docx', 'pdf', 'gdocs'}
        invalid_formats = set(formats) - valid_formats

        if invalid_formats:
            error = format_error_response(
                'INVALID_FORMAT',
                f'Invalid format(s): {", ".join(invalid_formats)}',
                400,
                {'valid_formats': list(valid_formats)}
            )
            return jsonify(error), 400

        # Check authentication for Google Docs
        if 'gdocs' in formats:
            from flask_dance.contrib.google import google
            if not google.authorized:
                error = format_error_response(
                    'AUTH_REQUIRED',
                    'Google Docs conversion requires authentication. Please sign in.',
                    401,
                    {'auth_url': '/login/google'}
                )
                return jsonify(error), 401

        logger.info(f'Converting file: {original_filename} to formats: {formats}')

        # Validate encoding
        encoding_error = validate_content_encoding(file)
        if encoding_error:
            return jsonify(encoding_error), encoding_error['status']

        # Read content
        try:
            content = file.read().decode('utf-8')
        except UnicodeDecodeError:
            error = format_error_response(
                'INVALID_ENCODING',
                'File must be UTF-8 encoded',
                422
            )
            return jsonify(error), 422

        # Validate content
        content_error = validate_markdown_content(content)
        if content_error:
            return jsonify(content_error), content_error['status']

        # Generate job ID and directory
        job_id = generate_job_id()
        job_dir = get_job_directory(job_id, str(current_app.config['CONVERTED_FOLDER']))

        logger.info(f'Job ID: {job_id}, Directory: {job_dir}')

        # Initialize converter
        converter = MarkdownConverter()

        # Convert to each requested format
        results = {}

        # Convert to DOCX
        if 'docx' in formats:
            try:
                docx_path = os.path.join(job_dir, f'{base_name}.docx')
                converter.convert_to_docx(content, docx_path)

                docx_info = get_file_info(docx_path)
                results['docx'] = {
                    'download_url': f'/api/download/{job_id}/docx',
                    'filename': docx_info['filename'],
                    'size': docx_info['size'],
                    'size_formatted': format_file_size(docx_info['size']),
                    'mimetype': get_mime_type('docx')
                }
                logger.info(f'Successfully converted to DOCX: {docx_path}')
            except Exception as e:
                logger.error(f'DOCX conversion failed: {e}', exc_info=True)
                error = format_error_response(
                    'CONVERSION_ERROR',
                    'Failed to convert to DOCX',
                    500
                )
                return jsonify(error), 500

        # Convert to PDF
        if 'pdf' in formats:
            try:
                pdf_path = os.path.join(job_dir, f'{base_name}.pdf')
                converter.convert_to_pdf(content, pdf_path)

                pdf_info = get_file_info(pdf_path)
                results['pdf'] = {
                    'download_url': f'/api/download/{job_id}/pdf',
                    'filename': pdf_info['filename'],
                    'size': pdf_info['size'],
                    'size_formatted': format_file_size(pdf_info['size']),
                    'mimetype': get_mime_type('pdf')
                }
                logger.info(f'Successfully converted to PDF: {pdf_path}')
            except Exception as e:
                logger.error(f'PDF conversion failed: {e}', exc_info=True)
                error = format_error_response(
                    'CONVERSION_ERROR',
                    'Failed to convert to PDF',
                    500
                )
                return jsonify(error), 500

        # Convert to Google Docs
        if 'gdocs' in formats:
            try:
                from app.utils.oauth_helpers import get_google_credentials
                from app.utils.google_services import build_google_services
                from app.converters.google_docs_converter import GoogleDocsConverter

                # Get OAuth credentials
                credentials = get_google_credentials()

                # Build Google API services
                docs_service, drive_service = build_google_services(credentials)

                # Create converter
                gdocs_converter = GoogleDocsConverter(docs_service, drive_service)

                # Convert
                gdocs_result = gdocs_converter.convert(
                    content,
                    f"{base_name} - Converted"
                )

                results['gdocs'] = {
                    'web_view_link': gdocs_result['webViewLink'],
                    'document_id': gdocs_result['documentId'],
                    'title': gdocs_result['title'],
                    'ownership': 'user'  # Document owned by authenticated user
                }
                logger.info(f'Successfully converted to Google Docs: {gdocs_result["documentId"]}')
            except Exception as e:
                logger.error(f'Google Docs conversion failed: {e}', exc_info=True)

                # Check if rate limit error
                if 'rate limit' in str(e).lower() or '429' in str(e):
                    error = format_error_response(
                        'RATE_LIMIT_EXCEEDED',
                        'Google Docs conversion temporarily unavailable',
                        429,
                        {'retry_after': 60}
                    )
                    return jsonify(error), 429

                error = format_error_response(
                    'CONVERSION_ERROR',
                    'Failed to convert to Google Docs',
                    500
                )
                return jsonify(error), 500

        # Build success response
        processing_time = calculate_processing_time(start_time)

        response = {
            'status': 'success',
            'job_id': job_id,
            'filename': base_name,
            'formats': results,
            'processing_time': round(processing_time, 2),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }

        logger.info(f'Successfully converted {base_name} to {len(formats)} format(s) in {processing_time:.2f}s')
        return jsonify(response), 200

    except Exception as e:
        logger.error(f'Unexpected error during conversion: {e}', exc_info=True)
        error = format_error_response(
            'INTERNAL_ERROR',
            'Internal server error during conversion',
            500
        )
        return jsonify(error), 500


@api_blueprint.route('/download/<job_id>/<format>', methods=['GET'])
def download(job_id: str, format: str):
    """
    Download converted file.

    Args:
        job_id: Unique job identifier (UUID)
        format: File format ('docx' or 'pdf')

    Returns:
        Binary file stream for download

    Status Codes:
        200: Success
        400: Invalid parameters
        404: File not found
        410: File expired
    """
    logger.info(f'Download request: job_id={job_id}, format={format}')

    # Validate job ID
    job_id_error = validate_job_id(job_id)
    if job_id_error:
        return jsonify(job_id_error), job_id_error['status']

    # Validate format
    if format not in ['docx', 'pdf']:
        error = format_error_response(
            'INVALID_FORMAT',
            f'Invalid format: {format}. Must be docx or pdf',
            400,
            {'allowed_formats': ['docx', 'pdf']}
        )
        return jsonify(error), 400

    try:
        base_dir = str(current_app.config['CONVERTED_FOLDER'])

        # Check if job has expired
        if is_job_expired(job_id, base_dir, max_age_hours=24):
            logger.warning(f'Job expired: {job_id}')
            error = format_error_response(
                'FILE_EXPIRED',
                'File has expired and been deleted',
                410,
                {
                    'job_id': job_id,
                    'expiration_policy': '24 hours'
                }
            )
            return jsonify(error), 410

        # Get file path
        file_path = get_file_path(job_id, format, base_dir)

        if not file_path or not os.path.exists(file_path):
            logger.warning(f'File not found: job_id={job_id}, format={format}')
            error = format_error_response(
                'FILE_NOT_FOUND',
                'Converted file not found',
                404,
                {
                    'job_id': job_id,
                    'format': format
                }
            )
            return jsonify(error), 404

        # Get file info for logging
        file_info = get_file_info(file_path)
        logger.info(f'Serving file: {file_info["filename"]} ({file_info["size"]} bytes)')

        # Send file
        return send_file(
            file_path,
            as_attachment=True,
            download_name=file_info['filename'],
            mimetype=get_mime_type(format)
        )

    except ValueError as e:
        # Path traversal or other validation error
        logger.error(f'Validation error: {e}')
        error = format_error_response(
            'INVALID_REQUEST',
            str(e),
            400
        )
        return jsonify(error), 400

    except Exception as e:
        logger.error(f'Unexpected error during download: {e}', exc_info=True)
        error = format_error_response(
            'INTERNAL_ERROR',
            'Internal server error during download',
            500
        )
        return jsonify(error), 500


def handle_legacy_single_format(file, format_type, base_name):
    """
    Handle legacy single format conversion (direct file download).

    This maintains backward compatibility with existing clients
    that expect direct file download instead of JSON response.

    Args:
        file: FileStorage object
        format_type: Format string ('docx' or 'pdf')
        base_name: Base filename without extension

    Returns:
        Binary file response

    Raises:
        Exception: If conversion fails
    """
    # Reset file pointer
    file.seek(0)

    try:
        content = file.read().decode('utf-8')
    except UnicodeDecodeError:
        error = format_error_response(
            'INVALID_ENCODING',
            'File must be UTF-8 encoded',
            422
        )
        return jsonify(error), 422

    # Generate job ID
    job_id = generate_job_id()
    job_dir = get_job_directory(job_id, str(current_app.config['CONVERTED_FOLDER']))

    # Convert
    converter = MarkdownConverter()
    output_path = os.path.join(job_dir, f'{base_name}.{format_type}')

    if format_type == 'docx':
        converter.convert_to_docx(content, output_path)
    else:  # pdf
        converter.convert_to_pdf(content, output_path)

    logger.info(f'Legacy conversion completed: {output_path}')

    # Return file directly
    return send_file(
        output_path,
        as_attachment=True,
        download_name=f'{base_name}.{format_type}',
        mimetype=get_mime_type(format_type)
    )


@api_blueprint.route('/cleanup', methods=['POST'])
def cleanup():
    """
    Manually trigger cleanup of old files.

    This endpoint is protected and should only be called by administrators
    or scheduled tasks. In production, use a proper authentication mechanism.

    Returns:
        JSON with cleanup statistics
    """
    # TODO: Add authentication for this endpoint in production

    try:
        base_dir = str(current_app.config['CONVERTED_FOLDER'])
        max_age_hours = current_app.config.get('CLEANUP_INTERVAL', 24 * 3600) // 3600

        logger.info(f'Starting manual cleanup (max_age={max_age_hours}h)')

        deleted_count = cleanup_old_files(base_dir, max_age_hours)

        response = {
            'status': 'success',
            'message': f'Cleanup completed',
            'deleted_directories': deleted_count,
            'max_age_hours': max_age_hours,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }

        logger.info(f'Cleanup completed: {deleted_count} directories deleted')
        return jsonify(response), 200

    except Exception as e:
        logger.error(f'Cleanup failed: {e}', exc_info=True)
        error = format_error_response(
            'CLEANUP_ERROR',
            'Cleanup operation failed',
            500
        )
        return jsonify(error), 500


@api_blueprint.errorhandler(413)
def request_entity_too_large(error):
    """Handle file too large errors"""
    max_size = current_app.config.get('MAX_FILE_SIZE', 10 * 1024 * 1024)
    error_response = format_error_response(
        'FILE_TOO_LARGE',
        f'File size exceeds maximum limit of {format_file_size(max_size)}',
        413,
        {'max_size': max_size}
    )
    return jsonify(error_response), 413
