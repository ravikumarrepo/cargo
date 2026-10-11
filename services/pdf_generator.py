"""
PDF Generator Service
Handles PDF generation using ReportLab
Works on all platforms including Render (no Chrome needed)
Emojis are automatically removed for PDF compatibility
"""

from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from io import BytesIO
import os
import re


class PDFGenerator:
    """Service for generating PDFs using ReportLab"""

    def __init__(self):
        pass

    @staticmethod
    def _remove_emojis(text):
        """Remove emojis from text, keeping only ASCII and common Latin characters"""
        if not text:
            return text

        result = []
        for char in text:
            code = ord(char)
            # Keep only ASCII letters, digits, punctuation, spaces, and common Latin-1
            # ASCII: 0-127, Latin-1 Supplement: 128-255
            if code <= 255:
                result.append(char)
            # Skip all emoji ranges and symbol characters
            # Emoji ranges: 0x1F300-0x1F9FF, 0x2600-0x27BF, 0x2300-0x23FF, etc.
            # Keep nothing above Unicode 255

        cleaned = ''.join(result).strip()
        # If everything was stripped, return placeholder
        return cleaned if cleaned else "[content]"

    def _get_page_size(self, page_size='A4', orientation='portrait'):
        """Get page size tuple from string"""
        if page_size == 'LETTER':
            base_size = letter
        else:
            base_size = A4

        if orientation == 'landscape':
            return (base_size[1], base_size[0])
        return base_size

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
        Generate a single PDF using ReportLab

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

        try:
            # Clean emojis from text for PDF compatibility
            title_clean = self._remove_emojis(title) if title else ""
            content_clean = self._remove_emojis(content) if content else ""

            # Create BytesIO buffer for PDF
            buffer = BytesIO()

            # Get page size
            page = self._get_page_size(page_size, orientation)

            # Convert margin from points to inches
            margin_inches = margin / 72.0

            # Create PDF document
            doc = SimpleDocTemplate(
                buffer,
                pagesize=page,
                rightMargin=margin_inches * inch,
                leftMargin=margin_inches * inch,
                topMargin=margin_inches * inch,
                bottomMargin=margin_inches * inch,
                title=f'{airline} - {title_clean}',
                author='Cargo'
            )

            # Create styles
            styles = getSampleStyleSheet()

            # Custom title style
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=font_size + 7,
                textColor='#1a1a1a',
                spaceAfter=30,
                alignment=TA_CENTER,
                fontName='Helvetica-Bold'
            )

            # Custom body style
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
            if title_clean:
                story.append(Paragraph(title_clean, title_style))
                story.append(Spacer(1, 0.2 * inch))

            # Add content paragraphs
            if content_clean:
                paragraphs = content_clean.split('\n')
                for para in paragraphs:
                    para_text = para.strip()
                    if para_text:
                        # Escape special characters
                        para_text = para_text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                        story.append(Paragraph(para_text, body_style))
                    else:
                        story.append(Spacer(1, 0.1 * inch))

            # Build PDF
            doc.build(story)

            # Get PDF data
            buffer.seek(0)
            return buffer

        except Exception as e:
            print(f"Error generating PDF: {str(e)}")
            raise

    def sanitize_filename(self, filename: str) -> str:
        """
        Sanitize filename for filesystem and ZIP compatibility

        Args:
            filename: Original filename

        Returns:
            Safe filename
        """
        # Remove emojis from filename
        filename = self._remove_emojis(filename)

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
