"""
Authentication Decorators
Decorators for protecting routes and enforcing authorization
"""

from functools import wraps
from flask import request, jsonify

from services.auth_service import AuthService
from services.models import User


def get_token_from_request():
    """Extract token from Authorization header or cookies"""
    # Try Authorization header first (Bearer token)
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        return auth_header[7:]

    # Try cookies
    token = request.cookies.get('auth_token')
    if token:
        return token

    return None


def auth_required(f):
    """
    Decorator to require authentication
    Verifies session token and user account status
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = get_token_from_request()

        if not token:
            return jsonify({'error': 'Authentication required'}), 401

        # Verify session and get user
        valid, user = AuthService.verify_session(token)

        if not valid or not user:
            return jsonify({'error': 'Invalid or expired session'}), 401

        # Store user in request context for use in route
        request.current_user = user

        return f(*args, **kwargs)

    return decorated_function


def admin_required(f):
    """
    Decorator to require admin privileges
    Must be used after @auth_required
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if user is authenticated (should be called after auth_required)
        if not hasattr(request, 'current_user'):
            return jsonify({'error': 'Authentication required'}), 401

        user = request.current_user

        # Check if user is admin
        if not user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403

        return f(*args, **kwargs)

    return decorated_function


def get_current_user():
    """Get the current authenticated user from request context"""
    return getattr(request, 'current_user', None)
