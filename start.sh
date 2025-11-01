#!/bin/bash
# Startup script for Railway deployment
# This script starts Gunicorn with the PORT environment variable

set -e

# Use Railway's PORT or default to 8080
PORT=${PORT:-8080}

echo "Starting Gunicorn on port $PORT..."

exec gunicorn \
    --bind "0.0.0.0:$PORT" \
    --workers 2 \
    --threads 2 \
    --timeout 30 \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    wsgi:app
