# Document Converter

A privacy-focused, open-source web application that converts Markdown and HTML files to professionally formatted Word (DOCX), PDF, and Google Docs documents.

## Features

- 📄 **Markdown to Word/PDF/Google Docs**: Convert markdown to multiple formats
- 🌐 **HTML to Word/PDF/Google Docs**: Convert HTML files with preserved formatting
- 📝 **YAML Front Matter**: Parse and display document metadata
- 🎨 **Rich Formatting**: Support for headings, lists, code blocks, tables, and more
- 🔐 **Zero-Knowledge Encryption**: Files encrypted at rest with session-based keys
- 🔒 **Privacy-First**: Files automatically deleted within 1 hour, we can't read them
- ☁️ **Google Docs Integration**: OAuth2-based conversion to Google Docs
- ⚡ **Fast**: Efficient conversion using Pandoc and Playwright
- 🐳 **Containerized**: Docker support for easy deployment
- ☁️ **Railway Ready**: One-click deployment to Railway
- 🌍 **Open Source**: Fully transparent, auditable code

## Supported Formats

### Input Formats
- **Markdown**: `.md`, `.markdown`, `.txt`
- **HTML**: `.html`, `.htm`

### Output Formats
- **Microsoft Word**: `.docx` (with page numbers and formatting)
- **PDF**: High-quality PDF with automatic page numbers
- **Google Docs**: Direct upload to user's Google Drive (requires OAuth)

### Format Features
- **YAML Front Matter**: Parsed and displayed in all formats
- **Syntax Highlighting**: Code blocks with syntax highlighting
- **Tables**: Full table support with borders and styling
- **Images**: Embedded images (not yet supported for Google Docs)
- **Links**: Clickable hyperlinks in all formats
- **Lists**: Numbered and bulleted lists
- **Formatting**: Bold, italic, strikethrough, inline code

## Technology Stack

### Backend
- **Python 3.12+**: Modern Python with type hints
- **Flask 3.0**: Lightweight web framework
- **Gunicorn**: Production WSGI server
- **Pypandoc**: Markdown to Word conversion
- **Playwright**: HTML to PDF rendering
- **BeautifulSoup4**: HTML parsing and sanitization
- **Python-frontmatter**: YAML parsing
- **Cryptography**: Fernet encryption for files at rest
- **Google APIs**: OAuth2 and Docs API integration

### Frontend
- **HTML5**: Semantic markup
- **Tailwind CSS**: Utility-first styling
- **Vanilla JavaScript**: No framework dependencies

### Deployment
- **Docker**: Containerized deployment
- **Railway**: Cloud hosting platform

## Quick Start

### Prerequisites

- Python 3.12 or higher
- Pandoc (installed via system package manager or pypandoc-binary)
- pip (Python package manager)
- (Optional) Google Cloud project for Google Docs conversion

### Local Development

```bash
# 1. Clone the repository
git clone https://github.com/ProfSynapse/doc-converter.git
cd doc-converter

# 2. Create virtual environment
python -m venv venv

# Activate on Windows
venv\Scripts\activate

# Activate on macOS/Linux
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Install Playwright browsers (for PDF generation)
playwright install chromium

# 5. Create necessary directories
mkdir -p tmp/converted

# 6. (Optional) Configure Google OAuth for Google Docs
# Create .env file with:
# GOOGLE_OAUTH_CLIENT_ID=your_client_id
# GOOGLE_OAUTH_CLIENT_SECRET=your_client_secret
# SECRET_KEY=your_random_secret_key

# 7. Run the application
python wsgi.py

# 8. Open browser
open http://localhost:8080
```

### Docker

```bash
# Build image
docker build -t doc-converter:latest .

# Run container (basic)
docker run -p 8080:8080 doc-converter:latest

# Run with Google OAuth (pass environment variables)
docker run -p 8080:8080 \
  -e GOOGLE_OAUTH_CLIENT_ID=your_client_id \
  -e GOOGLE_OAUTH_CLIENT_SECRET=your_client_secret \
  -e SECRET_KEY=your_secret_key \
  doc-converter:latest

# Access application
open http://localhost:8080
```

## Deployment

### Deploy to Railway (Recommended)

Railway provides easy deployment with automatic HTTPS and environment management.

#### Option 1: One-Click Deploy

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/your-template-id)

#### Option 2: Manual Deploy via CLI

```bash
# 1. Install Railway CLI
npm install -g @railway/cli

# 2. Login to Railway
railway login

# 3. Initialize project
railway init

# 4. Add environment variables (optional, for Google Docs)
railway variables set GOOGLE_OAUTH_CLIENT_ID=your_client_id
railway variables set GOOGLE_OAUTH_CLIENT_SECRET=your_client_secret
railway variables set SECRET_KEY=$(openssl rand -hex 32)

# 5. Deploy
railway up

# 6. View deployment
railway open
```

#### Option 3: Deploy via GitHub

1. Fork this repository
2. Create a new project on [Railway](https://railway.app)
3. Connect your GitHub repository
4. Add environment variables (if using Google Docs):
   - `GOOGLE_OAUTH_CLIENT_ID`
   - `GOOGLE_OAUTH_CLIENT_SECRET` (seal this variable)
   - `SECRET_KEY` (seal this variable)
5. Railway will automatically deploy on push

### Deploy to Other Platforms

#### Heroku

```bash
# Login to Heroku
heroku login

# Create app
heroku create your-app-name

# Set buildpacks
heroku buildpacks:add --index 1 https://github.com/heroku/heroku-buildpack-apt
heroku buildpacks:add --index 2 heroku/python

# Add Playwright buildpack for PDF generation
heroku buildpacks:add --index 3 https://github.com/mxschmitt/heroku-playwright-buildpack

# Set environment variables
heroku config:set SECRET_KEY=$(openssl rand -hex 32)
heroku config:set GOOGLE_OAUTH_CLIENT_ID=your_client_id
heroku config:set GOOGLE_OAUTH_CLIENT_SECRET=your_client_secret

# Deploy
git push heroku main

# Open app
heroku open
```

#### DigitalOcean App Platform

1. Create a new app from GitHub
2. Set environment variables in the app settings
3. Deploy automatically on push

#### Self-Hosted (VPS)

```bash
# On your server (Ubuntu/Debian)

# 1. Install system dependencies
sudo apt-get update
sudo apt-get install -y python3.12 python3-pip pandoc nginx

# 2. Clone repository
git clone https://github.com/ProfSynapse/doc-converter.git
cd doc-converter

# 3. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt
playwright install chromium
playwright install-deps

# 5. Create systemd service
sudo nano /etc/systemd/system/doc-converter.service

# Add:
[Unit]
Description=Document Converter
After=network.target

[Service]
User=www-data
WorkingDirectory=/path/to/doc-converter
Environment="PATH=/path/to/doc-converter/venv/bin"
ExecStart=/path/to/doc-converter/venv/bin/gunicorn -w 2 -b 0.0.0.0:8080 wsgi:app

[Install]
WantedBy=multi-user.target

# 6. Start service
sudo systemctl enable doc-converter
sudo systemctl start doc-converter

# 7. Configure nginx reverse proxy
sudo nano /etc/nginx/sites-available/doc-converter

# Add:
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# 8. Enable site and restart nginx
sudo ln -s /etc/nginx/sites-available/doc-converter /etc/nginx/sites-enabled/
sudo systemctl restart nginx

# 9. Get SSL certificate (optional but recommended)
sudo apt-get install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

## Google OAuth Setup (Optional)

To enable Google Docs conversion, you need to set up OAuth2:

### 1. Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project or select existing one
3. Enable APIs:
   - Google Docs API
   - Google Drive API

### 2. Create OAuth Credentials

1. Go to **APIs & Services > Credentials**
2. Click **Create Credentials > OAuth client ID**
3. Configure OAuth consent screen (if not done):
   - User Type: External
   - Add app name, support email
   - Add authorized domains
4. Create OAuth Client:
   - Application type: Web application
   - Add authorized redirect URIs:
     - Local: `http://localhost:8080/login/google/authorized`
     - Production: `https://your-domain.com/login/google/authorized`
5. Download JSON or copy Client ID and Client Secret

### 3. Set Environment Variables

**Local (.env file):**
```bash
GOOGLE_OAUTH_CLIENT_ID=your_client_id_here.apps.googleusercontent.com
GOOGLE_OAUTH_CLIENT_SECRET=your_client_secret_here
SECRET_KEY=your_random_secret_key_here
```

**Railway/Production:**
```bash
railway variables set GOOGLE_OAUTH_CLIENT_ID=your_client_id
railway variables set GOOGLE_OAUTH_CLIENT_SECRET=your_client_secret
railway variables set SECRET_KEY=$(openssl rand -hex 32)
```

**Generate Secret Key:**
```bash
# Linux/macOS
openssl rand -hex 32

# Python
python -c "import secrets; print(secrets.token_hex(32))"
```

### 4. Add Test Users (Development)

While your OAuth app is in testing mode:
1. Go to **OAuth consent screen**
2. Add test users (email addresses)
3. Only these users can authenticate

### 5. Publish App (Production)

For public access:
1. Complete OAuth consent screen information
2. Submit for Google verification
3. Wait for approval (1-3 weeks)

## Usage

### Web Interface

1. Open the application in your browser
2. (Optional) Sign in with Google for Google Docs conversion
3. Click "Choose File" or drag-and-drop a file (.md, .markdown, .txt, .html, .htm)
4. Select output format(s):
   - Word (DOCX)
   - PDF
   - Google Docs (requires sign-in)
5. Click "Convert"
6. Download your files or open in Google Docs

### API Endpoints

#### Convert Files

```bash
# Convert to multiple formats (new API)
curl -X POST http://localhost:8080/api/convert \
  -F "file=@document.md" \
  -F "formats=docx" \
  -F "formats=pdf"

# Convert HTML to PDF
curl -X POST http://localhost:8080/api/convert \
  -F "file=@document.html" \
  -F "formats=pdf"

# Convert to Google Docs (requires authentication)
# First: Sign in at http://localhost:8080/login/google
# Then use session cookie:
curl -X POST http://localhost:8080/api/convert \
  -F "file=@document.md" \
  -F "formats=gdocs" \
  -H "Cookie: session=your_session_cookie"

# Legacy API (single format, direct download)
curl -X POST http://localhost:8080/api/convert \
  -F "file=@document.md" \
  -F "format=docx" \
  --output document.docx
```

#### Download Converted File

```bash
curl http://localhost:8080/api/download/{job_id}/docx \
  --output document.docx
```

#### Health Check

```bash
curl http://localhost:8080/health
```

## Markdown Format

### Basic Markdown

```markdown
---
title: My Document
author: John Doe
date: 2025-10-31
tags: [markdown, converter, documentation]
---

# Introduction

This is a **markdown** document with *various* formatting.

## Features

- Bullet points
- **Bold text**
- *Italic text*
- `Inline code`

## Code Blocks

\```python
def hello_world():
    print("Hello, World!")
\```

## Tables

| Column 1 | Column 2 |
|----------|----------|
| Data 1   | Data 2   |

## Links

[OpenAI](https://openai.com)
```

### Front Matter

YAML front matter is optional but recommended for document metadata:

```yaml
---
title: Document Title
author: Author Name
date: 2025-10-31
version: 1.0
tags: [tag1, tag2, tag3]
---
```

## Configuration

### Environment Variables

| Variable | Default | Description | Required |
|----------|---------|-------------|----------|
| `FLASK_ENV` | `production` | Environment (development/production) | No |
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG/INFO/WARNING/ERROR) | No |
| `MAX_FILE_SIZE` | `10485760` | Max upload size in bytes (10MB) | No |
| `PORT` | `8080` | HTTP server port | No |
| `SECRET_KEY` | Auto-generated | Flask secret key for sessions | **Yes (production)** |
| `GOOGLE_OAUTH_CLIENT_ID` | None | Google OAuth client ID | For Google Docs |
| `GOOGLE_OAUTH_CLIENT_SECRET` | None | Google OAuth client secret (**seal in prod**) | For Google Docs |
| `OAUTHLIB_INSECURE_TRANSPORT` | `false` | Allow HTTP OAuth (dev only) | No |
| `CONVERTED_FOLDER` | `/tmp/converted` | Directory for temporary files | No |

### File Limits

- **Maximum file size**: 10 MB
- **Allowed extensions**: `.md`, `.markdown`, `.txt`, `.html`, `.htm`
- **File retention**: 1 hour (automatic cleanup)
- **Encryption**: Files encrypted at rest with session-based keys

## Project Structure

```
md-converter/
├── app/
│   ├── __init__.py              # Flask app factory
│   ├── config.py                # Configuration
│   ├── api/                     # API endpoints
│   ├── converters/              # Conversion engine
│   └── utils/                   # Utilities
├── static/
│   └── index.html               # Frontend
├── wsgi.py                      # WSGI entry point
├── requirements.txt             # Dependencies
├── Dockerfile                   # Container config
└── railway.toml                 # Railway config
```

## Security & Privacy

### Zero-Knowledge Encryption

- **Fernet encryption (AES-128)**: All converted files encrypted at rest
- **Session-based keys**: Encryption keys stored only in user's browser session
- **Zero-knowledge**: Server cannot decrypt files without user's active session
- **Automatic key destruction**: Keys deleted when session expires

### File Handling

- **1-hour retention**: Files automatically deleted within 1 hour
- **Background cleanup**: Runs every 5 minutes
- **Secure deletion**: Files overwritten with random data before removal
- **UUID isolation**: Each job in isolated directory with random UUID

### Security Measures

- **Input validation**: File type, size, encoding, and content validation
- **Filename sanitization**: Prevents path traversal attacks
- **HTML sanitization**: BeautifulSoup4 for safe HTML processing
- **Security headers**: CSP, XSS protection, frame options, HSTS
- **Non-root execution**: Container runs as non-privileged user
- **Resource limits**: Request timeouts and worker limits
- **OAuth security**: Session-only token storage, no database persistence

### Privacy

- **No file analysis**: Files never analyzed, indexed, or used for training
- **No permanent storage**: All files deleted within 1 hour
- **Open source**: Full code transparency and auditability
- **Privacy policy**: Clear documentation of data handling at `/privacy`

## API Documentation

### POST /api/convert

Convert markdown file to document format(s).

**Request:**
- Method: `POST`
- Content-Type: `multipart/form-data`
- Parameters:
  - `file`: Markdown file (required)
  - `format`: Output format - `docx`, `pdf`, or `both` (default: `both`)

**Response (format=both):**
```json
{
  "status": "success",
  "job_id": "uuid",
  "filename": "document",
  "formats": {
    "docx": {
      "download_url": "/api/download/{job_id}/docx",
      "filename": "document.docx",
      "size": 45678,
      "mimetype": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    },
    "pdf": {
      "download_url": "/api/download/{job_id}/pdf",
      "filename": "document.pdf",
      "size": 123456,
      "mimetype": "application/pdf"
    }
  },
  "processing_time": 2.34,
  "timestamp": "2025-10-31T10:30:00Z"
}
```

**Response (format=docx or pdf):**
- Binary file download

**Error Response:**
```json
{
  "error": "Error message",
  "code": "ERROR_CODE",
  "status": 400,
  "timestamp": "2025-10-31T10:30:00Z"
}
```

### GET /api/download/<job_id>/<format>

Download converted file.

**Request:**
- Method: `GET`
- Parameters:
  - `job_id`: UUID from conversion response
  - `format`: `docx` or `pdf`

**Response:**
- Binary file download

### GET /health

Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "service": "md-converter",
  "version": "1.0.0",
  "dependencies": {
    "pandoc": "available",
    "weasyprint": "62.3"
  },
  "timestamp": "2025-10-31T10:30:00Z"
}
```

## Development

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-cov

# Run all tests
pytest

# Run with coverage
pytest --cov=app tests/

# Run specific test file
pytest tests/test_converter.py
```

### Code Style

The project follows:
- **PEP 8**: Python style guide
- **Type hints**: For better code clarity
- **Docstrings**: Google-style documentation
- **Logging**: Comprehensive logging at all levels

### Adding New Features

1. Review architecture documentation in `docs/architecture/`
2. Implement feature in appropriate module
3. Add tests in `tests/`
4. Update documentation
5. Submit pull request

## Troubleshooting

### YAML Front Matter Parsing Errors

The converter uses Python's `frontmatter` library (lenient parser) instead of Pandoc's strict YAML parser. This means:

**✅ All these formats work:**
```yaml
# Multi-line lists
tags:
  - tag-one
  - tag-two

# Inline arrays  
tags: [tag-one, tag-two]

# Values with hyphens
project: my-project-name

# Unquoted strings
title: My Document Title
```

**How it works:**
1. Python parses your YAML front matter (accepts any valid YAML)
2. Metadata is formatted as markdown (not passed to Pandoc as YAML)
3. Clean markdown content goes to Pandoc (no YAML parsing issues)

**Tips for best compatibility:**
- Keep YAML front matter between `---` markers
- Use valid YAML syntax (any format)
- Special characters are handled automatically

### Pandoc not found

```bash
# Ubuntu/Debian
sudo apt-get install pandoc

# macOS
brew install pandoc

# Or use pypandoc-binary (already in requirements.txt)
pip install pypandoc-binary
```

### WeasyPrint installation fails

```bash
# Ubuntu/Debian
sudo apt-get install libpango-1.0-0 libpangoft2-1.0-0 libgdk-pixbuf2.0-0

# macOS
brew install pango gdk-pixbuf
```

### Port already in use

```bash
# Change port
export PORT=8081
python wsgi.py
```

## Performance

- **Conversion speed**: ~2-5 seconds per file
- **Concurrent requests**: Supports multiple simultaneous conversions
- **File size limit**: 10 MB (configurable)
- **Throughput**: 10-20 conversions/minute on standard hardware

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [Pandoc](https://pandoc.org/) - Universal document converter
- [Playwright](https://playwright.dev/) - Browser automation for PDF rendering
- [Flask](https://flask.palletsprojects.com/) - Web framework
- [Tailwind CSS](https://tailwindcss.com/) - CSS framework
- [Cryptography](https://cryptography.io/) - Encryption library
- [Google APIs](https://developers.google.com/) - Google Docs and Drive integration
- [BeautifulSoup4](https://www.crummy.com/software/BeautifulSoup/) - HTML parsing

## Contributing

We welcome contributions! Here's how to help:

### Reporting Issues
- Check existing issues first
- Provide detailed reproduction steps
- Include error messages and logs
- Specify your environment (OS, Python version, etc.)

### Pull Requests
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests if applicable
5. Run tests: `pytest`
6. Commit with clear messages
7. Push to your fork
8. Open a Pull Request

### Development Guidelines
- Follow PEP 8 style guide
- Add type hints
- Write docstrings (Google style)
- Add tests for new features
- Update documentation

## Support

For issues, questions, or contributions:
- **Issues**: [GitHub Issues](https://github.com/ProfSynapse/doc-converter/issues)
- **Discussions**: [GitHub Discussions](https://github.com/ProfSynapse/doc-converter/discussions)
- **Documentation**: `docs/` directory
- **API Spec**: `docs/architecture/API_SPECIFICATION.md`
- **Website**: [synapticlabs.ai](https://www.synapticlabs.ai)

---

**Version:** 2.0.0
**Status:** Production Ready
**License:** MIT
**Repository:** [github.com/ProfSynapse/doc-converter](https://github.com/ProfSynapse/doc-converter)
**Last Updated:** January 2025
