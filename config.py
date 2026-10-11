"""
Cargo Configuration
Environment and settings for the application
"""

import os
from datetime import timedelta

# Flask Configuration
SECRET_KEY = os.environ.get('SECRET_KEY', 'cargo-dev-key-change-in-production')
DEBUG = os.environ.get('FLASK_DEBUG', 'False') == 'True'

# File Upload Configuration
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'temp')
GENERATED_FOLDER = os.path.join(os.path.dirname(__file__), 'generated_pdfs')

# Ensure directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(GENERATED_FOLDER, exist_ok=True)

# Template Storage
TEMPLATES_FOLDER = os.path.join(os.path.dirname(__file__), 'templates_data')
os.makedirs(TEMPLATES_FOLDER, exist_ok=True)

# Database Configuration
DATABASE_URL = os.environ.get('DATABASE_URL')

# If DATABASE_URL not set, use SQLite fallback (for local development)
if not DATABASE_URL:
    DATABASE_URL = 'sqlite:///' + os.path.join(os.path.dirname(__file__), 'cargo.db')
else:
    # Convert PostgreSQL URL format if needed (Neon uses psycopg2)
    if DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

SQLALCHEMY_DATABASE_URI = DATABASE_URL
SQLALCHEMY_TRACK_MODIFICATIONS = False

# Authentication Configuration
SESSION_TIMEOUT = int(os.environ.get('SESSION_TIMEOUT', 28800))  # 8 hours (extended from 15 min)
REFRESH_TOKEN_EXPIRY = int(os.environ.get('REFRESH_TOKEN_EXPIRY', 604800))  # 7 days
LOGIN_RATE_LIMIT = os.environ.get('LOGIN_RATE_LIMIT', '5/minute')  # Max 5 attempts per minute per email

# Admin Configuration
ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'dmtoravi@gmail.com')

# Logging
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
