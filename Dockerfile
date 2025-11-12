# Multi-Stage Docker Build for Markdown & HTML Converter
# Location: /mnt/c/Users/Joseph/Documents/Code/md-converter/Dockerfile
#
# This Dockerfile creates an optimized production-ready image with:
# - Python 3.12 slim base
# - System dependencies for Pandoc, WeasyPrint, and Playwright/Chromium
# - Playwright browsers (Chromium) for HTML→PDF with full CSS support
# - Non-root user for security
# - Health check for Railway monitoring

# ============================================
# Stage 1: Base image with system dependencies
# ============================================
FROM python:3.12-slim as base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8080

# Install system dependencies for Pandoc, WeasyPrint, and Playwright
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Pandoc for Word generation
    pandoc \
    # WeasyPrint dependencies for PDF generation
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    shared-mime-info \
    # Playwright/Chromium dependencies
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    # Healthcheck dependencies
    curl \
    # Cleanup
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# ============================================
# Stage 2: Build dependencies
# ============================================
FROM base as builder

WORKDIR /build

# Copy requirements first for layer caching
COPY requirements.txt .

# Install Python dependencies to /install prefix
RUN pip install --prefix=/install --no-warn-script-location -r requirements.txt

# Install Playwright browsers (Chromium only)
# Set PYTHONPATH so Python can find playwright module installed to /install prefix
# This will install browsers to /ms-playwright
RUN PYTHONPATH=/install/lib/python3.12/site-packages:$PYTHONPATH \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright \
    python -m playwright install chromium --with-deps

# ============================================
# Stage 3: Runtime image
# ============================================
FROM base

# Set Playwright browser path (must match where we install them)
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

# Create non-root user for security
RUN useradd -m -u 1000 -s /bin/bash appuser && \
    mkdir -p /app /app/templates /tmp/converted && \
    chown -R appuser:appuser /app /tmp/converted

WORKDIR /app

# Copy Python packages from builder stage
COPY --from=builder /install /usr/local

# Copy Playwright browsers from builder stage
COPY --from=builder /ms-playwright /ms-playwright

# Copy application code
COPY --chown=appuser:appuser app/ /app/app/
COPY --chown=appuser:appuser static/ /app/static/
COPY --chown=appuser:appuser wsgi.py /app/
COPY --chown=appuser:appuser requirements.txt /app/

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8080

# Health check for Railway
# Note: Railway typically uses internal port, but we check on the PORT env var
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8080}/health || exit 1

# Start application with Gunicorn
# Using sh -c to ensure PORT variable expansion works
# ${PORT:-8080} provides fallback to 8080 if PORT is not set
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT:-8080} --workers 2 --threads 2 --timeout 30 --access-logfile - --error-logfile - --log-level info wsgi:app"]
