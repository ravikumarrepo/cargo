"""
PDF Generator Service
Handles PDF generation using html2pdf API
Supports full emoji rendering without black boxes
Works on all platforms including Render
"""

import requests
from io import BytesIO
import os
import re
import json


class PDFGenerator:
    """Service for generating PDFs with full emoji support via html2pdf API"""

    def __init__(self):
        self.api_url = "https://html2pdf.app/v1/generate"
        self.api_key = os.environ.get("HTML2PDF_API_KEY", "free")  # Free tier available

    def _get_page_format(self, page_size='A4'):
        """Get page format for html2pdf"""
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
        Generate a single PDF using html2pdf API with full emoji support

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
            # Escape HTML special characters but preserve emojis
            title_safe = self._escape_html(title) if title else ""
            content_safe = self._escape_html(content) if content else ""

            # Build content paragraphs
            content_paragraphs = ""
            if content_safe:
                paragraphs = content_safe.split('\n')
                for para in paragraphs:
                    para_text = para.strip()
                    if para_text:
                        content_paragraphs += f'<p>{para_text}</p>\n'
                    else:
                        content_paragraphs += '<p>&nbsp;</p>\n'

            # Convert margin from mm to cm for CSS
            margin_cm = margin / 10

            # Create HTML with full emoji support
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <style>
                    @page {{
                        size: {self._get_page_format(page_size)} {'landscape' if orientation == 'landscape' else 'portrait'};
                        margin: {margin_cm}cm;
                    }}

                    body {{
                        font-family: 'Segoe UI', 'Apple Color Emoji', 'Noto Color Emoji', sans-serif;
                        font-size: {font_size}px;
                        line-height: 1.6;
                        color: #1a1a1a;
                        margin: 0;
                        padding: 0;
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
                    }}
                </style>
            </head>
            <body>
                <h1>{title_safe}</h1>
                {content_paragraphs}
            </body>
            </html>
            """

            # Try html2pdf.app API (free, no key required)
            try:
                response = requests.post(
                    self.api_url,
                    json={
                        "html": html_content,
                        "apiKey": self.api_key
                    },
                    timeout=30
                )

                if response.status_code == 200:
                    return BytesIO(response.content)
            except Exception as e:
                print(f"html2pdf.app API failed: {e}")

            # Fallback: use local ReportLab as backup
            print("Falling back to local PDF generation...")
            return self._generate_pdf_local(
                airline, title, content, page_size, orientation, font_size, margin
            )

        except Exception as e:
            print(f"Error generating PDF: {str(e)}")
            raise

    def _generate_pdf_local(
        self,
        airline: str,
        title: str,
        content: str,
        page_size: str,
        orientation: str,
        font_size: int,
        margin: int
    ) -> BytesIO:
        """Fallback local PDF generation using ReportLab"""
        from reportlab.lib.pagesizes import A4, letter
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.enums import TA_CENTER, TA_LEFT

        # Get page size
        if page_size == 'LETTER':
            base_size = letter
        else:
            base_size = A4

        if orientation == 'landscape':
            page = (base_size[1], base_size[0])
        else:
            page = base_size

        # Convert margin from mm to inches
        margin_inches = margin / 25.4

        # Create buffer
        buffer = BytesIO()

        # Create PDF document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=page,
            rightMargin=margin_inches * inch,
            leftMargin=margin_inches * inch,
            topMargin=margin_inches * inch,
            bottomMargin=margin_inches * inch,
            title=f'{airline} - {title}',
            author='Cargo'
        )

        # Create styles
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=font_size + 7,
            textColor='#1a1a1a',
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )

        body_style = ParagraphStyle(
            'CustomBody',
            parent=styles['BodyText'],
            fontSize=font_size,
            leading=font_size * 1.6,
            spaceAfter=12,
            alignment=TA_LEFT,
            fontName='Helvetica'
        )

        # Build story
        story = []

        # Add title
        if title:
            story.append(Paragraph(self._escape_html(title), title_style))
            story.append(Spacer(1, 0.2 * inch))

        # Add content
        if content:
            paragraphs = content.split('\n')
            for para in paragraphs:
                para_text = para.strip()
                if para_text:
                    para_text = self._escape_html(para_text)
                    story.append(Paragraph(para_text, body_style))
                else:
                    story.append(Spacer(1, 0.1 * inch))

        # Build PDF
        doc.build(story)

        buffer.seek(0)
        return buffer

    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters but preserve emojis"""
        if not text:
            return text

        text = text.replace('&', '&amp;')
        text = text.replace('<', '&lt;')
        text = text.replace('>', '&gt;')

        return text

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
