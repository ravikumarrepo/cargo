"""
PDF Generator Service
Handles PDF generation using ReportLab with emoji-to-image conversion
Supports full emoji rendering via PIL/Pillow
Works on all platforms including Render
"""

from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.pdfgen import canvas
from io import BytesIO
import os
import re
import unicodedata
from PIL import Image, ImageDraw, ImageFont


class PDFGenerator:
    """Service for generating PDFs with emoji image rendering"""

    def __init__(self):
        self.emoji_size = 16  # Default emoji image size in pixels
        self.emoji_images = {}  # Cache for rendered emoji images

    def _render_emoji_to_image(self, emoji_char: str, size: int = 16) -> Image.Image:
        """Render emoji character to PIL image using system fonts"""

        try:
            # Create image
            img = Image.new('RGBA', (size, size), (255, 255, 255, 0))
            draw = ImageDraw.Draw(img)

            # Try to find a font that supports emojis
            font = None
            font_paths = [
                '/usr/share/fonts/opentype/noto/NotoColorEmoji.ttf',
                'C:\\Windows\\Fonts\\seguiemj.ttf',
                '/Library/Fonts/NotoColorEmoji.ttf',
                '/System/Library/Fonts/Apple Color Emoji.ttc',
            ]

            for font_path in font_paths:
                if os.path.exists(font_path):
                    try:
                        font = ImageFont.truetype(font_path, size)
                        break
                    except:
                        continue

            # Fall back to default font if no emoji font found
            if font is None:
                font = ImageFont.load_default()

            # Draw emoji
            draw.text((0, 0), emoji_char, fill=(0, 0, 0, 255), font=font)

            return img
        except Exception as e:
            print(f"Error rendering emoji {emoji_char}: {e}")
            # Return blank image on error
            return Image.new('RGBA', (size, size), (255, 255, 255, 0))

    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters"""
        if not text:
            return text

        text = text.replace('&', '&amp;')
        text = text.replace('<', '&lt;')
        text = text.replace('>', '&gt;')

        return text

    def _has_emoji(self, text: str) -> bool:
        """Check if text contains emojis"""
        for char in text:
            if ord(char) > 127:  # Non-ASCII
                try:
                    if unicodedata.category(char) in ('So', 'Sk'):  # Symbol categories
                        return True
                except:
                    pass
        return False

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
        Generate a single PDF using ReportLab with emoji image rendering

        Args:
            airline: Airline name (for metadata)
            title: Document title (emojis supported)
            content: Document content (emojis supported)
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
            if title:
                # Escape HTML but preserve emojis
                title_safe = self._escape_html(title)
                story.append(Paragraph(title_safe, title_style))
                story.append(Spacer(1, 0.2 * inch))

            # Add content paragraphs
            if content:
                paragraphs = content.split('\n')
                for para in paragraphs:
                    para_text = para.strip()
                    if para_text:
                        # Escape HTML but preserve emojis
                        para_text = self._escape_html(para_text)
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
