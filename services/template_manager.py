"""
Template Manager Service
Handles template persistence using JSON files
"""

import json
import os
import uuid
from datetime import datetime
from typing import Dict, List, Optional


class TemplateManager:
    """Service for managing content templates"""

    def __init__(self, storage_dir: str = 'templates_data'):
        self.storage_dir = storage_dir
        os.makedirs(self.storage_dir, exist_ok=True)
        self.index_file = os.path.join(self.storage_dir, 'index.json')
        self._ensure_index()

    def _ensure_index(self):
        """Ensure index file exists"""
        if not os.path.exists(self.index_file):
            self._save_index([])

    def _load_index(self) -> List[Dict]:
        """Load template index"""
        try:
            with open(self.index_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []

    def _save_index(self, index: List[Dict]):
        """Save template index"""
        with open(self.index_file, 'w', encoding='utf-8') as f:
            json.dump(index, f, indent=2, ensure_ascii=False)

    def save_template(self, template_data: Dict) -> str:
        """
        Save a new template

        Args:
            template_data: Dictionary containing template information

        Returns:
            Template ID
        """
        template_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()

        # Create template object
        template = {
            'id': template_id,
            'name': template_data.get('name', 'Untitled Template'),
            'title': template_data.get('title', ''),
            'content': template_data.get('content', ''),
            'replacementMode': template_data.get('replacementMode', 'placeholder'),
            'originalName': template_data.get('originalName', ''),
            'caseSensitive': template_data.get('caseSensitive', False),
            'settings': template_data.get('settings', {}),
            'createdAt': timestamp,
            'updatedAt': timestamp
        }

        # Save template file
        template_file = os.path.join(self.storage_dir, f'{template_id}.json')
        with open(template_file, 'w', encoding='utf-8') as f:
            json.dump(template, f, indent=2, ensure_ascii=False)

        # Update index
        index = self._load_index()
        index.append({
            'id': template_id,
            'name': template['name'],
            'createdAt': timestamp,
            'updatedAt': timestamp
        })
        self._save_index(index)

        return template_id

    def get_template(self, template_id: str) -> Optional[Dict]:
        """Get a specific template by ID"""
        template_file = os.path.join(self.storage_dir, f'{template_id}.json')

        if not os.path.exists(template_file):
            return None

        try:
            with open(template_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return None

    def get_all_templates(self) -> List[Dict]:
        """Get all template summaries"""
        return self._load_index()

    def update_template(self, template_id: str, template_data: Dict) -> bool:
        """Update an existing template"""
        template = self.get_template(template_id)

        if not template:
            return False

        # Update fields
        template['name'] = template_data.get('name', template['name'])
        template['title'] = template_data.get('title', template['title'])
        template['content'] = template_data.get('content', template['content'])
        template['replacementMode'] = template_data.get('replacementMode', template['replacementMode'])
        template['originalName'] = template_data.get('originalName', template['originalName'])
        template['caseSensitive'] = template_data.get('caseSensitive', template['caseSensitive'])
        template['settings'] = template_data.get('settings', template['settings'])
        template['updatedAt'] = datetime.now().isoformat()

        # Save template
        template_file = os.path.join(self.storage_dir, f'{template_id}.json')
        with open(template_file, 'w', encoding='utf-8') as f:
            json.dump(template, f, indent=2, ensure_ascii=False)

        # Update index
        index = self._load_index()
        for item in index:
            if item['id'] == template_id:
                item['name'] = template['name']
                item['updatedAt'] = template['updatedAt']
                break
        self._save_index(index)

        return True

    def delete_template(self, template_id: str) -> bool:
        """Delete a template"""
        template_file = os.path.join(self.storage_dir, f'{template_id}.json')

        if not os.path.exists(template_file):
            return False

        # Delete file
        os.remove(template_file)

        # Update index
        index = self._load_index()
        index = [item for item in index if item['id'] != template_id]
        self._save_index(index)

        return True

    def duplicate_template(self, template_id: str, new_name: str = None) -> Optional[str]:
        """Duplicate an existing template"""
        template = self.get_template(template_id)

        if not template:
            return None

        # Create new template data
        new_template_data = {
            'name': new_name or f"{template['name']} (Copy)",
            'title': template['title'],
            'content': template['content'],
            'replacementMode': template['replacementMode'],
            'originalName': template['originalName'],
            'caseSensitive': template['caseSensitive'],
            'settings': template['settings']
        }

        return self.save_template(new_template_data)
