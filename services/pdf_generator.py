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
        """Generate one PDF using a shared browser-compatible workflow."""

        results = await self._generate_many_async([{
            "airline": airline,
            "title": title,
            "content": content,
            "page_size": page_size,
            "orientation": orientation,
            "font_size": font_size,
            "margin": margin,
        }])
        return results[0]

    async def _generate_many_async(self, documents: list) -> list:
        """Generate multiple PDFs using one Chromium browser."""

        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                ],
            )

            try:
                results = []

                for doc in documents:
                    title_safe = self._escape_html(
                        doc.get("title", "")
                    )
                    content_safe = self._escape_html(
                        doc.get("content", "")
                    )

                    paragraphs = []
                    for para in content_safe.split("\n"):
                        if para.strip():
                            paragraphs.append(f"<p>{para.strip()}</p>")
                        else:
                            paragraphs.append("<p>&nbsp;</p>")

                    font_size = int(doc.get("font_size", 11))
                    margin = int(doc.get("margin", 50))

                    html_content = f"""
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <meta charset="UTF-8">
                        <style>
                            body {{
                                font-family: -apple-system,
                                    BlinkMacSystemFont, 'Segoe UI',
                                    'Apple Color Emoji', 'Segoe UI Emoji',
                                    sans-serif;
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
                                overflow-wrap: anywhere;
                                word-break: break-word;
                            }}
                        </style>
                    </head>
                    <body>
                        <h1>{title_safe}</h1>
                        {''.join(paragraphs)}
                    </body>
                    </html>
                    """

                    page = await browser.new_page()
                    try:
                        await page.set_content(
                            html_content,
                            wait_until="load",
                        )

                        pdf_bytes = await page.pdf(
                            format=self._get_page_format(
                                doc.get("page_size", "A4")
                            ),
                            margin={
                                "top": f"{margin}mm",
                                "bottom": f"{margin}mm",
                                "left": f"{margin}mm",
                                "right": f"{margin}mm",
                            },
                            landscape=(
                                doc.get("orientation", "portrait")
                                == "landscape"
                            ),
                            print_background=True,
                        )
                        results.append(pdf_bytes)
                    finally:
                        await page.close()

                return results

            finally:
                await browser.close()

    def generate_pdfs(self, documents: list) -> list:
        """Synchronous entry point for bulk PDF generation."""

        try:
            results = asyncio.run(
                self._generate_many_async(documents)
            )
            return [BytesIO(data) for data in results]
        except Exception as e:
            print(f"Error generating bulk PDFs: {e}")
            raise


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
