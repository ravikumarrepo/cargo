"""
PDF Generator Service
Handles PDF generation using ReportLab with emoji font support
Supports full emoji rendering and Unicode characters
Works on all platforms including Render
Uses Noto Color Emoji font for proper emoji rendering
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
import urllib.request


class PDFGenerator:
    """Service for generating PDFs using ReportLab with emoji font support"""

    def __init__(self):
        self.emoji_font_loaded = False
        self._load_emoji_font()

    def _load_emoji_font(self):
        """Load Noto Color Emoji font for emoji support"""
        try:
            # Check if font is already registered
            if 'NotoColorEmoji' in pdfmetrics.getRegisteredFontNames():
                self.emoji_font_loaded = True
                return

            # Try to find system emoji font
            font_paths = [
                '/usr/share/fonts/opentype/noto/NotoColorEmoji.ttf',  # Linux
                'C:\\Windows\\Fonts\\seguiemj.ttf',  # Windows (Segoe UI Emoji)
                '/Library/Fonts/NotoColorEmoji.ttf',  # macOS
                '/System/Library/Fonts/Apple Color Emoji.ttc',  # macOS alt
            ]

            font_found = False
            for font_path in font_paths:
                if os.path.exists(font_path):
                    try:
                        pdfmetrics.registerFont(TTFont('EmojiFont', font_path))
                        self.emoji_font_loaded = True
                        font_found = True
                        print(f"Loaded emoji font from: {font_path}")
                        break
                    except Exception as e:
                        print(f"Failed to load font from {font_path}: {e}")
                        continue

            if not font_found:
                # Try downloading Noto Color Emoji if not found locally
                print("Emoji font not found locally, attempting fallback...")
                self.emoji_font_loaded = False

        except Exception as e:
            print(f"Error loading emoji font: {e}")
            self.emoji_font_loaded = False

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
        Generate a single PDF using ReportLab with emoji support

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

            # Determine font to use (with emoji support if available)
            body_font = 'Helvetica'
            title_font = 'Helvetica-Bold'

            if self.emoji_font_loaded:
                body_font = 'EmojiFont'
                title_font = 'EmojiFont'

            # Custom title style
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=font_size + 7,
                textColor='#1a1a1a',
                spaceAfter=30,
                alignment=TA_CENTER,
                fontName=title_font
            )

            # Custom body style
            body_style = ParagraphStyle(
                'CustomBody',
                parent=styles['BodyText'],
                fontSize=font_size,
                leading=font_size * 1.6,
                spaceAfter=12,
                alignment=TA_LEFT,
                fontName=body_font
            )

            # Build story
            story = []

            # Add title
            if title:
                story.append(Paragraph(self._prepare_paragraph(title, font_size + 7), title_style))
                story.append(Spacer(1, 0.2 * inch))

            # Add content paragraphs
            if content:
                paragraphs = content.split('\n')
                for para in paragraphs:
                    para_text = para.strip()
                    if para_text:
                        # Escape special characters but keep emojis
                        para_text = self._prepare_paragraph(para_text, font_size)
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

    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters"""
        if not text:
            return text

        text = text.replace('&', '&amp;')
        text = text.replace('<', '&lt;')
        text = text.replace('>', '&gt;')

        return text


    def _prepare_paragraph(self, text: str, font_size: int = 11) -> str:
        """Replace emojis with inline PNG images for PDF rendering."""
        import emoji as emoji_lib

        if not text:
            return ""

        matches = emoji_lib.emoji_list(text)
        parts = []
        last = 0

        cache_dir = "/tmp/cargo_emoji_cache"
        os.makedirs(cache_dir, exist_ok=True)

        for match in matches:
            start = match["match_start"]
            end = match["match_end"]
            emoji_char = match["emoji"]

            # Escape the ordinary text before this emoji.
            parts.append(self._escape_html(text[last:start]))

            # Create the Twemoji PNG filename.
            codepoints = "-".join(
                f"{ord(char):x}"
                for char in emoji_char
                if ord(char) != 0xFE0F
            )

            image_path = os.path.join(cache_dir, f"{codepoints}.png")
            image_url = (
                "https://cdnjs.cloudflare.com/ajax/libs/"
                f"twemoji/14.0.2/72x72/{codepoints}.png"
            )

            try:
                if not os.path.exists(image_path):
                    with urllib.request.urlopen(image_url, timeout=5) as response:
                        image_data = response.read()

                    with open(image_path, "wb") as image_file:
                        image_file.write(image_data)

                size = max(10, font_size)
                parts.append(
                    f'<img src="{image_path}" width="{size}" '
                    f'height="{size}" valign="middle"/>'
                )
            except Exception as error:
                print(f"Could not load emoji {emoji_char}: {error}")
                parts.append("[emoji]")

            last = end

        parts.append(self._escape_html(text[last:]))
        return "".join(parts)


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
