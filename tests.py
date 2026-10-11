"""
Tests for Cargo - Bulk Content & PDF Generator
Run with: python -m pytest tests.py -v
"""

import unittest
from services.replacement import ReplacementService
from services.validation import ValidationService
from services.pdf_generator import PDFGenerator
from services.template_manager import TemplateManager


class TestReplacementService(unittest.TestCase):
    """Test the replacement service"""

    def setUp(self):
        self.service = ReplacementService()

    def test_placeholder_replacement(self):
        """Test placeholder mode replacement"""
        text = "Welcome to {{AIRLINE_NAME}}! Book with {{AIRLINE_NAME}} today."
        result, count = self.service.replace_text(text, "Air India", "placeholder")

        self.assertEqual(result, "Welcome to Air India! Book with Air India today.")
        self.assertEqual(count, 2)

    def test_original_name_replacement(self):
        """Test original name mode replacement"""
        text = "Welcome to Air India! Book with Air India today."
        result, count = self.service.replace_text(
            text, "IndiGo", "original", "Air India"
        )

        self.assertEqual(result, "Welcome to IndiGo! Book with IndiGo today.")
        self.assertEqual(count, 2)

    def test_case_insensitive_replacement(self):
        """Test case-insensitive replacement"""
        text = "AIR INDIA, Air India, air india"
        result, count = self.service.replace_text(
            text, "Emirates", "original", "air india", case_sensitive=False
        )

        self.assertEqual(count, 3)
        self.assertIn("Emirates", result)

    def test_case_sensitive_replacement(self):
        """Test case-sensitive replacement"""
        text = "AIR INDIA, Air India, air india"
        result, count = self.service.replace_text(
            text, "Emirates", "original", "Air India", case_sensitive=True
        )

        self.assertEqual(count, 1)
        self.assertIn("AIR INDIA", result)
        self.assertIn("air india", result)

    def test_emoji_preservation(self):
        """Test that emojis are preserved"""
        text = "Fly with {{AIRLINE_NAME}}! ✈️🌍🎉"
        result, count = self.service.replace_text(text, "Qatar Airways", "placeholder")

        self.assertIn("✈️", result)
        self.assertIn("🌍", result)
        self.assertIn("🎉", result)
        self.assertEqual(count, 1)

    def test_unicode_preservation(self):
        """Test that Unicode characters are preserved"""
        text = "{{AIRLINE_NAME}} - ñoño, 北京, العربية"
        result, count = self.service.replace_text(text, "Emirates", "placeholder")

        self.assertIn("ñoño", result)
        self.assertIn("北京", result)
        self.assertIn("العربية", result)

    def test_line_breaks_preservation(self):
        """Test that line breaks are preserved"""
        text = "Line 1\nLine 2\n\nLine 3 with {{AIRLINE_NAME}}"
        result, count = self.service.replace_text(text, "SpiceJet", "placeholder")

        self.assertEqual(result.count('\n'), 3)
        self.assertIn("Line 3 with SpiceJet", result)

    def test_multiple_occurrences(self):
        """Test replacing multiple occurrences"""
        text = "{{AIRLINE_NAME}} " * 50
        result, count = self.service.replace_text(text, "Test Air", "placeholder")

        self.assertEqual(count, 50)
        self.assertEqual(result.count("Test Air"), 50)

    def test_no_replacement(self):
        """Test when no replacement is found"""
        text = "No placeholder here"
        result, count = self.service.replace_text(text, "Air India", "placeholder")

        self.assertEqual(count, 0)
        self.assertEqual(result, text)

    def test_generate_all(self):
        """Test generating content for multiple airlines"""
        airlines = ["Air India", "IndiGo", "SpiceJet"]
        title = "Welcome to {{AIRLINE_NAME}}"
        content = "Book with {{AIRLINE_NAME}} today!"

        results = self.service.generate_all(
            title, content, airlines, "placeholder"
        )

        self.assertEqual(len(results), 3)
        self.assertEqual(results[0]['airline'], "Air India")
        self.assertIn("Air India", results[0]['generatedTitle'])
        self.assertIn("IndiGo", results[1]['generatedContent'])


class TestValidationService(unittest.TestCase):
    """Test the validation service"""

    def setUp(self):
        self.service = ValidationService()

    def test_valid_input(self):
        """Test validation with valid inputs"""
        result = self.service.validate(
            title="Title with {{AIRLINE_NAME}}",
            content="Content with {{AIRLINE_NAME}}",
            airlines=["Air India", "IndiGo"],
            replacement_mode="placeholder"
        )

        self.assertTrue(result['valid'])
        self.assertEqual(len(result['errors']), 0)

    def test_empty_title(self):
        """Test validation with empty title"""
        result = self.service.validate(
            title="",
            content="Content",
            airlines=["Air India"],
            replacement_mode="placeholder"
        )

        self.assertFalse(result['valid'])
        self.assertIn("Title cannot be empty", result['errors'])

    def test_empty_content(self):
        """Test validation with empty content"""
        result = self.service.validate(
            title="Title",
            content="",
            airlines=["Air India"],
            replacement_mode="placeholder"
        )

        self.assertFalse(result['valid'])
        self.assertIn("Content cannot be empty", result['errors'])

    def test_empty_airlines(self):
        """Test validation with empty airline list"""
        result = self.service.validate(
            title="Title",
            content="Content",
            airlines=[],
            replacement_mode="placeholder"
        )

        self.assertFalse(result['valid'])
        self.assertIn("Airline list cannot be empty", result['errors'])

    def test_missing_placeholder(self):
        """Test validation when placeholder is missing"""
        result = self.service.validate(
            title="Title without placeholder",
            content="Content without placeholder",
            airlines=["Air India"],
            replacement_mode="placeholder"
        )

        self.assertFalse(result['valid'])
        self.assertTrue(any("not found" in err for err in result['errors']))

    def test_missing_original_name(self):
        """Test validation in original mode without original name"""
        result = self.service.validate(
            title="Title with Air India",
            content="Content",
            airlines=["IndiGo"],
            replacement_mode="original",
            original_name=""
        )

        self.assertFalse(result['valid'])
        self.assertIn("Original airline name is required for original-name mode", result['errors'])

    def test_parse_airline_list_newlines(self):
        """Test parsing airlines separated by newlines"""
        text = "Air India\nIndiGo\nSpiceJet"
        airlines = self.service.parse_airline_list(text)

        self.assertEqual(len(airlines), 3)
        self.assertIn("Air India", airlines)

    def test_parse_airline_list_commas(self):
        """Test parsing airlines separated by commas"""
        text = "Air India, IndiGo, SpiceJet"
        airlines = self.service.parse_airline_list(text)

        self.assertGreaterEqual(len(airlines), 3)
        self.assertIn("IndiGo", airlines)

    def test_parse_airline_list_duplicates(self):
        """Test that duplicates are removed"""
        text = "Air India\nIndiGo\nAir India\nIndiGo"
        airlines = self.service.parse_airline_list(text)

        self.assertEqual(len(airlines), 2)

    def test_parse_airline_list_csv(self):
        """Test parsing CSV format"""
        text = "Airline\nAir India\nIndiGo\nSpiceJet"
        airlines = self.service.parse_airline_list(text)

        # Should skip header
        self.assertGreater(len(airlines), 0)


class TestPDFGenerator(unittest.TestCase):
    """Test the PDF generator"""

    def setUp(self):
        self.generator = PDFGenerator()

    def test_generate_pdf(self):
        """Test basic PDF generation"""
        buffer = self.generator.generate_pdf(
            airline="Air India",
            title="Welcome to Air India",
            content="Book your flights with Air India today!\n\nEnjoy great service."
        )

        self.assertIsNotNone(buffer)
        self.assertGreater(buffer.getbuffer().nbytes, 0)

    def test_pdf_with_emojis(self):
        """Test PDF generation with emojis"""
        buffer = self.generator.generate_pdf(
            airline="Emirates",
            title="Fly with Emirates ✈️",
            content="Great service 🌟 and comfort 😊"
        )

        self.assertIsNotNone(buffer)

    def test_pdf_with_unicode(self):
        """Test PDF generation with Unicode characters"""
        buffer = self.generator.generate_pdf(
            airline="Air France",
            title="Bienvenue à bord",
            content="Français, 中文, العربية, Español"
        )

        self.assertIsNotNone(buffer)

    def test_pdf_long_content(self):
        """Test PDF with long content (multiple pages)"""
        long_content = "This is a paragraph.\n\n" * 100
        buffer = self.generator.generate_pdf(
            airline="British Airways",
            title="Long Document",
            content=long_content
        )

        self.assertIsNotNone(buffer)
        self.assertGreater(buffer.getbuffer().nbytes, 1000)

    def test_sanitize_filename(self):
        """Test filename sanitization"""
        # Test invalid characters
        result = self.generator.sanitize_filename("Air<India>.pdf")
        self.assertNotIn("<", result)
        self.assertNotIn(">", result)

        # Test long names
        long_name = "A" * 300 + ".pdf"
        result = self.generator.sanitize_filename(long_name)
        self.assertLessEqual(len(result), 204)  # 200 + .pdf

        # Test empty name
        result = self.generator.sanitize_filename("")
        self.assertEqual(result, "document.pdf")

    def test_pdf_settings(self):
        """Test PDF with different settings"""
        buffer = self.generator.generate_pdf(
            airline="Lufthansa",
            title="Test Document",
            content="Content here",
            page_size="LETTER",
            orientation="landscape",
            font_size=14,
            margin=30
        )

        self.assertIsNotNone(buffer)


class TestTemplateManager(unittest.TestCase):
    """Test the template manager"""

    def setUp(self):
        self.manager = TemplateManager(storage_dir='test_templates')

    def tearDown(self):
        # Clean up test templates
        import shutil
        import os
        if os.path.exists('test_templates'):
            shutil.rmtree('test_templates')

    def test_save_template(self):
        """Test saving a template"""
        template_data = {
            'name': 'Test Template',
            'title': 'Title with {{AIRLINE_NAME}}',
            'content': 'Content here',
            'replacementMode': 'placeholder',
            'originalName': '',
            'caseSensitive': False,
            'settings': {}
        }

        template_id = self.manager.save_template(template_data)
        self.assertIsNotNone(template_id)

    def test_get_template(self):
        """Test retrieving a template"""
        template_data = {
            'name': 'Test Template',
            'title': 'Title',
            'content': 'Content'
        }

        template_id = self.manager.save_template(template_data)
        template = self.manager.get_template(template_id)

        self.assertIsNotNone(template)
        self.assertEqual(template['name'], 'Test Template')
        self.assertEqual(template['title'], 'Title')

    def test_delete_template(self):
        """Test deleting a template"""
        template_data = {'name': 'To Delete', 'title': 'T', 'content': 'C'}
        template_id = self.manager.save_template(template_data)

        success = self.manager.delete_template(template_id)
        self.assertTrue(success)

        # Verify it's deleted
        template = self.manager.get_template(template_id)
        self.assertIsNone(template)

    def test_get_all_templates(self):
        """Test getting all templates"""
        self.manager.save_template({'name': 'T1', 'title': 'Title1', 'content': 'C1'})
        self.manager.save_template({'name': 'T2', 'title': 'Title2', 'content': 'C2'})

        templates = self.manager.get_all_templates()
        self.assertEqual(len(templates), 2)


if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2)
