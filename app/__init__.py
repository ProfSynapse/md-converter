"""
Flask Application Factory
Location: /mnt/c/Users/Joseph/Documents/Code/md-converter/app/__init__.py

This module creates and configures the Flask application instance.
It registers blueprints, error handlers, and applies middleware.

Used by: wsgi.py for production deployment
"""
from flask import Flask, jsonify, send_from_directory
from flask.logging import default_handler
import logging
import os
from datetime import datetime


def create_app(config_name='default'):
    """
    Create and configure Flask application.

    Args:
        config_name: Configuration to use (development, production, default)

    Returns:
        Configured Flask application instance
    """
    # Create Flask app with correct static folder
    # In production (Docker), static folder is at /app/static
    # In development, it's relative to the app root
    static_folder = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static')
    app = Flask(__name__, static_folder=static_folder)

    # Load configuration
    from app.config import config
    app.config.from_object(config[config_name])

    # Configure logging
    configure_logging(app)

    # Create necessary directories
    os.makedirs(app.config['CONVERTED_FOLDER'], exist_ok=True)

    # Register OAuth blueprint (Flask-Dance)
    if app.config.get('GOOGLE_OAUTH_CLIENT_ID') and app.config.get('GOOGLE_OAUTH_CLIENT_SECRET'):
        from flask_dance.contrib.google import make_google_blueprint

        google_bp = make_google_blueprint(
            client_id=app.config['GOOGLE_OAUTH_CLIENT_ID'],
            client_secret=app.config['GOOGLE_OAUTH_CLIENT_SECRET'],
            scope=[
                'https://www.googleapis.com/auth/documents',
                'https://www.googleapis.com/auth/drive.file',
                'openid',
                'email',
                'profile'
            ],
            redirect_to='index',  # Redirect to home after login
        )
        app.register_blueprint(google_bp, url_prefix='/auth/google')
        app.logger.info('Google OAuth blueprint registered')
    else:
        app.logger.warning('Google OAuth not configured - Google Docs conversion disabled')

    # Register auth blueprint (custom auth routes)
    from app.auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    # Register API blueprint
    from app.api import api_blueprint
    app.register_blueprint(api_blueprint, url_prefix='/api')

    # Register error handlers
    register_error_handlers(app)

    # Add security headers
    @app.after_request
    def add_security_headers(response):
        """Add security headers to all responses"""
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'

        if not app.debug:
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'

        # Content Security Policy
        csp = (
            "default-src 'self'; "
            "script-src 'self' https://cdn.tailwindcss.com 'unsafe-inline'; "
            "style-src 'self' https://cdn.tailwindcss.com https://fonts.googleapis.com 'unsafe-inline'; "
            "img-src 'self' data: https: https://picoshare-production-7223.up.railway.app; "
            "font-src 'self' data: https://fonts.gstatic.com; "
            "connect-src 'self';"
        )
        response.headers['Content-Security-Policy'] = csp
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'

        return response

    # Health check endpoint
    @app.route('/health')
    def health_check():
        """Health check endpoint for Railway monitoring with detailed diagnostics"""
        import traceback

        health_status = {
            'status': 'healthy',
            'service': 'md-converter',
            'version': '1.0.0',
            'dependencies': {},
            'diagnostics': {},
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }

        is_healthy = True

        # Check pypandoc/pandoc
        try:
            import pypandoc
            pandoc_version = pypandoc.get_pandoc_version()
            health_status['dependencies']['pandoc'] = pandoc_version
            app.logger.info(f'Pandoc version: {pandoc_version}')
        except Exception as e:
            error_detail = {
                'error': str(e),
                'type': type(e).__name__,
                'traceback': traceback.format_exc()
            }
            app.logger.error(f'Pandoc check failed: {error_detail}')
            health_status['dependencies']['pandoc'] = 'unavailable'
            health_status['diagnostics']['pandoc_error'] = error_detail
            is_healthy = False

        # Check weasyprint
        try:
            from weasyprint import __version__ as weasyprint_version
            health_status['dependencies']['weasyprint'] = weasyprint_version
            app.logger.info(f'WeasyPrint version: {weasyprint_version}')
        except Exception as e:
            error_detail = {
                'error': str(e),
                'type': type(e).__name__,
                'traceback': traceback.format_exc()
            }
            app.logger.error(f'WeasyPrint check failed: {error_detail}')
            health_status['dependencies']['weasyprint'] = 'unavailable'
            health_status['diagnostics']['weasyprint_error'] = error_detail
            is_healthy = False

        # Check filesystem permissions
        try:
            converted_folder = app.config.get('CONVERTED_FOLDER', '/tmp/converted')
            health_status['diagnostics']['converted_folder'] = str(converted_folder)
            health_status['diagnostics']['converted_folder_exists'] = os.path.exists(converted_folder)
            health_status['diagnostics']['converted_folder_writable'] = os.access(converted_folder, os.W_OK)

            static_folder = app.static_folder
            health_status['diagnostics']['static_folder'] = str(static_folder)
            health_status['diagnostics']['static_folder_exists'] = os.path.exists(static_folder) if static_folder else False
        except Exception as e:
            app.logger.error(f'Filesystem check failed: {e}')
            health_status['diagnostics']['filesystem_error'] = str(e)

        # For Railway, we'll be more lenient - return 200 even if some deps fail
        # This allows the service to start and we can debug from logs
        if not is_healthy:
            health_status['status'] = 'degraded'
            app.logger.error(f'Health check DEGRADED - Full status: {health_status}')
        else:
            app.logger.info('Health check PASSED - All dependencies available')

        return jsonify(health_status), 200

    # Serve static files
    @app.route('/')
    def index():
        """Serve the main application page"""
        return send_from_directory(app.static_folder, 'index.html')

    @app.route('/<path:path>')
    def static_files(path):
        """Serve other static files"""
        return send_from_directory(app.static_folder, path)

    app.logger.info(f'Flask application created with config: {config_name}')

    # Startup diagnostics
    with app.app_context():
        app.logger.info('=== Startup Diagnostics ===')
        app.logger.info(f'Python version: {os.sys.version}')
        app.logger.info(f'Working directory: {os.getcwd()}')
        app.logger.info(f'Static folder: {app.static_folder}')
        app.logger.info(f'Static folder exists: {os.path.exists(app.static_folder) if app.static_folder else False}')
        app.logger.info(f'Converted folder: {app.config.get("CONVERTED_FOLDER")}')
        app.logger.info(f'Converted folder exists: {os.path.exists(app.config.get("CONVERTED_FOLDER", ""))}')

        # Test dependencies
        try:
            import pypandoc
            version = pypandoc.get_pandoc_version()
            app.logger.info(f'✓ Pandoc available: version {version}')
        except Exception as e:
            app.logger.error(f'✗ Pandoc unavailable: {type(e).__name__}: {e}')

        try:
            from weasyprint import __version__
            app.logger.info(f'✓ WeasyPrint available: version {__version__}')
        except Exception as e:
            app.logger.error(f'✗ WeasyPrint unavailable: {type(e).__name__}: {e}')

        app.logger.info('=== End Startup Diagnostics ===')

    return app


def configure_logging(app):
    """
    Configure application logging.

    Args:
        app: Flask application instance
    """
    log_level = getattr(logging, app.config['LOG_LEVEL'].upper())

    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Set Flask logger level
    app.logger.setLevel(log_level)

    # Suppress noisy libraries
    logging.getLogger('werkzeug').setLevel(logging.WARNING)

    return app


def register_error_handlers(app):
    """
    Register custom error handlers.

    Args:
        app: Flask application instance
    """

    @app.errorhandler(400)
    def bad_request(error):
        """Handle bad request errors"""
        return jsonify({
            'error': 'Bad request',
            'code': 'BAD_REQUEST',
            'status': 400,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 400

    @app.errorhandler(404)
    def not_found(error):
        """Handle not found errors"""
        return jsonify({
            'error': 'Resource not found',
            'code': 'NOT_FOUND',
            'status': 404,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 404

    @app.errorhandler(413)
    def too_large(error):
        """Handle file too large errors"""
        max_size = app.config.get('MAX_FILE_SIZE', 10485760)
        return jsonify({
            'error': f'File size exceeds maximum limit of {max_size} bytes',
            'code': 'FILE_TOO_LARGE',
            'status': 413,
            'max_size': max_size,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 413

    @app.errorhandler(415)
    def unsupported_media_type(error):
        """Handle unsupported media type errors"""
        return jsonify({
            'error': 'Unsupported media type',
            'code': 'UNSUPPORTED_MEDIA_TYPE',
            'status': 415,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 415

    @app.errorhandler(500)
    def internal_error(error):
        """Handle internal server errors"""
        app.logger.error(f'Internal server error: {error}')
        return jsonify({
            'error': 'Internal server error',
            'code': 'INTERNAL_ERROR',
            'status': 500,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 500

    @app.errorhandler(503)
    def service_unavailable(error):
        """Handle service unavailable errors"""
        return jsonify({
            'error': 'Service temporarily unavailable',
            'code': 'SERVICE_UNAVAILABLE',
            'status': 503,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 503
