#!/usr/bin/env python
"""
Initialize Admin Account
One-time setup script to create the initial admin user
Run this after setting up the database
"""

import os
import sys
from getpass import getpass

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from services.models import User
from services.auth_service import AuthService
from config import ADMIN_EMAIL


def init_admin():
    """Initialize the admin account"""
    with app.app_context():
        # Check if admin already exists
        admin_user = User.query.filter_by(email=ADMIN_EMAIL).first()

        if admin_user:
            if admin_user.is_admin:
                print(f"✓ Admin user already exists: {ADMIN_EMAIL}")
                return True
            else:
                print(f"✗ User exists but is not admin: {ADMIN_EMAIL}")
                print("  Please remove or modify this user manually")
                return False

        # Check if users exist at all (only initialize if no users)
        user_count = User.query.count()
        if user_count > 0:
            print("✗ Database already contains users")
            print("  To add an admin, use the admin dashboard or modify manually")
            return False

        print("=" * 60)
        print("Cargo - Admin Account Initialization")
        print("=" * 60)
        print()

        # Try to get admin password from environment
        admin_password = os.environ.get('ADMIN_PASSWORD')

        if not admin_password:
            print("Admin password not found in ADMIN_PASSWORD environment variable")
            print("Please set ADMIN_PASSWORD and try again:")
            print()
            print("  export ADMIN_PASSWORD='your-secure-password'")
            print("  python scripts/init_admin.py")
            print()
            return False

        # Validate password
        valid, msg = AuthService.validate_password(admin_password)
        if not valid:
            print(f"✗ Password validation failed: {msg}")
            return False

        try:
            # Create admin user
            admin = User(
                id=None,  # Will be auto-generated
                email=ADMIN_EMAIL,
                full_name='Administrator',
                password_hash=AuthService.hash_password(admin_password),
                account_status='approved',
                is_admin=True
            )

            db.session.add(admin)
            db.session.commit()

            print("✓ Admin account created successfully")
            print()
            print("Admin Details:")
            print(f"  Email: {ADMIN_EMAIL}")
            print(f"  Status: Approved")
            print(f"  Role: Administrator")
            print()
            print("Next steps:")
            print("  1. Start the application: python app.py")
            print("  2. Navigate to http://localhost:5000/login")
            print("  3. Log in with admin credentials")
            print("  4. Visit /admin to manage users")
            print()

            return True

        except Exception as e:
            db.session.rollback()
            print(f"✗ Failed to create admin account: {str(e)}")
            return False


if __name__ == '__main__':
    success = init_admin()
    sys.exit(0 if success else 1)
