"""
PDF Generator Service
Handles PDF generation using Playwright with Chrome
Supports full emoji rendering and Unicode characters
Works on Render with headless Chromium
"""

import asyncio
from playwright.async_api import async_playwright
from io import BytesIO
import os
import re


class PDFGenerator:
    """Service for generating PDFs using Playwright with full emoji support"""

    def __init__(self):
        pass

    def _get_page_format(self, page_size='A4'):
        """Get page format for Playwright"""
        if page_size == 'LETTER':
            return 'Letter'
        return 'A4'

    def generate_pdf(
        self,
        airline: str,
        title: str,
        content: str,
        page_size: str = 'A4',
        orientation: str = 'portrait',
        font_size: int = 11,
        margin: int = 50
    ) -> BytesIO:
        """
        Generate a single PDF using Playwright with full emoji support

        Args:
            airline: Airline name (for metadata)
            title: Document title (emojis fully supported)
            content: Document content (emojis fully supported)
            page_size: 'A4' or 'LETTER'
            orientation: 'portrait' or 'landscape'
            font_size: Base font size
            margin: Page margin in mm

        Returns:
            BytesIO buffer containing PDF data
        """

        try:
            # Run async function synchronously
            pdf_bytes = asyncio.run(self._generate_pdf_async(
                airline, title, content, page_size, orientation, font_size, margin
            ))
            return BytesIO(pdf_bytes)

        except Exception as e:
            print(f"Error generating PDF: {str(e)}")
            raise

    async def _generate_pdf_async(
        self,
        airline: str,
        title: str,
        content: str,
        page_size: str,
        orientation: str,
        font_size: int,
        margin: int
    ) -> bytes:
        """Async PDF generation using Playwright"""

        # Escape HTML special characters but preserve emojis
        title_safe = self._escape_html(title) if title else ""
        content_safe = self._escape_html(content) if content else ""

        # Build content paragraphs with emoji support
        content_paragraphs = ""
        if content_safe:
            paragraphs = content_safe.split('\n')
            for para in paragraphs:
                para_text = para.strip()
                if para_text:
                    content_paragraphs += f'<p>{para_text}</p>\n'
                else:
                    content_paragraphs += '<p>&nbsp;</p>\n'

        # Create HTML with full emoji support
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Apple Color Emoji', 'Segoe UI Emoji', sans-serif;
                    font-size: {font_size}px;
                    line-height: 1.6;
                    color: #1a1a1a;
                    margin: 0;
                    padding: {margin}mm;
                }}

                h1 {{
                    font-size: {font_size + 7}px;
                    font-weight: bold;
                    text-align: center;
                    margin: 0 0 20px 0;
                    color: #1a1a1a;
                }}

                p {{
                    margin: 12px 0;
                    word-wrap: break-word;
                    word-break: break-word;
                }}
            </style>
        </head>
        <body>
            <h1>{title_safe}</h1>
            {content_paragraphs}
        </body>
        </html>
        """

        async with async_playwright() as p:
            # Launch Chromium browser
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage'
                ]
            )

            try:
                page = await browser.new_page()

                # Set content with emoji font support
                await page.set_content(html_content, wait_until='networkidle')

                # Generate PDF with emoji support
                page_format = self._get_page_format(page_size)
                margin_mm = f"{margin}mm"

                pdf_bytes = await page.pdf(
                    format=page_format,
                    margin={
                        'top': margin_mm,
                        'bottom': margin_mm,
                        'left': margin_mm,
                        'right': margin_mm
                    },
                    landscape=(orientation == 'landscape'),
                    print_background=True
                )

                await page.close()
                return pdf_bytes

            finally:
                await browser.close()

    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters but preserve emojis"""
        if not text:
            return text

        text = text.replace('&', '&amp;')
        text = text.replace('<', '&lt;')
        text = text.replace('>', '&gt;')
        text = text.replace('"', '&quot;')
        text = text.replace("'", '&#39;')

        return text

    def sanitize_filename(self, filename: str) -> str:
        """
        Sanitize filename for filesystem and ZIP compatibility

        Args:
            filename: Original filename

        Returns:
            Safe filename with emojis preserved where possible
        """
        # Remove or replace invalid characters
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)

        # Remove control characters but keep emojis
        filename = ''.join(char for char in filename if ord(char) >= 32 or char in '\n\t')

        # Limit length
        name, ext = os.path.splitext(filename)
        if len(name) > 200:
            name = name[:200]

        # Ensure it has .pdf extension
        if not ext.lower() == '.pdf':
            filename = name + '.pdf'
        else:
            filename = name + ext

        # Ensure it's not empty
        if not filename or filename == '.pdf':
            filename = 'document.pdf'

        return filename

    def generate_preview_pdf(
        self,
        airline: str,
        title: str,
        content: str,
        settings: dict
    ) -> BytesIO:
        """Generate preview PDF with custom settings"""

        return self.generate_pdf(
            airline=airline,
            title=title,
            content=content,
            page_size=settings.get('pageSize', 'A4'),
            orientation=settings.get('orientation', 'portrait'),
            font_size=settings.get('fontSize', 11),
            margin=settings.get('margin', 50)
        )
