
"""
Cargo PDF Generator
Uses Playwright/Chromium for PDF generation.
Reuses one browser and one page for bulk batches.
Preserves Unicode and emoji characters where supported by installed fonts.
"""

import asyncio
import html
import os
import re
from io import BytesIO

from playwright.async_api import async_playwright


class PDFGenerator:
    def __init__(self):
        pass

    def _get_page_format(self, page_size="A4"):
        return "Letter" if str(page_size).upper() == "LETTER" else "A4"

    def _escape_html(self, text):
        """Escape HTML without removing Unicode or emoji characters."""
        return html.escape(str(text or ""), quote=True)

    def _build_html(self, title, content, font_size, margin):
        """Build a standalone HTML document without external requests."""
        title_safe = self._escape_html(title)
        content_safe = self._escape_html(content)

        paragraphs = []
        for paragraph in content_safe.splitlines():
            if paragraph.strip():
                paragraphs.append(f"<p>{paragraph.strip()}</p>")
            else:
                paragraphs.append("<p>&nbsp;</p>")

        return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        @page {{
            size: auto;
        }}

        * {{
            box-sizing: border-box;
        }}

        html {{
            -webkit-print-color-adjust: exact;
            print-color-adjust: exact;
        }}

        body {{
            font-family: "Noto Color Emoji", "Segoe UI Emoji",
                         "Apple Color Emoji", Arial, sans-serif;
            font-size: {font_size}px;
            line-height: 1.6;
            color: #1a1a1a;
            margin: 0;
            padding: 0;
            overflow-wrap: anywhere;
            -webkit-print-color-adjust: exact;
            print-color-adjust: exact;
        }}

        
        @font-face {
            font-family: "NotoColorEmoji";
            src: url("file:///opt/render/project/src/static/fonts/NotoColorEmoji.ttf");
        }
        
        .emoji {
            font-family: "NotoColorEmoji", sans-serif;
        }


        h1 {{
            font-size: {font_size + 7}px;
            font-weight: bold;
            text-align: center;
            margin: 0 0 20px 0;
            color: #1a1a1a;
            overflow-wrap: anywhere;
        }}

        p {{
            margin: 12px 0;
            white-space: pre-wrap;
            overflow-wrap: anywhere;
            word-break: normal;
        }}
    </style>
</head>
<body>
    <h1>{title_safe}</h1>
    {''.join(paragraphs)}
</body>
</html>"""

    async def _generate_many_async(self, documents):
        """Generate a batch with one Chromium browser and one page."""
        if not documents:
            return []

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
                context = await browser.new_context()
                page = await context.new_page()
                results = []

                try:
                    for doc in documents:
                        font_size = int(doc.get("font_size", 11))
                        margin = int(doc.get("margin", 50))

                        html_content = self._build_html(
                            title=doc.get("title", ""),
                            content=doc.get("content", ""),
                            font_size=font_size,
                            margin=margin,
                        )

                        await page.set_content(
                            html_content,
                            wait_until="domcontentloaded",
                        )

                        # Wait for the browser's available fonts to be ready.
                        await page.evaluate(
                            "() => document.fonts.ready.then(() => true)"
                        )

                        pdf_bytes = await page.pdf(
                            format=self._get_page_format(
                                doc.get("page_size", "A4")
                            ),
                            landscape=(
                                str(doc.get("orientation", "portrait")).lower()
                                == "landscape"
                            ),
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
                    await context.close()

                return results

            finally:
                await browser.close()

    def generate_pdfs(self, documents):
        """Return a list of BytesIO objects, in the same order as documents."""
        try:
            pdf_results = asyncio.run(
                self._generate_many_async(documents)
            )
            return [BytesIO(data) for data in pdf_results]
        except Exception as exc:
            print(f"Error generating bulk PDFs: {exc}")
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

    def generate_pdf(
        self,
        airline,
        title,
        content,
        page_size="A4",
        orientation="portrait",
        font_size=11,
        margin=50,
    ):
        try:
            pdf_bytes = asyncio.run(
                self._generate_pdf_async(
                    airline,
                    title,
                    content,
                    page_size,
                    orientation,
                    font_size,
                    margin,
                )
            )
            return BytesIO(pdf_bytes)
        except Exception as exc:
            print(f"Error generating PDF: {exc}")
            raise

    def generate_preview_pdf(self, airline, title, content, settings):
        return self.generate_pdf(
            airline=airline,
            title=title,
            content=content,
            page_size=settings.get("pageSize", "A4"),
            orientation=settings.get("orientation", "portrait"),
            font_size=settings.get("fontSize", 11),
            margin=settings.get("margin", 50),
        )

    def sanitize_filename(self, filename):
        """Make a safe ZIP-compatible filename while retaining Unicode."""
        filename = str(filename or "")
        filename = re.sub(r'[<>:"/\\|?*]', "_", filename)
        filename = "".join(
            char for char in filename
            if ord(char) >= 32 and ord(char) != 127
        ).strip().rstrip(".")

        name, ext = os.path.splitext(filename)
        if ext.lower() != ".pdf":
            name = filename
        else:
            name = name

        name = name[:200].strip().rstrip(".")
        return f"{name}.pdf" if name else "document.pdf"
