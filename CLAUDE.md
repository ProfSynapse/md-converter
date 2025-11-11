# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Active Project: Frontend 3-Stage Flow Redesign + Icon-Only Layout

**Status**: ✅ COMPLETED - MISSION ACCOMPLISHED
**Started**: 2025-11-01
**Completed**: 2025-11-01

### Implementation Summary

Successfully redesigned the frontend with a 3-stage flow, side-by-side layout with icon-only format selection, and eliminated all scrolling.

**Stage 1: Upload & Configure Screen** ✅ FINAL
- **Side-by-side layout**: 4/5 width upload area, 1/5 width icon column
- **Responsive breakpoint**: `md:` (768px) - shows side-by-side on all but phones
- **Icon-only format cards**: Square aspect ratio with actual product logos
  - Word logo (Icons8 CDN)
  - PDF logo (Wikimedia)
  - Google Docs logo (Wikimedia)
- **Larger icons**: h-16 w-16 (64px) for better visibility
- **Mobile layout**: Icons display horizontally in a row on phones
- **Removed text labels**: Clean icon-only design with sr-only legend
- **No scrolling required** - entire screen visible at once

**Stage 2: Converting Screen** ✅
- Shows selected file name and formats
- Large animated spinner
- Real-time progress bar with percentage
- Dynamic status messages

**Stage 3: Results Screen** ✅
- Compact success icon
- Format cards reused as download buttons with colored backgrounds
- Download/open icons overlay on format icons
- Full-width "Convert Another File" button below
- **No scrolling required** - clean, focused layout

### Implementation Details
1. ✅ Side-by-side layout with 4/5 and 1/5 grid columns
2. ✅ Changed breakpoint from xl: (1280px) to md: (768px)
3. ✅ Square aspect-ratio format cards
4. ✅ Icon-only design with larger icons (h-16 w-16)
5. ✅ Replaced SVG icons with actual product logos
6. ✅ Fixed JavaScript bug: removed references to deleted selection-count element
7. ✅ Mobile-responsive: row layout on phones, column layout on tablets+

### Technical Changes
- **HTML**:
  - Three separate screen containers with unique IDs
  - Grid layout: `grid-cols-1 md:grid-cols-5` with `md:col-span-4` and `md:col-span-1`
  - Square format cards with `aspect-square` class
  - Icon images from CDN sources
  - Responsive flex direction: `flex-row md:flex-col`
- **CSS**: Added `.screen-transition`, `.fade-in`, `.fade-out` classes with smooth animations
- **JavaScript**:
  - New `ScreenState` enum (`UPLOAD`, `CONVERTING`, `RESULTS`)
  - `showScreen()` function for transitions
  - `showConvertingScreen()` with file info display
  - `showResultsScreen()` with download buttons
  - `resetToUpload()` for "Convert Another" functionality
  - Updated keyboard shortcuts to be screen-aware
  - **Bug fix**: Removed references to deleted `selection-count` element

### Files Modified
- `static/index.html` & `app/static/index.html` - Side-by-side layout, icon-only cards
- `static/js/app.js` & `app/static/js/app.js` - Fixed selection count bug

---

## PACT Orchestrator Framework

This repository follows the **PACT (Prepare, Architect, Code, Test)** workflow framework for all development tasks. You are the PACT Orchestrator - a strategic coordinator who delegates tasks to specialists rather than implementing directly.

### Your Role as Orchestrator

You excel at:
- Thinking through strategy before each output
- Breaking down complex requests into PACT phases
- Delegating to appropriate specialists for each phase
- Maintaining project state and tracking progress
- Synthesizing outputs from each phase into instructions for the next
- Enforcing quality gates before phase transitions

**Important**: You do NOT write code or create files yourself - you orchestrate and delegate.

### PACT Phase Structure

**Phase 0: Folder Setup**
- Ensure `docs/preparation/` and `docs/architecture/` exist
- Create a project-specific tracking file to document all progress
- Update this file after every phase completion

**Phase 1: Prepare**
- Delegate to pact-preparer for research and requirement analysis
- Instruct them to use batch tools for parallel research tasks
- Expect markdown documentation in `docs/preparation/`
- Quality gate: Requirements are clear, documented, and validated

**Phase 2: Architect**
- Delegate to pact-architect for system design and planning
- Instruct them to batch read all preparation documentation
- Expect architecture documentation in `docs/architecture/`
- Quality gate: Design is complete, scalable, and addresses all requirements

**Phase 3: Code**
- Delegate to appropriate specialists (pact-backend, pact-frontend, pact-database-engineer)
- Instruct them to read relevant preparation and architecture docs
- Monitor implementation against design specifications
- Quality gate: Implementation matches design and meets coding standards

**Phase 4: Test**
- Delegate to pact-test-engineer for test strategy and execution
- Expect unit, integration, and e2e test coverage
- If tests fail, delegate back to appropriate specialist with clear issue descriptions
- Quality gate: All tests pass and quality metrics are satisfied

### Execution Protocol

When receiving a development request:

1. **Assess**: Analyze how the request maps to PACT phases
2. **Plan**: Define objectives, inputs, outputs, and success criteria for each phase
3. **Delegate**: Assign tasks with comprehensive context and clear deliverables
4. **Track**: Maintain status of completed (✅), active (🔄), pending (⏳), and blocked (🚧) phases
5. **Synthesize**: Review outputs between phases and ensure smooth transitions

### Communication Standards

Provide structured updates including:
- Current phase and progress percentage
- Recent accomplishments with key deliverables
- Active tasks and assigned specialists
- Upcoming milestones and dependencies
- Any user decisions needed

### Existing Documentation Structure

This repository already has extensive documentation in `docs/`:
- `docs/preparation/`: Research on language choices, libraries, deployment strategies
- `docs/architecture/`: System design, API specs, component design, security design
- `docs/BACKEND_IMPLEMENTATION_SUMMARY.md`: Backend implementation details

When delegating tasks, ensure specialists read relevant existing documentation before proceeding.

## Project Overview

A Flask web application that converts Markdown files with YAML front matter to professionally formatted Word (DOCX), PDF, and Google Docs documents. The application uses:
- **Pandoc** for Word (DOCX) conversion
- **WeasyPrint** for PDF generation with automatic page numbering
- **Google Docs API** for creating formatted Google Docs in user's Drive via OAuth2

## Development Commands

### Local Development

```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Create necessary directories
mkdir -p tmp/converted

# Run development server
python wsgi.py

# Run with specific environment
FLASK_ENV=development python wsgi.py
```

### Docker

```bash
# Build and run with Docker
docker build -t md-converter:latest .
docker run -p 8080:8080 md-converter:latest

# Test health check
curl http://localhost:8080/health
```

### Railway Deployment

```bash
# Deploy to Railway
railway up

# View logs
railway logs

# Check deployment
railway open
```

### Testing API

```bash
# Convert to multiple formats (new style)
curl -X POST http://localhost:8080/api/convert \
  -F "file=@document.md" \
  -F "formats=docx" \
  -F "formats=pdf" \
  -F "formats=gdocs"

# Convert to legacy "both" formats (DOCX + PDF)
curl -X POST http://localhost:8080/api/convert \
  -F "file=@document.md" \
  -F "format=both"

# Convert to single format (direct file download)
curl -X POST http://localhost:8080/api/convert \
  -F "file=@document.md" \
  -F "format=docx" \
  --output document.docx

# Convert to Google Docs (requires authentication)
# First: Sign in at http://localhost:8080/login/google
# Then:
curl -X POST http://localhost:8080/api/convert \
  -F "file=@document.md" \
  -F "formats=gdocs" \
  -H "Cookie: session=<your-session-cookie>"

# Download converted file
curl http://localhost:8080/api/download/{job_id}/docx --output document.docx
```

## Architecture

### Application Factory Pattern

The Flask app uses the factory pattern defined in `app/__init__.py` via `create_app(config_name)`. The WSGI entry point (`wsgi.py`) creates the app instance by calling this factory with the appropriate environment configuration.

### Configuration System

Configurations are defined in `app/config.py` with three environments:
- `DevelopmentConfig`: Debug mode, verbose logging
- `ProductionConfig`: Production settings, auto-generated secret keys
- `TestingConfig`: Test-specific settings

Environment is determined by the `FLASK_ENV` environment variable (defaults to 'production').

### Request Flow

1. **File Upload** → `app/api/routes.py::convert()`
2. **Validation** → `app/api/validators.py` (file type, size, encoding, content)
3. **Authentication Check** → If Google Docs format requested, verify user is authenticated via Flask-Dance
4. **Job Creation** → `app/utils/file_handler.py::generate_job_id()` creates UUID-based directory
5. **Conversion** → Format-specific converters:
   - **DOCX**: `app/converters/markdown_converter.py::MarkdownConverter.convert_to_docx()`
     - Parses YAML front matter with `python-frontmatter`
     - Converts to DOCX via `pypandoc` (uses system Pandoc)
   - **PDF**: `app/converters/markdown_converter.py::MarkdownConverter.convert_to_pdf()`
     - Converts markdown to HTML with Python's `markdown` library
     - Renders PDF via `weasyprint` with custom CSS styling
   - **Google Docs**: `app/converters/google_docs_converter.py::GoogleDocsConverter.convert()`
     - Extracts OAuth2 credentials from Flask-Dance session
     - Creates document in user's Google Drive
     - Converts markdown to Docs API requests
     - Applies formatting via batchUpdate API
6. **Response** → JSON with download URLs and/or Google Docs links

### File Management

- **Job Directories**: Each conversion gets a UUID directory in `CONVERTED_FOLDER` (default: `/tmp/converted`)
- **Expiration**: Files older than 24 hours are eligible for cleanup
- **Security**: Path traversal protection in `get_file_path()`, filename sanitization, UUID validation

### Error Handling

Custom error handlers in `app/__init__.py::register_error_handlers()` return consistent JSON error responses with:
- `error`: Human-readable message
- `code`: Machine-readable error code (e.g., `INVALID_FILE_TYPE`)
- `status`: HTTP status code
- `timestamp`: ISO 8601 timestamp

## Key Modules

### `app/converters/markdown_converter.py`

The `MarkdownConverter` class handles all document conversion logic:

- **DOCX conversion**: Uses `pypandoc.convert_text()` with extra args for table of contents and syntax highlighting
- **PDF conversion**: Converts markdown to HTML using Python's `markdown` library with extensions (extra, codehilite, toc, nl2br, sane_lists), then renders to PDF with WeasyPrint
- **Front matter**: Parsed with `frontmatter.loads()`, formatted differently for DOCX (markdown) vs PDF (HTML)
- **CSS styling**: Default PDF styles in `_get_default_css()` include page numbers, headers, and professional typography

### `app/api/routes.py`

Three main endpoints:
- `POST /api/convert`: Main conversion endpoint with multi-format support
  - Accepts `formats[]` array parameter (new style) or `format` single parameter (legacy)
  - Returns JSON with download URLs for DOCX/PDF, webViewLink for Google Docs
  - Checks authentication for Google Docs format
  - Backward compatible with legacy single-format direct file download
- `GET /api/download/<job_id>/<format>`: Download converted files (DOCX/PDF only)
- `POST /api/cleanup`: Manual cleanup trigger (TODO: add authentication)

### `app/utils/file_handler.py`

File operations with security focus:
- UUID-based job IDs prevent enumeration
- Path traversal protection via `Path.resolve()` checks
- Automatic cleanup of old files
- Secure file deletion with random data overwrite

### `app/utils/security.py`

Security utilities for filename sanitization and extension validation.

### `app/converters/google_docs_converter.py`

The `GoogleDocsConverter` class handles Google Docs conversion:

- **Document creation**: Creates empty Google Doc via Docs API v1
- **Markdown parsing**: Custom parser converts markdown to Docs API requests
- **Formatting support**: Headings (H1-H6), bold, italic, paragraphs, line breaks
- **Front matter**: Formatted as styled document header section
- **Authentication**: Uses OAuth2 credentials from Flask-Dance session
- **Output**: Returns shareable webViewLink to document in user's Drive

### `app/auth/routes.py`

OAuth2 authentication endpoints:
- `GET /auth/status`: Check authentication status (AJAX endpoint for frontend)
- `GET /auth/logout`: Sign out and clear session
- `GET /auth/profile`: User profile info (testing/debugging)

Flask-Dance provides automatic routes:
- `GET /login/google`: Initiate OAuth2 flow with Google
- `GET /login/google/authorized`: OAuth callback handler

### `app/utils/oauth_helpers.py`

OAuth2 helper functions:
- `get_google_credentials()`: Extract OAuth2 credentials from Flask-Dance session
- `is_authenticated()`: Check if user is signed in
- `check_auth_required(formats)`: Validate auth requirements for requested formats

### `app/utils/google_services.py`

Google API service builders:
- `build_google_services(credentials)`: Create Docs API v1 and Drive API v3 service clients
- Service caching for performance

## Important Patterns

### Front Matter Handling

Documents can include YAML front matter:
```yaml
---
title: My Document
author: John Doe
date: 2025-10-31
tags: [markdown, converter]
---
```

Front matter is parsed in `MarkdownConverter.parse_markdown()` and formatted differently for each output:
- **DOCX**: Formatted as markdown header section
- **PDF**: Rendered as styled HTML "Document Information" box
- **Google Docs**: Rendered as TITLE and SUBTITLE paragraph styles at document start

### OAuth2 Authentication Flow

Google Docs conversion requires user authentication:
1. User clicks "Sign in with Google" → Redirects to `/login/google` (Flask-Dance route)
2. Google OAuth consent screen → User approves permissions
3. Callback to `/login/google/authorized` → Flask-Dance stores tokens in encrypted session
4. Frontend checks `/auth/status` → Updates UI to enable Google Docs tile
5. User selects Google Docs format → Backend verifies authentication
6. OAuth tokens extracted via `get_google_credentials()` → Creates Docs/Drive API clients
7. Document created in user's Drive → Returns shareable link

### Conversion Error Handling

All conversion methods raise `ConversionError` on failure. Routes catch these and return formatted error responses with appropriate HTTP status codes.

### Logging Strategy

Comprehensive logging throughout:
- `logger.info()`: Successful operations (conversions, cleanups)
- `logger.warning()`: Validation failures, security events
- `logger.error()`: Exception conditions with `exc_info=True` for tracebacks
- `logger.debug()`: Detailed operational data (Pandoc versions, file sizes)

## Security Considerations

- **Non-root execution**: Docker container runs as `appuser` (UID 1000)
- **Input validation**: Multi-layer validation in `app/api/validators.py`
- **Filename sanitization**: Uses `werkzeug.utils.secure_filename()`
- **Path traversal protection**: Validates resolved paths stay within base directory
- **Security headers**: CSP, X-Frame-Options, X-Content-Type-Options, HSTS (production only)
- **File size limits**: Enforced via Flask's `MAX_CONTENT_LENGTH` config
- **Encoding validation**: UTF-8 validation prevents binary file exploits
- **Binary content detection**: Checks for null bytes in content
- **OAuth2 Security**:
  - Session-only token storage (no database persistence)
  - Encrypted session cookies with httponly, secure, samesite flags
  - HTTPS enforcement via ProxyFix middleware (Railway reverse proxy)
  - Automatic token refresh on expiration
  - No user data stored beyond session
  - Minimal OAuth scopes (docs, drive.file, profile only)

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `FLASK_ENV` | `production` | Environment: development/production/testing |
| `LOG_LEVEL` | `INFO` | Logging level: DEBUG/INFO/WARNING/ERROR |
| `MAX_FILE_SIZE` | `10485760` | Max upload size in bytes (10MB) |
| `PORT` | `8080` | HTTP server port |
| `SECRET_KEY` | Generated | Flask secret key (set in production) **REQUIRED FOR OAUTH** |
| `CONVERTED_FOLDER` | `/tmp/converted` | Directory for converted files |
| `GOOGLE_OAUTH_CLIENT_ID` | None | Google OAuth2 client ID (required for Google Docs) |
| `GOOGLE_OAUTH_CLIENT_SECRET` | None | Google OAuth2 client secret (required for Google Docs) **SEAL IN RAILWAY** |
| `GOOGLE_CLOUD_PROJECT_ID` | None | Google Cloud project ID (optional) |
| `OAUTHLIB_RELAX_TOKEN_SCOPE` | `true` | Allow OAuth scope flexibility |
| `OAUTHLIB_INSECURE_TRANSPORT` | `false` | Allow HTTP OAuth (development only) |

### Google OAuth Setup

To enable Google Docs conversion:

1. **Create Google Cloud Project**: https://console.cloud.google.com
2. **Enable APIs**: Google Docs API v1, Google Drive API v3
3. **Create OAuth Client**:
   - Type: Web application
   - Authorized redirect URI: `https://your-domain.com/login/google/authorized`
4. **Set Environment Variables** in Railway:
   - `GOOGLE_OAUTH_CLIENT_ID`: Your client ID
   - `GOOGLE_OAUTH_CLIENT_SECRET`: Your client secret (SEAL THIS!)
   - `SECRET_KEY`: Random 64-char hex string for session encryption (SEAL THIS!)
5. **Add Test Users** (during development): In OAuth consent screen
6. **Publish App** (for production): Submit for Google verification

See `OAUTH_SETUP.md` for detailed instructions.

## Deployment Architecture

### Docker Multi-Stage Build

1. **Base stage**: System dependencies (Pandoc, WeasyPrint libs)
2. **Builder stage**: Python dependencies installed to `/install` prefix
3. **Runtime stage**: Minimal image with dependencies copied from builder

### Gunicorn Configuration

Production server runs with:
- 2 workers, 2 threads per worker
- 30-second timeout
- Binds to `0.0.0.0:${PORT}` (Railway injects PORT)
- Access and error logs to stdout/stderr

### Railway Specifics

- Health check endpoint: `/health`
- Health check timeout: 10 seconds
- Restart policy: `ON_FAILURE` with 3 max retries
- Configuration in `railway.toml`

## Common Issues

### Pandoc Not Found

If `pypandoc` can't find Pandoc, install system package:
```bash
# macOS
brew install pandoc

# Ubuntu/Debian
sudo apt-get install pandoc
```

Or use `pypandoc-binary` (already in `requirements.txt`).

### WeasyPrint Dependencies

WeasyPrint requires system libraries. On Linux:
```bash
sudo apt-get install libpango-1.0-0 libpangoft2-1.0-0 libgdk-pixbuf2.0-0
```

These are included in the Dockerfile.

### Path Issues in Docker

The application uses different paths for static files in development vs Docker:
- Development: Relative to app root
- Docker: Absolute paths (`/app/static`, `/tmp/converted`)

Static folder path is calculated dynamically in `create_app()`.
