"""
Cargo Database Models
User, Session, and Audit Log models for authentication and access control
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import uuid

db = SQLAlchemy()


class User(db.Model):
    """User account model with authentication and status tracking"""
    __tablename__ = 'users'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    full_name = db.Column(db.String(255), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    # Account status: pending, approved, rejected, revoked, suspended
    account_status = db.Column(db.String(50), default='pending', nullable=False, index=True)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)

    rejected_reason = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    sessions = db.relationship('Session', backref='user', lazy=True, cascade='all, delete-orphan')
    audit_logs_as_target = db.relationship('AuditLog', foreign_keys='AuditLog.target_user_id', backref='target_user', lazy=True)
    audit_logs_as_admin = db.relationship('AuditLog', foreign_keys='AuditLog.admin_id', backref='admin_user', lazy=True)

    def to_dict(self, include_sensitive=False):
        """Convert user to dictionary"""
        data = {
            'id': self.id,
            'email': self.email,
            'full_name': self.full_name,
            'account_status': self.account_status,
            'is_admin': self.is_admin,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
        if include_sensitive and self.account_status == 'rejected':
            data['rejected_reason'] = self.rejected_reason
        return data


class Session(db.Model):
    """User session tokens for authentication"""
    __tablename__ = 'sessions'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False, index=True)
    token = db.Column(db.String(255), unique=True, nullable=False, index=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)

    def is_valid(self):
        """Check if session is still valid"""
        return datetime.utcnow() < self.expires_at

    def to_dict(self):
        """Convert session to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'created_at': self.created_at.isoformat(),
            'expires_at': self.expires_at.isoformat(),
            'is_valid': self.is_valid()
        }


class AuditLog(db.Model):
    """Audit log for administrative actions"""
    __tablename__ = 'audit_logs'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # Action type: created, approved, rejected, revoked, restored, suspended
    action = db.Column(db.String(50), nullable=False, index=True)

    admin_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False, index=True)
    target_user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False, index=True)

    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    details = db.Column(db.Text, nullable=True)
    outcome = db.Column(db.String(50), default='success', nullable=False)  # success, error, etc.

    def to_dict(self):
        """Convert audit log to dictionary"""
        return {
            'id': self.id,
            'action': self.action,
            'admin_id': self.admin_id,
            'admin_email': self.admin_user.email if self.admin_user else None,
            'target_user_id': self.target_user_id,
            'target_email': self.target_user.email if self.target_user else None,
            'timestamp': self.timestamp.isoformat(),
            'details': self.details,
            'outcome': self.outcome
        }
