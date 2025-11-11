# API Endpoint Design

**Document Version**: 1.0
**Date**: 2025-11-01
**Phase**: PACT Architecture
**Status**: Ready for Implementation

---

## Executive Summary

This document specifies the updated API endpoint design for supporting multi-format conversion including Google Docs, while maintaining backward compatibility with existing DOCX and PDF conversion functionality. The design introduces a multi-select format parameter and enhanced response structure.

**Key Changes**:
1. `/api/convert` now accepts multiple formats via array parameter
2. Response structure supports multiple output formats
3. New authentication endpoints for OAuth2 flow
4. Backward compatibility maintained for existing clients
5. Enhanced error responses with auth_url for Google Docs

---

## Endpoint Overview

### New Endpoints

| Method | Endpoint | Purpose | Auth Required |
|--------|----------|---------|---------------|
| GET | `/auth/google` | Initiate OAuth flow | No |
| GET | `/auth/google/authorized` | OAuth callback | No |
| GET | `/auth/logout` | Sign out user | No |
| GET | `/auth/status` | Check auth state (AJAX) | No |

### Modified Endpoints

| Method | Endpoint | Change | Backward Compatible |
|--------|----------|--------|---------------------|
| POST | `/api/convert` | Now accepts `formats` array | Yes (via fallback) |

### Unchanged Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/download/<job_id>/<format>` | Download converted files |
| POST | `/api/cleanup` | Cleanup old files |
| GET | `/health` | Health check (enhanced) |

---

## Endpoint Specifications

### POST /api/convert

**Purpose**: Convert markdown file to one or more output formats

#### Request Specification

**Headers**:
```
Content-Type: multipart/form-data
Cookie: session=<session-cookie>  # For Google Docs authentication
```

**Form Parameters**:

| Parameter | Type | Required | Values | Description |
|-----------|------|----------|--------|-------------|
| `file` | File | Yes | .md, .markdown | Markdown file to convert |
| `formats` | Array | Yes | docx, pdf, gdocs | Output formats (one or more) |

**Legacy Parameter** (Backward Compatibility):

| Parameter | Type | Required | Values | Description |
|-----------|------|----------|--------|-------------|
| `format` | String | No | docx, pdf, both | Single format (deprecated but supported) |

**Example Requests**:

```bash
# Multi-format (new style)
curl -X POST http://localhost:8080/api/convert \
  -F "file=@document.md" \
  -F "formats=docx" \
  -F "formats=pdf" \
  -F "formats=gdocs"

# Single format (legacy style - still supported)
curl -X POST http://localhost:8080/api/convert \
  -F "file=@document.md" \
  -F "format=docx"

# Both formats (legacy style - still supported)
curl -X POST http://localhost:8080/api/convert \
  -F "file=@document.md" \
  -F "format=both"
```

#### Response Specification

**Success Response (Multiple Formats)**:

```json
HTTP/1.1 200 OK
Content-Type: application/json

{
  "status": "success",
  "job_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
  "filename": "document",
  "formats": {
    "docx": {
      "download_url": "/api/download/a1b2c3d4-e5f6-7890-1234-567890abcdef/docx",
      "filename": "document.docx",
      "size": 15234,
      "size_formatted": "14.88 KB",
      "mimetype": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    },
    "pdf": {
      "download_url": "/api/download/a1b2c3d4-e5f6-7890-1234-567890abcdef/pdf",
      "filename": "document.pdf",
      "size": 45678,
      "size_formatted": "44.61 KB",
      "mimetype": "application/pdf"
    },
    "gdocs": {
      "web_view_link": "https://docs.google.com/document/d/abc123xyz/edit",
      "document_id": "abc123xyz",
      "title": "document - Converted",
      "ownership": "user"
    }
  },
  "processing_time": 4.23,
  "timestamp": "2025-11-01T12:34:56Z"
}
```

**Success Response (Single Format - Legacy Compatibility)**:

When using legacy `format=docx` parameter, response is direct file download:

```
HTTP/1.1 200 OK
Content-Type: application/vnd.openxmlformats-officedocument.wordprocessingml.document
Content-Disposition: attachment; filename="document.docx"

[Binary file content]
```

**Error Responses**:

```json
// 400 Bad Request - No formats selected
{
  "error": "No output format selected",
  "code": "NO_FORMAT_SELECTED",
  "status": 400,
  "timestamp": "2025-11-01T12:34:56Z"
}

// 401 Unauthorized - Google Docs requires authentication
{
  "error": "Google Docs conversion requires authentication. Please sign in.",
  "code": "AUTH_REQUIRED",
  "status": 401,
  "auth_url": "https://your-app.railway.app/auth/google",
  "timestamp": "2025-11-01T12:34:56Z"
}

// 415 Unsupported Media Type - Invalid file type
{
  "error": "Invalid file type. Only .md and .markdown files are supported.",
  "code": "INVALID_FILE_TYPE",
  "status": 415,
  "allowed_extensions": [".md", ".markdown"],
  "timestamp": "2025-11-01T12:34:56Z"
}

// 422 Unprocessable Entity - Invalid content
{
  "error": "File must be UTF-8 encoded",
  "code": "INVALID_ENCODING",
  "status": 422,
  "timestamp": "2025-11-01T12:34:56Z"
}

// 429 Too Many Requests - Rate limit exceeded
{
  "error": "Google Docs conversion temporarily unavailable",
  "code": "RATE_LIMIT_EXCEEDED",
  "status": 429,
  "retry_after": 60,
  "timestamp": "2025-11-01T12:34:56Z"
}

// 500 Internal Server Error - Conversion failed
{
  "error": "Document conversion failed",
  "code": "CONVERSION_ERROR",
  "status": 500,
  "timestamp": "2025-11-01T12:34:56Z"
}
```

#### Implementation

**Route Handler** (`app/api/routes.py`):

```python
@api_blueprint.route('/convert', methods=['POST'])
def convert():
    """
    Convert markdown file to one or more output formats.

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
                    {'auth_url': url_for('google.login', _external=True)}
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
                    'download_url': url_for('api.download', job_id=job_id,
                                           format='docx', _external=True),
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
                    'download_url': url_for('api.download', job_id=job_id,
                                           format='pdf', _external=True),
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


def handle_legacy_single_format(file, format_type, base_name):
    """
    Handle legacy single format conversion (direct file download).

    This maintains backward compatibility with existing clients
    that expect direct file download instead of JSON response.
    """
    # Reset file pointer
    file.seek(0)

    content = file.read().decode('utf-8')

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

    # Return file directly
    return send_file(
        output_path,
        as_attachment=True,
        download_name=f'{base_name}.{format_type}',
        mimetype=get_mime_type(format_type)
    )
```

---

### GET /api/download/<job_id>/<format>

**Purpose**: Download converted file (DOCX or PDF)

**Note**: No changes to this endpoint. Continues to work as before.

**Parameters**:
- `job_id`: UUID job identifier
- `format`: File format (docx or pdf)

**Response**: Binary file stream

---

### GET /auth/status

**Purpose**: Check user authentication status (AJAX endpoint)

#### Request Specification

**Headers**:
```
Cookie: session=<session-cookie>
```

**Example Request**:
```bash
curl http://localhost:8080/auth/status \
  -H "Cookie: session=..."
```

#### Response Specification

**Success Response (Authenticated)**:

```json
HTTP/1.1 200 OK
Content-Type: application/json

{
  "authenticated": true,
  "user": {
    "email": "user@example.com",
    "name": "John Doe",
    "picture": "https://lh3.googleusercontent.com/..."
  }
}
```

**Success Response (Not Authenticated)**:

```json
HTTP/1.1 200 OK
Content-Type: application/json

{
  "authenticated": false,
  "user": null
}
```

#### Implementation

See OAuth2 Authentication Design document for implementation details.

---

### GET /auth/logout

**Purpose**: Sign out user and clear session

#### Request Specification

**Headers**:
```
Cookie: session=<session-cookie>
```

#### Response Specification

**Success Response**:

```
HTTP/1.1 302 Found
Location: /
Set-Cookie: session=; Expires=Thu, 01 Jan 1970 00:00:00 GMT; Path=/
```

---

### GET /health

**Purpose**: Health check endpoint (enhanced with OAuth status)

#### Response Specification

**Success Response**:

```json
HTTP/1.1 200 OK
Content-Type: application/json

{
  "status": "healthy",
  "service": "md-converter",
  "version": "1.0.0",
  "features": {
    "docx_conversion": true,
    "pdf_conversion": true,
    "google_docs_conversion": true,
    "oauth_configured": true
  },
  "dependencies": {
    "pandoc": "3.1.8",
    "weasyprint": "62.3",
    "google_oauth": "configured"
  },
  "timestamp": "2025-11-01T12:34:56Z"
}
```

**Degraded Response**:

```json
HTTP/1.1 503 Service Unavailable
Content-Type: application/json

{
  "status": "degraded",
  "service": "md-converter",
  "version": "1.0.0",
  "features": {
    "docx_conversion": true,
    "pdf_conversion": true,
    "google_docs_conversion": false,
    "oauth_configured": false
  },
  "warnings": [
    "OAuth not configured - Google Docs conversion disabled"
  ],
  "timestamp": "2025-11-01T12:34:56Z"
}
```

---

## Backward Compatibility Strategy

### Legacy Parameter Support

**Old Style** (Still Supported):
```bash
# Single format
curl -F "file=@doc.md" -F "format=docx" /api/convert
→ Returns binary file directly

# Both formats
curl -F "file=@doc.md" -F "format=both" /api/convert
→ Returns JSON with docx and pdf URLs
```

**New Style** (Preferred):
```bash
# Single format
curl -F "file=@doc.md" -F "formats=docx" /api/convert
→ Returns JSON with docx URL

# Multiple formats
curl -F "file=@doc.md" -F "formats=docx" -F "formats=pdf" /api/convert
→ Returns JSON with docx and pdf URLs
```

### Migration Path for Clients

**Phase 1** (Current): Both styles supported

**Phase 2** (6 months): Add deprecation warning for `format` parameter

**Phase 3** (12 months): Remove `format` parameter support (breaking change)

---

## Error Handling Standards

### Error Response Format

All error responses follow this structure:

```json
{
  "error": "Human-readable error message",
  "code": "MACHINE_READABLE_CODE",
  "status": 400,
  "details": {},  // Optional additional context
  "timestamp": "2025-11-01T12:34:56Z"
}
```

### Error Codes

| Code | Status | Description |
|------|--------|-------------|
| `NO_FORMAT_SELECTED` | 400 | No output formats specified |
| `INVALID_FORMAT` | 400 | Invalid format in request |
| `AUTH_REQUIRED` | 401 | Google Docs requires authentication |
| `INVALID_FILE_TYPE` | 415 | File extension not .md or .markdown |
| `INVALID_ENCODING` | 422 | File not UTF-8 encoded |
| `INVALID_CONTENT` | 422 | Markdown content validation failed |
| `RATE_LIMIT_EXCEEDED` | 429 | Google API rate limit exceeded |
| `CONVERSION_ERROR` | 500 | General conversion failure |
| `INTERNAL_ERROR` | 500 | Unexpected server error |

---

## API Versioning (Future Consideration)

### Current Approach

No API versioning in initial implementation. All endpoints at `/api/` root.

### Future Versioning Strategy

If breaking changes needed:

```
/api/v1/convert  # Legacy (current)
/api/v2/convert  # Future version with breaking changes
```

**Recommendation**: Avoid versioning by maintaining backward compatibility via parameter fallback.

---

## Testing Checklist

### Unit Tests

- [ ] Test multi-format parameter parsing
- [ ] Test legacy parameter fallback
- [ ] Test format validation
- [ ] Test auth requirement check
- [ ] Test error response formatting

### Integration Tests

- [ ] Test DOCX-only conversion
- [ ] Test PDF-only conversion
- [ ] Test DOCX + PDF conversion
- [ ] Test DOCX + PDF + Google Docs (authenticated)
- [ ] Test Google Docs without auth (should return 401)
- [ ] Test legacy `format=docx` (should return file)
- [ ] Test legacy `format=both` (should return JSON)
- [ ] Test invalid format
- [ ] Test no format specified
- [ ] Test rate limit handling

### API Contract Tests

- [ ] Response structure matches specification
- [ ] Error responses include all required fields
- [ ] Auth URLs are absolute URLs
- [ ] Timestamps are ISO 8601 formatted
- [ ] File sizes are integers
- [ ] Mimetypes are correct

---

**API Endpoint Design Status**: COMPLETE
**Ready for Implementation**: YES
**Next Document**: Frontend UI Architecture
