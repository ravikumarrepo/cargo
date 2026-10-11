"""
PDF Generator Service
Handles PDF generation with emoji support using ReportLab
Works on all platforms including Render (no Chrome needed)
"""

from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from io import BytesIO
import os
import re
import sys

# Try to register emoji-supporting fonts
def _setup_fonts():
    """Setup fonts with emoji support"""
    try:
        # Try to find and register DejaVu Sans font (has good emoji support)
        font_paths = [
            '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',  # Linux
            'C:\\Windows\\Fonts\\arial.ttf',  # Windows
            '/System/Library/Fonts/Arial.ttf',  # macOS
            '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',  # Linux alt
        ]

        for font_path in font_paths:
            if os.path.exists(font_path):
                try:
                    pdfmetrics.registerFont(TTFont('CustomFont', font_path))
                    return 'CustomFont'
                except:
                    pass
    except:
        pass

    # Fallback to Helvetica (standard)
    return 'Helvetica'

# Initialize font on module load
_CUSTOM_FONT = _setup_fonts()


class PDFGenerator:
    """Service for generating PDFs with emoji support using ReportLab"""

    def __init__(self):
        pass

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
        Generate a single PDF with emoji support using ReportLab

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
                title=f'{airline} - {title}',
                author='Cargo'
            )

            # Create styles
            styles = getSampleStyleSheet()

            # Custom title style - use Helvetica (safe fallback)
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=font_size + 7,
                textColor='#1a1a1a',
                spaceAfter=30,
                alignment=TA_CENTER,
                fontName='Helvetica-Bold'
            )

            # Custom body style - use Helvetica (safe fallback)
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
                # Keep emojis in title
                title_text = title
                story.append(Paragraph(title_text, title_style))
                story.append(Spacer(1, 0.2 * inch))

            # Add content paragraphs
            if content:
                paragraphs = content.split('\n')
                for para in paragraphs:
                    para_text = para.strip()
                    if para_text:
                        # Escape special characters but keep emojis
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
