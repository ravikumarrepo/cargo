
"""
PDF Generator Service
- Generates PDFs using Playwright and Chromium
- Supports Unicode and emoji characters
- Supports A4 and Letter page sizes
- Supports portrait and landscape orientation
- Optimized bulk generation: one browser per batch
- Compatible with Render deployment
"""

import asyncio
import os
import re
from io import BytesIO
from html import escape

from playwright.async_api import async_playwright


class PDFGenerator:
    """PDF generation service with optimized bulk processing."""

    def __init__(self):
        pass

    def _get_page_format(self, page_size="A4"):
        """Return the Playwright page format."""
        if str(page_size).upper() == "LETTER":
            return "Letter"
        return "A4"

    def _escape_html(self, text):
        """Escape HTML characters while preserving Unicode and emojis."""
        if not text:
            return ""
        return escape(str(text), quote=True)

    def _build_html(
        self,
        title,
        content,
        font_size=11,
        margin=50,
    ):
        """Build the HTML document used for PDF rendering."""

        title_safe = self._escape_html(title)
        content_safe = self._escape_html(content)

        paragraphs = []

        for paragraph in content_safe.split("\n"):
            if paragraph.strip():
                paragraphs.append(f"<p>{paragraph.strip()}</p>")
            else:
                paragraphs.append("<p>&nbsp;</p>")

        content_html = "\n".join(paragraphs)

        return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">

    <style>
        @page {{
            margin: 0;
        }}

        html {{
            -webkit-print-color-adjust: exact;
            print-color-adjust: exact;
        }}

        body {{
            font-family:
                "Noto Sans",
                "Segoe UI",
                "Apple Color Emoji",
                "Segoe UI Emoji",
                "Noto Color Emoji",
                sans-serif;
            font-size: {int(font_size)}px;
            line-height: 1.6;
            color: #1a1a1a;
            margin: 0;
            padding: {int(margin)}mm;
            overflow-wrap: anywhere;
        }}

        h1 {{
            font-size: {int(font_size) + 7}px;
            font-weight: bold;
            text-align: center;
            margin: 0 0 20px 0;
            color: #1a1a1a;
            overflow-wrap: anywhere;
        }}

        p {{
            margin: 12px 0;
            overflow-wrap: anywhere;
            word-break: break-word;
            white-space: pre-wrap;
        }}
    </style>
</head>

<body>
    <h1>{title_safe}</h1>
    {content_html}
</body>
</html>"""

    async def _generate_many_async(self, documents):
        """
        Generate multiple PDFs using one browser.

        Each document receives its own page. Pages are closed
        immediately after PDF generation to limit memory usage.
        """

        if not documents:
            return []

        results = []

        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                ],
            )

            try:
                for document in documents:
                    title = document.get("title") or ""
                    content = document.get("content") or ""

                    font_size = int(document.get("font_size", 11))
                    margin = int(document.get("margin", 50))

                    page_size = self._get_page_format(
                        document.get("page_size", "A4")
                    )

                    orientation = str(
                        document.get("orientation", "portrait")
                    ).lower()

                    html_content = self._build_html(
                        title=title,
                        content=content,
                        font_size=font_size,
                        margin=margin,
                    )

                    page = await browser.new_page()

                    try:
                        # No networkidle wait: the HTML is self-contained.
                        await page.set_content(
                            html_content,
                            wait_until="load",
                        )

                        pdf_bytes = await page.pdf(
                            format=page_size,
                            landscape=(orientation == "landscape"),
                            margin={
                                "top": f"{margin}mm",
                                "bottom": f"{margin}mm",
                                "left": f"{margin}mm",
                                "right": f"{margin}mm",
                            },
                            print_background=True,
                        )

                        results.append(pdf_bytes)

                    finally:
                        await page.close()

                return results

            finally:
                await browser.close()

    def generate_pdfs(self, documents):
        """
        Generate a list of PDFs with a single browser launch.

        Args:
            documents: List of dictionaries. Each dictionary can contain:
                airline, title, content, page_size, orientation,
                font_size, margin.

        Returns:
            List of BytesIO buffers in the same order as documents.
        """

        if not documents:
            return []

        try:
            pdf_results = asyncio.run(
                self._generate_many_async(documents)
            )

            return [
                BytesIO(pdf_bytes)
                for pdf_bytes in pdf_results
            ]

        except Exception as error:
            print(f"Error generating bulk PDFs: {error}")
            raise

    async def _generate_pdf_async(
        self,
        airline,
        title,
        content,
        page_size,
        orientation,
        font_size,
        margin,
    ):
        """Generate a single PDF asynchronously."""

        results = await self._generate_many_async([
            {
                "airline": airline,
                "title": title,
                "content": content,
                "page_size": page_size,
                "orientation": orientation,
                "font_size": font_size,
                "margin": margin,
            }
        ])

        return results[0]

    def generate_pdf(
        self,
        airline: str,
        title: str,
        content: str,
        page_size: str = "A4",
        orientation: str = "portrait",
        font_size: int = 11,
        margin: int = 50,
    ) -> BytesIO:
        """Generate one PDF and return it as a BytesIO buffer."""

        try:
            pdf_bytes = asyncio.run(
                self._generate_pdf_async(
                    airline=airline,
                    title=title,
                    content=content,
                    page_size=page_size,
                    orientation=orientation,
                    font_size=font_size,
                    margin=margin,
                )
            )

            return BytesIO(pdf_bytes)

        except Exception as error:
            print(f"Error generating PDF: {error}")
            raise

    def generate_preview_pdf(
        self,
        airline: str,
        title: str,
        content: str,
        settings: dict,
    ) -> BytesIO:
        """Generate a preview PDF using custom settings."""

        return self.generate_pdf(
            airline=airline,
            title=title,
            content=content,
            page_size=settings.get("pageSize", "A4"),
            orientation=settings.get("orientation", "portrait"),
            font_size=settings.get("fontSize", 11),
            margin=settings.get("margin", 50),
        )

    def sanitize_filename(self, filename: str) -> str:
        """Sanitize a filename while preserving Unicode characters."""

        filename = str(filename or "").strip()

        # Replace filesystem-invalid characters.
        filename = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", filename)

        name, extension = os.path.splitext(filename)

        if len(name) > 200:
            name = name[:200]

        if extension.lower() != ".pdf":
            filename = name + ".pdf"
        else:
            filename = name + extension

        if not filename or filename == ".pdf":
            filename = "document.pdf"

        return filename
