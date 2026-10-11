"""
Validation Service
Handles input validation and airline list parsing
"""

import re
import csv
from io import StringIO
from typing import List, Dict


class ValidationService:
    """Service for validating user inputs"""

    def __init__(self):
        self.placeholder = "{{AIRLINE_NAME}}"

    def validate(
        self,
        title: str,
        content: str,
        airlines: List[str],
        replacement_mode: str,
        original_name: str = ''
    ) -> Dict:
        """
        Validate all inputs before generation

        Returns:
            Dictionary with 'valid' boolean and 'errors' list
        """
        errors = []

        # Validate title
        if not title or not title.strip():
            errors.append("Title cannot be empty")

        # Validate content
        if not content or not content.strip():
            errors.append("Content cannot be empty")

        # Validate airlines
        if not airlines or len(airlines) == 0:
            errors.append("Airline list cannot be empty")

        valid_airlines = [a for a in airlines if a.strip()]
        if len(valid_airlines) == 0:
            errors.append("Airline list contains no valid entries")

        # Check for duplicates
        duplicates = self._find_duplicates(airlines)
        if duplicates:
            errors.append(f"Duplicate airlines found: {', '.join(duplicates[:3])}")

        # Mode-specific validation
        if replacement_mode == 'placeholder':
            # Check if placeholder exists
            if self.placeholder not in title and self.placeholder not in content:
                errors.append(f"Placeholder '{self.placeholder}' not found in title or content")
        elif replacement_mode == 'original':
            # Check if original name is provided
            if not original_name or not original_name.strip():
                errors.append("Original airline name is required for original-name mode")
            elif original_name not in title and original_name not in content:
                errors.append(f"Original airline name '{original_name}' not found in title or content")

        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': self._generate_warnings(title, content, airlines)
        }

    def parse_airline_list(self, text: str) -> List[str]:
        """
        Parse airline list from text input
        Supports:
        - One airline per line
        - Comma-separated
        - Semicolon-separated
        - CSV format

        Returns:
            List of airline names
        """
        if not text:
            return []

        airlines = []

        # Check if it looks like simple delimited list (no newlines)
        has_newlines = '\n' in text
        has_commas = ',' in text
        has_semicolons = ';' in text

        # If simple delimited list without newlines, parse directly
        if not has_newlines and (has_commas or has_semicolons):
            # Split by comma or semicolon
            if has_commas:
                parts = text.split(',')
            else:
                parts = text.split(';')

            for part in parts:
                airline = part.strip()
                if airline:
                    airlines.append(airline)
            return airlines

        # Try CSV parsing for more complex formats
        try:
            reader = csv.reader(StringIO(text))

            for row in reader:
                if row:
                    # Take first column if multiple columns
                    airline = row[0].strip()
                    if airline and airline.lower() not in ['airline', 'name']:  # Skip common headers
                        airlines.append(airline)
        except:
            # Fallback: split by delimiters
            text = text.replace(',', '\n')
            text = text.replace(';', '\n')

            lines = text.split('\n')
            for line in lines:
                airline = line.strip()
                if airline:
                    airlines.append(airline)

        # Remove duplicates while preserving order
        seen = set()
        unique_airlines = []
        for airline in airlines:
            if airline not in seen:
                seen.add(airline)
                unique_airlines.append(airline)

        return unique_airlines

    def _find_duplicates(self, airlines: List[str]) -> List[str]:
        """Find duplicate airline names"""
        seen = set()
        duplicates = set()

        for airline in airlines:
            airline_lower = airline.lower().strip()
            if airline_lower in seen:
                duplicates.add(airline)
            seen.add(airline_lower)

        return list(duplicates)

    def _generate_warnings(
        self,
        title: str,
        content: str,
        airlines: List[str]
    ) -> List[str]:
        """Generate warnings for potential issues"""
        warnings = []

        # Check for very long airline lists
        if len(airlines) > 100:
            warnings.append(f"Large airline list ({len(airlines)} entries). Generation may take a while.")

        # Check for very long content
        if len(content) > 10000:
            warnings.append("Content is very long. PDFs may span multiple pages.")

        # Check for special characters that might cause issues
        special_chars = ['<', '>', '&', '"', "'"]
        for char in special_chars:
            if char in content:
                warnings.append("Content contains HTML special characters. They will be escaped in PDFs.")
                break

        return warnings

    def validate_filename(self, filename: str) -> bool:
        """Validate if filename is safe"""
        # Check for invalid characters
        invalid_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
        return not any(char in filename for char in invalid_chars)
