"""
Cargo Configuration
Environment and settings for the application
"""

import os

# Database Configuration
DATABASE_URL = os.environ.get('DATABASE_URL')

# Flask Configuration
DEBUG = os.environ.get('FLASK_DEBUG', 'False') == 'True'

SECRET_KEY = os.environ.get('SECRET_KEY')
if not SECRET_KEY:
    if DEBUG or not DATABASE_URL:
        # Local development only
        SECRET_KEY = 'cargo-dev-key-change-in-production'
    else:
        # In production with a real database, refuse to start with a
        # predictable key — sessions and password resets are signed with it.
        raise RuntimeError(
            "SECRET_KEY must be set in the environment when running "
            "with a production database."
        )

# File Upload Configuration
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'temp')
GENERATED_FOLDER = os.path.join(os.path.dirname(__file__), 'generated_pdfs')

# Ensure directories exist
if os.environ.get("VERCEL"):
    UPLOAD_FOLDER = "/tmp/cargo"
    GENERATED_FOLDER = "/tmp/cargo/generated_pdfs"
    TEMPLATES_FOLDER = "/tmp/cargo/templates_data"
else:
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "temp")
    GENERATED_FOLDER = os.path.join(BASE_DIR, "generated_pdfs")
    TEMPLATES_FOLDER = os.path.join(BASE_DIR, "templates_data")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(GENERATED_FOLDER, exist_ok=True)
os.makedirs(TEMPLATES_FOLDER, exist_ok=True)

# Template Storage
TEMPLATES_FOLDER = os.path.join(os.path.dirname(__file__), 'templates_data')
os.makedirs(TEMPLATES_FOLDER, exist_ok=True)

# If DATABASE_URL not set, use SQLite fallback (for local development)
if not DATABASE_URL:
    DATABASE_URL = 'sqlite:///' + os.path.join(os.path.dirname(__file__), 'cargo.db')
else:
    # Convert PostgreSQL URL format if needed (Neon/Heroku style)
    if DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

SQLALCHEMY_DATABASE_URI = DATABASE_URL
SQLALCHEMY_TRACK_MODIFICATIONS = False

# Connection pool resilience
# - pool_pre_ping: validates connections before use, replacing dead ones
#   silently (essential for Neon, which closes idle connections)
# - pool_recycle: proactively rotate connections before the server drops them
if DATABASE_URL.startswith('postgresql'):
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': int(os.environ.get('DB_POOL_RECYCLE', 280)),
        'pool_size': int(os.environ.get('DB_POOL_SIZE', 10)),
        'max_overflow': int(os.environ.get('DB_MAX_OVERFLOW', 5)),
        'pool_timeout': int(os.environ.get('DB_POOL_TIMEOUT', 30)),
        'connect_args': {
            'connect_timeout': int(os.environ.get('DB_CONNECT_TIMEOUT', 15)),
            'application_name': 'cargo-pdf-generator',
        },
    }
else:
    # SQLite needs no pooling
    SQLALCHEMY_ENGINE_OPTIONS = {}

# Authentication Configuration
SESSION_TIMEOUT = int(os.environ.get('SESSION_TIMEOUT', 28800))  # 8 hours (extended from 15 min)
REFRESH_TOKEN_EXPIRY = int(os.environ.get('REFRESH_TOKEN_EXPIRY', 604800))  # 7 days
LOGIN_RATE_LIMIT = os.environ.get('LOGIN_RATE_LIMIT', '5/minute')  # Max 5 attempts per minute per email

# Admin Configuration
ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'dmtoravi@gmail.com')

# Logging
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
