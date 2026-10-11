"""
PDF Generator Service
Handles PDF generation with emoji support using Selenium + Chrome
"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from io import BytesIO
import os
import re
import base64
import tempfile
import json


class PDFGenerator:
    """Service for generating PDFs with full emoji support using Chrome"""

    def __init__(self):
        pass

    def _get_chrome_options(self):
        """Configure Chrome options for PDF generation"""
        chrome_options = Options()
        chrome_options.add_argument('--headless=new')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-software-rasterizer')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')

        # Keep window open
        chrome_options.add_experimental_option("detach", False)

        return chrome_options

    def _create_html_content(self, airline, title, content, font_size, margin, page_size='A4', orientation='portrait'):
        """Create HTML content with emoji-supporting fonts"""

        # Escape HTML
        title_escaped = title.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;') if title else ''

        # Convert content paragraphs
        content_html = ''
        if content:
            paragraphs = content.split('\n')
            for para in paragraphs:
                para_escaped = para.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                if para_escaped.strip():
                    content_html += f'<p>{para_escaped}</p>'
                else:
                    content_html += '<p class="empty">&nbsp;</p>'

        # Page dimensions
        page_css = f'size: {page_size} {orientation};'

        # Create complete HTML document
        html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{airline} - {title_escaped}</title>
    <style>
        @page {{
            {page_css}
            margin: {margin * 0.0352778}cm;
        }}

        body {{
            font-family: "Segoe UI", "Segoe UI Emoji", "Segoe UI Symbol", "Noto Color Emoji", "Apple Color Emoji", Arial, sans-serif;
            font-size: {font_size}pt;
            line-height: 1.6;
            color: #333;
            margin: 0;
            padding: 0;
            -webkit-print-color-adjust: exact;
            print-color-adjust: exact;
        }}

        h1 {{
            font-size: {font_size + 7}pt;
            text-align: center;
            color: #1a1a1a;
            margin-bottom: 30px;
            font-weight: bold;
        }}

        p {{
            margin: 0 0 15px 0;
            text-align: left;
        }}

        p.empty {{
            margin: 0 0 8px 0;
            height: 0.5em;
        }}

        /* Ensure emojis render */
        body, h1, p {{
            font-feature-settings: "liga" 1, "calt" 1;
            -webkit-font-smoothing: antialiased;
        }}
    </style>
</head>
<body>
    <h1>{title_escaped}</h1>
    {content_html}
    <script>
        // Signal that page is ready
        window.pageReady = true;
    </script>
</body>
</html>'''

        return html

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
        Generate a single PDF with full emoji support using Chrome

        Args:
            airline: Airline name (for metadata)
            title: Document title
            content: Document content
            page_size: 'A4' or 'LETTER'
            orientation: 'portrait' or 'landscape'
            font_size: Base font size
            margin: Page margin in points

        Returns:
            BytesIO buffer containing PDF data
        """

        # Create HTML content
        html_content = self._create_html_content(airline, title, content, font_size, margin, page_size, orientation)

        # Create temporary HTML file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
            f.write(html_content)
            html_file_path = f.name

        driver = None
        try:
            # Setup Chrome
            chrome_options = self._get_chrome_options()

            # Initialize driver
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)

            # Load HTML file
            file_url = 'file:///' + html_file_path.replace('\\', '/')
            driver.get(file_url)

            # Wait for page to be ready
            WebDriverWait(driver, 10).until(
                lambda d: d.execute_script('return window.pageReady === true')
            )

            # Additional wait for font loading
            driver.execute_script('return document.fonts.ready')

            # PDF print settings for Chrome DevTools Protocol
            print_options = {
                'landscape': orientation == 'landscape',
                'displayHeaderFooter': False,
                'printBackground': True,
                'preferCSSPageSize': True,
                'marginTop': 0,
                'marginBottom': 0,
                'marginLeft': 0,
                'marginRight': 0,
            }

            # Generate PDF using Chrome DevTools Protocol
            result = driver.execute_cdp_cmd('Page.printToPDF', print_options)

            # Decode base64 PDF data
            pdf_bytes = base64.b64decode(result['data'])

            # Create BytesIO buffer
            buffer = BytesIO(pdf_bytes)
            buffer.seek(0)

            return buffer

        finally:
            # Clean up
            if driver:
                try:
                    driver.quit()
                except:
                    pass

            # Clean up temp file
            try:
                if os.path.exists(html_file_path):
                    os.unlink(html_file_path)
            except:
                pass

    def sanitize_filename(self, filename: str) -> str:
        """
        Sanitize filename for filesystem and ZIP compatibility

        Args:
            filename: Original filename

        Returns:
            Safe filename
        """
        # Remove or replace invalid characters
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)

        # Remove control characters
        filename = ''.join(char for char in filename if ord(char) >= 32)

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
