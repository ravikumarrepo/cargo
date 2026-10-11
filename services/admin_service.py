"""
Admin Service
Handles user management and approval workflows
"""

from datetime import datetime
from sqlalchemy import and_

from services.models import db, User, AuditLog


class AdminService:
    """Service for administrative operations"""

    @staticmethod
    def approve_user(user_id: str, admin_id: str) -> tuple[bool, str]:
        """
        Approve a pending user

        Args:
            user_id: ID of user to approve
            admin_id: ID of admin performing action

        Returns:
            Tuple of (success, message)
        """
        try:
            user = User.query.get(user_id)
            if not user:
                return False, "User not found"

            # Log the action
            audit = AuditLog(
                action='approved',
                admin_id=admin_id,
                target_user_id=user_id,
                details=f"User {user.email} approved",
                outcome='success'
            )

            user.account_status = 'approved'
            user.updated_at = datetime.utcnow()

            db.session.add(audit)
            db.session.commit()

            return True, f"User {user.email} approved"
        except Exception as e:
            db.session.rollback()
            return False, f"Approval failed: {str(e)}"

    @staticmethod
    def reject_user(user_id: str, admin_id: str, reason: str = "") -> tuple[bool, str]:
        """
        Reject a pending user

        Args:
            user_id: ID of user to reject
            admin_id: ID of admin performing action
            reason: Reason for rejection

        Returns:
            Tuple of (success, message)
        """
        try:
            user = User.query.get(user_id)
            if not user:
                return False, "User not found"

            # Log the action
            audit = AuditLog(
                action='rejected',
                admin_id=admin_id,
                target_user_id=user_id,
                details=f"User {user.email} rejected. Reason: {reason}",
                outcome='success'
            )

            user.account_status = 'rejected'
            user.rejected_reason = reason
            user.updated_at = datetime.utcnow()

            db.session.add(audit)
            db.session.commit()

            return True, f"User {user.email} rejected"
        except Exception as e:
            db.session.rollback()
            return False, f"Rejection failed: {str(e)}"

    @staticmethod
    def revoke_access(user_id: str, admin_id: str) -> tuple[bool, str]:
        """
        Revoke access from an approved user

        Args:
            user_id: ID of user to revoke
            admin_id: ID of admin performing action

        Returns:
            Tuple of (success, message)
        """
        try:
            user = User.query.get(user_id)
            if not user:
                return False, "User not found"

            # Log the action
            audit = AuditLog(
                action='revoked',
                admin_id=admin_id,
                target_user_id=user_id,
                details=f"User {user.email} access revoked",
                outcome='success'
            )

            user.account_status = 'revoked'
            user.updated_at = datetime.utcnow()

            # Invalidate all user sessions
            from services.auth_service import AuthService
            AuthService.revoke_user_sessions(user_id)

            db.session.add(audit)
            db.session.commit()

            return True, f"User {user.email} access revoked"
        except Exception as e:
            db.session.rollback()
            return False, f"Revocation failed: {str(e)}"

    @staticmethod
    def restore_access(user_id: str, admin_id: str) -> tuple[bool, str]:
        """
        Restore access to a revoked or suspended user

        Args:
            user_id: ID of user to restore
            admin_id: ID of admin performing action

        Returns:
            Tuple of (success, message)
        """
        try:
            user = User.query.get(user_id)
            if not user:
                return False, "User not found"

            if user.account_status not in ['revoked', 'suspended']:
                return False, f"Can only restore revoked or suspended users, current status: {user.account_status}"

            # Log the action
            audit = AuditLog(
                action='restored',
                admin_id=admin_id,
                target_user_id=user_id,
                details=f"User {user.email} access restored",
                outcome='success'
            )

            user.account_status = 'approved'
            user.updated_at = datetime.utcnow()

            db.session.add(audit)
            db.session.commit()

            return True, f"User {user.email} access restored"
        except Exception as e:
            db.session.rollback()
            return False, f"Restoration failed: {str(e)}"

    @staticmethod
    def suspend_user(user_id: str, admin_id: str) -> tuple[bool, str]:
        """
        Suspend a user account

        Args:
            user_id: ID of user to suspend
            admin_id: ID of admin performing action

        Returns:
            Tuple of (success, message)
        """
        try:
            user = User.query.get(user_id)
            if not user:
                return False, "User not found"

            # Log the action
            audit = AuditLog(
                action='suspended',
                admin_id=admin_id,
                target_user_id=user_id,
                details=f"User {user.email} suspended",
                outcome='success'
            )

            user.account_status = 'suspended'
            user.updated_at = datetime.utcnow()

            # Invalidate all user sessions
            from services.auth_service import AuthService
            AuthService.revoke_user_sessions(user_id)

            db.session.add(audit)
            db.session.commit()

            return True, f"User {user.email} suspended"
        except Exception as e:
            db.session.rollback()
            return False, f"Suspension failed: {str(e)}"

    @staticmethod
    def logout_user_sessions(user_id: str, admin_id: str) -> tuple[bool, str]:
        """
        Force logout all sessions for a user

        Args:
            user_id: ID of user to logout
            admin_id: ID of admin performing action

        Returns:
            Tuple of (success, message)
        """
        try:
            user = User.query.get(user_id)
            if not user:
                return False, "User not found"

            # Log the action
            audit = AuditLog(
                action='logged_out',
                admin_id=admin_id,
                target_user_id=user_id,
                details=f"User {user.email} sessions terminated",
                outcome='success'
            )

            from services.auth_service import AuthService
            AuthService.revoke_user_sessions(user_id)

            db.session.add(audit)
            db.session.commit()

            return True, f"User {user.email} sessions terminated"
        except Exception as e:
            db.session.rollback()
            return False, f"Session termination failed: {str(e)}"

    @staticmethod
    def get_user_stats() -> dict:
        """Get user statistics"""
        try:
            total = User.query.count()
            pending = User.query.filter_by(account_status='pending').count()
            approved = User.query.filter_by(account_status='approved').count()
            rejected = User.query.filter_by(account_status='rejected').count()
            revoked = User.query.filter_by(account_status='revoked').count()
            suspended = User.query.filter_by(account_status='suspended').count()

            return {
                'total': total,
                'pending': pending,
                'approved': approved,
                'rejected': rejected,
                'revoked': revoked,
                'suspended': suspended
            }
        except Exception as e:
            return {'error': str(e)}

    @staticmethod
    def get_users(status: str = None, search: str = None, limit: int = 20, offset: int = 0) -> tuple[list, int]:
        """
        Get users with optional filtering

        Args:
            status: Filter by account status
            search: Search by email or name
            limit: Results per page
            offset: Page offset

        Returns:
            Tuple of (users_list, total_count)
        """
        try:
            query = User.query

            if status:
                query = query.filter_by(account_status=status)

            if search:
                search_term = f"%{search}%"
                query = query.filter(
                    (User.email.ilike(search_term)) | (User.full_name.ilike(search_term))
                )

            total = query.count()
            users = query.order_by(User.created_at.desc()).limit(limit).offset(offset).all()

            return [u.to_dict() for u in users], total
        except Exception as e:
            return [], 0

    @staticmethod
    def get_user_history(user_id: str, limit: int = 50) -> list:
        """Get audit log for a specific user"""
        try:
            logs = AuditLog.query.filter_by(target_user_id=user_id).order_by(
                AuditLog.timestamp.desc()
            ).limit(limit).all()

            return [log.to_dict() for log in logs]
        except Exception as e:
            return []

    @staticmethod
    def get_audit_log(action: str = None, limit: int = 50, offset: int = 0) -> tuple[list, int]:
        """
        Get audit log entries

        Args:
            action: Filter by action type
            limit: Results per page
            offset: Page offset

        Returns:
            Tuple of (logs_list, total_count)
        """
        try:
            query = AuditLog.query

            if action:
                query = query.filter_by(action=action)

            total = query.count()
            logs = query.order_by(AuditLog.timestamp.desc()).limit(limit).offset(offset).all()

            return [log.to_dict() for log in logs], total
        except Exception as e:
            return [], 0

    @staticmethod
    def search_users(query_text: str, status: str = None, limit: int = 20) -> list:
        """
        Search users by email or name

        Args:
            query_text: Search term
            status: Filter by account status
            limit: Result limit

        Returns:
            List of matching users
        """
        try:
            query = User.query

            if query_text:
                search_term = f"%{query_text}%"
                query = query.filter(
                    (User.email.ilike(search_term)) | (User.full_name.ilike(search_term))
                )

            if status:
                query = query.filter_by(account_status=status)

            users = query.order_by(User.created_at.desc()).limit(limit).all()

            return [u.to_dict() for u in users]
        except Exception as e:
            return []
