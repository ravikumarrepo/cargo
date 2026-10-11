"""
Authentication Service
Handles user registration, login, and session management
"""

from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import uuid
import re

from services.models import db, User, Session


class AuthService:
    """Service for authentication and session management"""

    # Password requirements
    MIN_PASSWORD_LENGTH = 8

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using werkzeug's built-in bcrypt"""
        return generate_password_hash(password, method='pbkdf2:sha256')

    @staticmethod
    def verify_password(password_hash: str, password: str) -> bool:
        """Verify a password against its hash"""
        return check_password_hash(password_hash, password)

    @staticmethod
    def validate_email(email: str) -> tuple[bool, str]:
        """Validate email format"""
        email = email.strip()
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email):
            return False, "Invalid email format"
        if len(email) > 255:
            return False, "Email is too long"
        return True, ""

    @staticmethod
    def validate_password(password: str) -> tuple[bool, str]:
        """Validate password strength"""
        if len(password) < AuthService.MIN_PASSWORD_LENGTH:
            return False, f"Password must be at least {AuthService.MIN_PASSWORD_LENGTH} characters"
        if not any(c.isupper() for c in password):
            return False, "Password must contain at least one uppercase letter"
        if not any(c.isdigit() for c in password):
            return False, "Password must contain at least one digit"
        return True, ""

    @staticmethod
    def validate_full_name(name: str) -> tuple[bool, str]:
        """Validate full name"""
        name = name.strip()
        if not name:
            return False, "Full name is required"
        if len(name) < 2:
            return False, "Full name must be at least 2 characters"
        if len(name) > 255:
            return False, "Full name is too long"
        return True, ""

    @staticmethod
    def register_user(email: str, full_name: str, password: str, confirm_password: str) -> tuple[bool, str, User | None]:
        """
        Register a new user

        Args:
            email: User email
            full_name: User full name
            password: User password
            confirm_password: Password confirmation

        Returns:
            Tuple of (success, message, user)
        """
        # Validate inputs
        email = email.strip()
        full_name = full_name.strip()

        # Validate email
        valid, msg = AuthService.validate_email(email)
        if not valid:
            return False, msg, None

        # Check if email already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return False, "Email already registered", None

        # Validate full name
        valid, msg = AuthService.validate_full_name(full_name)
        if not valid:
            return False, msg, None

        # Validate passwords match
        if password != confirm_password:
            return False, "Passwords do not match", None

        # Validate password strength
        valid, msg = AuthService.validate_password(password)
        if not valid:
            return False, msg, None

        try:
            # Create new user with pending status
            new_user = User(
                email=email,
                full_name=full_name,
                password_hash=AuthService.hash_password(password),
                account_status='pending',
                is_admin=False
            )

            db.session.add(new_user)
            db.session.commit()

            return True, "Registration successful. Awaiting administrator approval.", new_user
        except Exception as e:
            db.session.rollback()
            return False, f"Registration failed: {str(e)}", None

    @staticmethod
    def authenticate(email: str, password: str) -> tuple[bool, str, Session | None, User | None]:
        """
        Authenticate a user and create a session

        Args:
            email: User email
            password: User password

        Returns:
            Tuple of (success, message, session, user)
        """
        email = email.strip()

        try:
            # Find user by email
            user = User.query.filter_by(email=email).first()

            if not user:
                return False, "Invalid email or password", None, None

            # Verify password
            if not AuthService.verify_password(user.password_hash, password):
                return False, "Invalid email or password", None, None

            # Check account status
            if user.account_status == 'pending':
                return False, "Account is pending administrator approval", None, user
            elif user.account_status == 'rejected':
                return False, "Registration was declined", None, user
            elif user.account_status == 'revoked':
                return False, "Account access has been revoked", None, user
            elif user.account_status == 'suspended':
                return False, "Account is temporarily suspended", None, user
            elif user.account_status != 'approved':
                return False, f"Account status: {user.account_status}", None, user

            # Create new session
            from config import SESSION_TIMEOUT
            token = str(uuid.uuid4())
            session = Session(
                user_id=user.id,
                token=token,
                expires_at=datetime.utcnow() + timedelta(seconds=SESSION_TIMEOUT)
            )

            db.session.add(session)
            db.session.commit()

            return True, "Login successful", session, user

        except Exception as e:
            db.session.rollback()
            return False, f"Login failed: {str(e)}", None, None

    @staticmethod
    def verify_session(token: str) -> tuple[bool, User | None]:
        """
        Verify a session token and return the user

        Args:
            token: Session token

        Returns:
            Tuple of (valid, user)
        """
        try:
            session = Session.query.filter_by(token=token).first()

            if not session:
                return False, None

            # Check if session is expired
            if not session.is_valid():
                return False, None

            # Check user account status
            user = session.user

            if user.account_status != 'approved':
                return False, None

            return True, user

        except Exception as e:
            return False, None

    @staticmethod
    def revoke_user_sessions(user_id: str) -> bool:
        """
        Revoke all sessions for a user

        Args:
            user_id: User ID

        Returns:
            Success status
        """
        try:
            Session.query.filter_by(user_id=user_id).delete()
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            return False

    @staticmethod
    def logout(token: str) -> bool:
        """
        Logout a user by deleting their session

        Args:
            token: Session token

        Returns:
            Success status
        """
        try:
            session = Session.query.filter_by(token=token).first()
            if session:
                db.session.delete(session)
                db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            return False

    @staticmethod
    def get_user_by_id(user_id: str) -> User | None:
        """Get a user by ID"""
        return User.query.get(user_id)

    @staticmethod
    def get_user_by_email(email: str) -> User | None:
        """Get a user by email"""
        return User.query.filter_by(email=email).first()
