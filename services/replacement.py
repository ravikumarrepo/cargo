"""
Replacement Service
Handles deterministic text replacement logic
"""

import re
from typing import Dict, List, Optional


class ReplacementService:
    """Service for exact string replacement operations"""

    def __init__(self):
        self.placeholder = "{{AIRLINE_NAME}}"

    def replace_text(
        self,
        text: str,
        target_airline: str,
        replacement_mode: str = 'placeholder',
        original_name: str = '',
        case_sensitive: bool = False
    ) -> tuple[str, int]:
        """
        Replace airline name in text

        Args:
            text: Original text
            target_airline: Airline name to insert
            replacement_mode: 'placeholder' or 'original'
            original_name: Original airline name (for 'original' mode)
            case_sensitive: Whether to match case-sensitively

        Returns:
            Tuple of (replaced_text, replacement_count)
        """
        if not text:
            return text, 0

        if replacement_mode == 'placeholder':
            # Replace placeholder
            count = text.count(self.placeholder)
            replaced = text.replace(self.placeholder, target_airline)
            return replaced, count
        else:
            # Replace original airline name
            if not original_name:
                return text, 0

            if case_sensitive:
                # Case-sensitive replacement
                count = text.count(original_name)
                replaced = text.replace(original_name, target_airline)
            else:
                # Case-insensitive replacement
                pattern = re.compile(re.escape(original_name), re.IGNORECASE)
                matches = pattern.findall(text)
                count = len(matches)
                replaced = pattern.sub(target_airline, text)

            return replaced, count

    def generate_preview(
        self,
        title: str,
        content: str,
        airline: str,
        replacement_mode: str = 'placeholder',
        original_name: str = '',
        case_sensitive: bool = False
    ) -> Dict:
        """Generate preview for a single airline"""

        title_replaced, title_count = self.replace_text(
            title, airline, replacement_mode, original_name, case_sensitive
        )
        content_replaced, content_count = self.replace_text(
            content, airline, replacement_mode, original_name, case_sensitive
        )

        total_replacements = title_count + content_count

        # Check for unresolved placeholders
        has_placeholder_in_title = self.placeholder in title_replaced
        has_placeholder_in_content = self.placeholder in content_replaced

        return {
            'airline': airline,
            'originalTitle': title,
            'generatedTitle': title_replaced,
            'originalContent': content,
            'generatedContent': content_replaced,
            'titleReplacements': title_count,
            'contentReplacements': content_count,
            'totalReplacements': total_replacements,
            'hasUnresolvedPlaceholder': has_placeholder_in_title or has_placeholder_in_content,
            'warning': self._generate_warning(
                title_count, content_count,
                has_placeholder_in_title, has_placeholder_in_content
            )
        }

    def generate_all(
        self,
        title: str,
        content: str,
        airlines: List[str],
        replacement_mode: str = 'placeholder',
        original_name: str = '',
        case_sensitive: bool = False
    ) -> List[Dict]:
        """Generate content for all airlines"""

        results = []

        for airline in airlines:
            if not airline.strip():
                continue

            title_replaced, title_count = self.replace_text(
                title, airline, replacement_mode, original_name, case_sensitive
            )
            content_replaced, content_count = self.replace_text(
                content, airline, replacement_mode, original_name, case_sensitive
            )

            results.append({
                'airline': airline,
                'generatedTitle': title_replaced,
                'generatedContent': content_replaced,
                'titleReplacements': title_count,
                'contentReplacements': content_count,
                'totalReplacements': title_count + content_count
            })

        return results

    def _generate_warning(
        self,
        title_count: int,
        content_count: int,
        has_placeholder_title: bool,
        has_placeholder_content: bool
    ) -> Optional[str]:
        """Generate warning message if needed"""

        if has_placeholder_title or has_placeholder_content:
            locations = []
            if has_placeholder_title:
                locations.append('title')
            if has_placeholder_content:
                locations.append('content')
            return f"Unresolved placeholder found in {' and '.join(locations)}"

        if title_count == 0 and content_count == 0:
            return "No replacements made. Check your placeholder or original airline name."

        return None
