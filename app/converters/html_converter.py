"""
HTML Converter
Location: /mnt/c/Users/Joseph/Documents/Code/md-converter/app/converters/html_converter.py

This module provides the core conversion engine for transforming HTML files
to Word (DOCX), PDF, and Google Docs formats.

Dependencies:
    - pypandoc: HTML to Word conversion
    - weasyprint: PDF generation
    - bleach: HTML sanitization
    - beautifulsoup4: HTML parsing

Used by: app/api/routes.py for handling HTML conversion requests
"""
import pypandoc
import logging
from pathlib import Path
from typing import Optional
from weasyprint import HTML as WeasyHTML
from app.utils.security import sanitize_html, validate_html_content, count_html_images


logger = logging.getLogger(__name__)


class ConversionError(Exception):
    """Raised when document conversion fails"""
    pass


class HtmlConverter:
    """
    Converts HTML files to Word (DOCX), PDF, and Google Docs formats.

    This class handles:
    - Sanitizing HTML content (XSS prevention)
    - Converting HTML to Word (DOCX) via pypandoc
    - Converting HTML to PDF via weasyprint
    - Preparing HTML for Google Docs conversion

    Example:
        >>> converter = HtmlConverter()
        >>> converter.convert_to_docx(html_content, 'output.docx')
        'output.docx'
    """

    def __init__(self):
        """
        Initialize converter.

        Raises:
            RuntimeError: If Pandoc is not available
        """
        self._verify_pandoc()
        logger.info('HtmlConverter initialized')

    def _verify_pandoc(self) -> None:
        """
        Verify Pandoc is available in the system.

        Raises:
            RuntimeError: If Pandoc is not found
        """
        try:
            version = pypandoc.get_pandoc_version()
            logger.debug(f'Pandoc version {version} detected')
        except OSError as e:
            error_msg = (
                'Pandoc not found. '
                'Install with: apt-get install pandoc or pip install pypandoc-binary'
            )
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e

    def validate_and_sanitize(
        self,
        html_content: str,
        max_size: int = 10 * 1024 * 1024,
        max_images: int = 100
    ) -> str:
        """
        Validate and sanitize HTML content.

        Args:
            html_content: Raw HTML string
            max_size: Maximum allowed size in bytes
            max_images: Maximum allowed images per document

        Returns:
            Sanitized HTML string

        Raises:
            ConversionError: If validation fails
        """
        # Validate content
        validation_error = validate_html_content(html_content, max_size)
        if validation_error:
            raise ConversionError(
                f"{validation_error['error']} (code: {validation_error['code']})"
            )

        # Count images (DOS prevention)
        image_error = count_html_images(html_content, max_images)
        if image_error:
            raise ConversionError(
                f"{image_error['error']} (code: {image_error['code']})"
            )

        # Sanitize HTML (XSS prevention)
        sanitized = sanitize_html(html_content)
        if not sanitized:
            raise ConversionError('HTML sanitization resulted in empty content')

        logger.debug(f'HTML validated and sanitized: {len(html_content)} -> {len(sanitized)} bytes')
        return sanitized

    def convert_to_docx(
        self,
        html_content: str,
        output_path: str,
        sanitize: bool = True,
        base_url: Optional[str] = None
    ) -> str:
        """
        Convert HTML to Word document.

        Uses Pandoc which automatically fetches and embeds images from URLs.

        Args:
            html_content: HTML content string
            output_path: Path for output .docx file
            sanitize: Whether to sanitize HTML (default: True)
            base_url: Base URL for resolving relative image paths (optional)

        Returns:
            Path to generated document

        Raises:
            ConversionError: If conversion fails

        Example:
            >>> path = converter.convert_to_docx(
            ...     '<html><body><h1>Hello</h1></body></html>',
            ...     '/tmp/output.docx'
            ... )
        """
        logger.info(f'Converting HTML to DOCX: {output_path}')

        try:
            # Sanitize if requested
            if sanitize:
                html_content = self.validate_and_sanitize(html_content)

            # Prepare Pandoc arguments
            extra_args = [
                '--standalone',
                '--highlight-style=pygments',
            ]

            # Add base URL for resolving relative image paths
            if base_url:
                extra_args.append(f'--resource-path={base_url}')

            # Convert with pypandoc
            # Pandoc automatically fetches images from <img src="https://..."> URLs
            pypandoc.convert_text(
                html_content,
                'docx',
                format='html',
                outputfile=output_path,
                extra_args=extra_args
            )

            file_size = Path(output_path).stat().st_size
            logger.info(f'Successfully created DOCX: {output_path} ({file_size} bytes)')
            return output_path

        except Exception as e:
            error_msg = f'DOCX conversion failed: {str(e)}'
            logger.error(error_msg, exc_info=True)
            raise ConversionError(error_msg) from e

    def convert_to_pdf(
        self,
        html_content: str,
        output_path: str,
        sanitize: bool = True,
        base_url: Optional[str] = None,
        css_style: Optional[str] = None
    ) -> str:
        """
        Convert HTML to PDF with page numbers.

        Uses WeasyPrint which automatically fetches images from URLs.

        Args:
            html_content: HTML content string
            output_path: Path for output .pdf file
            sanitize: Whether to sanitize HTML (default: True)
            base_url: Base URL for resolving relative image paths (optional)
            css_style: Custom CSS for styling (uses default if None)

        Returns:
            Path to generated document

        Raises:
            ConversionError: If conversion fails

        Example:
            >>> path = converter.convert_to_pdf(
            ...     '<html><body><h1>Hello</h1></body></html>',
            ...     '/tmp/output.pdf'
            ... )
        """
        logger.info(f'Converting HTML to PDF: {output_path}')

        try:
            # Sanitize if requested
            if sanitize:
                html_content = self.validate_and_sanitize(html_content)

            # Wrap content if it's a fragment (not a complete HTML document)
            if not html_content.strip().startswith('<!DOCTYPE') and not html_content.strip().startswith('<html'):
                # Default CSS if none provided
                if css_style is None:
                    css_style = self._get_default_css()

                html_content = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="utf-8">
                    <title>Document</title>
                    <style>{css_style}</style>
                </head>
                <body>
                    {html_content}
                </body>
                </html>
                """

            # Generate PDF with WeasyPrint
            # WeasyPrint automatically fetches images from URLs
            WeasyHTML(
                string=html_content,
                base_url=base_url  # For resolving relative URLs
            ).write_pdf(output_path)

            file_size = Path(output_path).stat().st_size
            logger.info(f'Successfully created PDF: {output_path} ({file_size} bytes)')
            return output_path

        except Exception as e:
            error_msg = f'PDF conversion failed: {str(e)}'
            logger.error(error_msg, exc_info=True)
            raise ConversionError(error_msg) from e

    def _get_default_css(self) -> str:
        """
        Get default CSS styling for PDF generation.

        Returns:
            CSS string with page layout and styling
        """
        return """
        @page {
            size: A4;
            margin: 1in 0.75in;

            @bottom-center {
                content: "Page " counter(page) " of " counter(pages);
                font-size: 10pt;
                color: #666;
                font-family: 'Helvetica', sans-serif;
            }
        }

        @page :first {
            @bottom-center {
                content: "";
            }
        }

        body {
            font-family: 'Georgia', serif;
            font-size: 11pt;
            line-height: 1.6;
            color: #333;
        }

        h1, h2, h3, h4, h5, h6 {
            font-family: 'Helvetica', sans-serif;
            color: #000;
            page-break-after: avoid;
        }

        h1 {
            font-size: 24pt;
            margin-top: 0;
            border-bottom: 2px solid #333;
            padding-bottom: 10pt;
        }

        h2 {
            font-size: 18pt;
            margin-top: 20pt;
            border-bottom: 1px solid #999;
            padding-bottom: 5pt;
        }

        h3 {
            font-size: 14pt;
            margin-top: 15pt;
        }

        p {
            margin: 0.5em 0;
            text-align: justify;
        }

        code {
            background-color: #f4f4f4;
            padding: 2px 4px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
            font-size: 9pt;
            color: #c7254e;
        }

        pre {
            background-color: #f4f4f4;
            padding: 10pt;
            border-left: 3px solid #666;
            overflow-x: auto;
            page-break-inside: avoid;
            margin: 1em 0;
        }

        pre code {
            background-color: transparent;
            padding: 0;
            color: inherit;
        }

        blockquote {
            border-left: 4px solid #ddd;
            padding-left: 15pt;
            margin-left: 0;
            color: #666;
            font-style: italic;
            page-break-inside: avoid;
        }

        table {
            border-collapse: collapse;
            width: 100%;
            margin: 15pt 0;
            page-break-inside: avoid;
        }

        th, td {
            border: 1px solid #ddd;
            padding: 8pt;
            text-align: left;
        }

        th {
            background-color: #f4f4f4;
            font-weight: bold;
            color: #000;
        }

        tr:nth-child(even) {
            background-color: #fafafa;
        }

        img {
            max-width: 100%;
            height: auto;
            display: block;
            margin: 1em auto;
        }

        a {
            color: #0066cc;
            text-decoration: none;
        }

        a:hover {
            text-decoration: underline;
        }

        ul, ol {
            margin: 0.5em 0;
            padding-left: 2em;
        }

        li {
            margin: 0.25em 0;
        }

        hr {
            border: none;
            border-top: 1px solid #ccc;
            margin: 2em 0;
        }
        """
