"""
Security monitoring and audit service for the IBET application.
Provides security event logging, suspicious activity detection, and audit trail functionality.
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from django.utils import timezone
from django.core.cache import cache
from django.db import models
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)

User = get_user_model()


class SecurityEventManager:
    """
    Manager for security events and audit logging.
    """

    # Event types
    EVENT_TYPES = {
        'LOGIN_SUCCESS': 'login_success',
        'LOGIN_FAILED': 'login_failed',
        'LOGOUT': 'logout',
        'OTP_GENERATED': 'otp_generated',
        'OTP_VERIFIED': 'otp_verified',
        'OTP_FAILED': 'otp_failed',
        'WALLET_ACCESS': 'wallet_access',
        'WALLET_DEPOSIT': 'wallet_deposit',
        'WALLET_WITHDRAWAL': 'wallet_withdrawal',
        'WALLET_TRANSFER': 'wallet_transfer',
        'SUSPICIOUS_ACTIVITY': 'suspicious_activity',
        'RATE_LIMIT_EXCEEDED': 'rate_limit_exceeded',
        'UNAUTHORIZED_ACCESS': 'unauthorized_access',
        'PARENT_STUDENT_LINK': 'parent_student_link',
        'FUND_TRANSFER': 'fund_transfer',
        'SECURITY_VIOLATION': 'security_violation'
    }

    @classmethod
    def log_event(cls, event_type: str, user_id: int, details: Dict[str, Any] = None,
                  ip_address: str = None, user_agent: str = None) -> bool:
        """
        Log a security event.

        Args:
            event_type: Type of security event
            user_id: ID of the user associated with the event
            details: Additional details about the event
            ip_address: IP address of the request
            user_agent: User agent string

        Returns:
            bool: True if logged successfully
        """
        try:
            # Create event data
            event_data = {
                'event_type': event_type,
                'user_id': user_id,
                'details': details or {},
                'ip_address': ip_address,
                'user_agent': user_agent,
                'timestamp': timezone.now().isoformat(),
                'severity': cls._get_event_severity(event_type)
            }

            # Store in cache for quick access (24 hours)
            cache_key = f"security_event_{user_id}_{event_type}_{int(timezone.now().timestamp())}"
            cache.set(cache_key, event_data, timeout=86400)  # 24 hours

            # Log to system logger
            logger.info(f"Security Event: {event_type} - User: {user_id} - Details: {details}")

            # Store in database if available
            try:
                cls._store_event_in_db(event_data)
            except Exception as db_error:
                logger.warning(f"Failed to store security event in database: {db_error}")

            return True

        except Exception as e:
            logger.error(f"Failed to log security event: {e}")
            return False

    @classmethod
    def _get_event_severity(cls, event_type: str) -> str:
        """Get severity level for event type."""
        severity_map = {
            'LOGIN_SUCCESS': 'INFO',
            'LOGIN_FAILED': 'WARNING',
            'LOGOUT': 'INFO',
            'OTP_GENERATED': 'INFO',
            'OTP_VERIFIED': 'INFO',
            'OTP_FAILED': 'WARNING',
            'WALLET_ACCESS': 'INFO',
            'WALLET_DEPOSIT': 'INFO',
            'WALLET_WITHDRAWAL': 'INFO',
            'WALLET_TRANSFER': 'INFO',
            'SUSPICIOUS_ACTIVITY': 'CRITICAL',
            'RATE_LIMIT_EXCEEDED': 'WARNING',
            'UNAUTHORIZED_ACCESS': 'CRITICAL',
            'PARENT_STUDENT_LINK': 'INFO',
            'FUND_TRANSFER': 'WARNING',
            'SECURITY_VIOLATION': 'CRITICAL'
        }
        return severity_map.get(event_type, 'INFO')

    @classmethod
    def _store_event_in_db(cls, event_data: Dict[str, Any]):
        """Store event in database for long-term storage."""
        # This would typically store in a SecurityEvent model
        # For now, we'll just log it
        logger.debug(f"Would store security event in database: {event_data}")

    @classmethod
    def get_user_events(cls, user_id: int, hours: int = 24) -> List[Dict[str, Any]]:
        """
        Get security events for a specific user within the last N hours.

        Args:
            user_id: User ID to get events for
            hours: Number of hours to look back

        Returns:
            List of security events
        """
        events = []
        cutoff_time = timezone.now() - timedelta(hours=hours)

        # Get events from cache (this is a simplified implementation)
        # In production, you'd query the database
        cache_pattern = f"security_event_{user_id}_*"
        # Note: Django cache doesn't support pattern matching easily
        # This would need a more sophisticated implementation

        return events

    @classmethod
    def detect_suspicious_activity(cls, user_id: int, activity_type: str,
                                 threshold: int = 5, time_window_minutes: int = 10) -> bool:
        """
        Detect if user activity appears suspicious based on frequency.

        Args:
            user_id: User ID to check
            activity_type: Type of activity to monitor
            threshold: Number of events that trigger suspicion
            time_window_minutes: Time window to check

        Returns:
            bool: True if suspicious activity detected
        """
        cache_key = f"suspicious_{user_id}_{activity_type}"

        # Get current count
        current_count = cache.get(cache_key, 0)

        if current_count >= threshold:
            # Log suspicious activity
            cls.log_event(
                cls.EVENT_TYPES['SUSPICIOUS_ACTIVITY'],
                user_id,
                {
                    'activity_type': activity_type,
                    'count': current_count,
                    'threshold': threshold,
                    'time_window_minutes': time_window_minutes
                }
            )
            return True

        # Increment counter
        cache.set(cache_key, current_count + 1, timeout=time_window_minutes * 60)
        return False

    @classmethod
    def get_security_summary(cls, hours: int = 24) -> Dict[str, Any]:
        """
        Get a summary of security events for the last N hours.

        Args:
            hours: Number of hours to summarize

        Returns:
            Dict with security summary
        """
        # This would typically aggregate from database
        # For now, return a basic summary
        return {
            'total_events': 0,
            'critical_events': 0,
            'warning_events': 0,
            'info_events': 0,
            'most_active_users': [],
            'common_event_types': {}
        }


class AuditService:
    """
    Service for auditing sensitive operations and maintaining audit trails.
    """

    @classmethod
    def audit_wallet_operation(cls, user_id: int, operation: str, amount: float,
                             details: Dict[str, Any] = None) -> bool:
        """
        Audit a wallet operation.

        Args:
            user_id: User performing the operation
            operation: Type of operation (e.g., 'transfer', 'withdrawal')
            amount: Amount involved
            details: Additional details

        Returns:
            bool: True if audited successfully
        """
        try:
            audit_data = {
                'operation': operation,
                'amount': amount,
                'details': details or {}
            }

            SecurityEventManager.log_event(
                SecurityEventManager.EVENT_TYPES['FUND_TRANSFER'],
                user_id,
                audit_data
            )

            logger.info(f"Wallet operation audited: {operation} - User: {user_id} - Amount: {amount}")
            return True

        except Exception as e:
            logger.error(f"Failed to audit wallet operation: {e}")
            return False

    @classmethod
    def audit_parent_student_link(cls, parent_id: int, student_id: int,
                                operation: str, details: Dict[str, Any] = None) -> bool:
        """
        Audit parent-student linking operations.

        Args:
            parent_id: Parent user ID
            student_id: Student user ID
            operation: Type of operation (e.g., 'link', 'unlink', 'access')
            details: Additional details

        Returns:
            bool: True if audited successfully
        """
        try:
            audit_data = {
                'operation': operation,
                'student_id': student_id,
                'details': details or {}
            }

            SecurityEventManager.log_event(
                SecurityEventManager.EVENT_TYPES['PARENT_STUDENT_LINK'],
                parent_id,
                audit_data
            )

            logger.info(f"Parent-student operation audited: {operation} - Parent: {parent_id} - Student: {student_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to audit parent-student operation: {e}")
            return False

    @classmethod
    def audit_otp_operation(cls, user_id: int, operation: str, success: bool,
                          details: Dict[str, Any] = None) -> bool:
        """
        Audit OTP operations.

        Args:
            user_id: User performing the operation
            operation: Type of operation (e.g., 'generate', 'verify')
            success: Whether the operation was successful
            details: Additional details

        Returns:
            bool: True if audited successfully
        """
        try:
            event_type = SecurityEventManager.EVENT_TYPES['OTP_VERIFIED'] if success else SecurityEventManager.EVENT_TYPES['OTP_FAILED']

            audit_data = {
                'operation': operation,
                'success': success,
                'details': details or {}
            }

            SecurityEventManager.log_event(
                event_type,
                user_id,
                audit_data
            )

            logger.info(f"OTP operation audited: {operation} - User: {user_id} - Success: {success}")
            return True

        except Exception as e:
            logger.error(f"Failed to audit OTP operation: {e}")
            return False


class SecurityMonitor:
    """
    Monitor for real-time security threat detection and response.
    """

    @classmethod
    def check_failed_logins(cls, user_id: int, max_attempts: int = 5,
                          time_window_minutes: int = 15) -> bool:
        """
        Check for excessive failed login attempts.

        Args:
            user_id: User ID to check
            max_attempts: Maximum allowed failed attempts
            time_window_minutes: Time window to check

        Returns:
            bool: True if suspicious activity detected
        """
        return SecurityEventManager.detect_suspicious_activity(
            user_id, 'login_failed', max_attempts, time_window_minutes
        )

    @classmethod
    def check_otp_failures(cls, user_id: int, max_attempts: int = 3,
                         time_window_minutes: int = 10) -> bool:
        """
        Check for excessive OTP verification failures.

        Args:
            user_id: User ID to check
            max_attempts: Maximum allowed failed attempts
            time_window_minutes: Time window to check

        Returns:
            bool: True if suspicious activity detected
        """
        return SecurityEventManager.detect_suspicious_activity(
            user_id, 'otp_failed', max_attempts, time_window_minutes
        )

    @classmethod
    def check_rate_limit_violations(cls, user_id: int, max_violations: int = 10,
                                  time_window_minutes: int = 60) -> bool:
        """
        Check for excessive rate limit violations.

        Args:
            user_id: User ID to check
            max_violations: Maximum allowed violations
            time_window_minutes: Time window to check

        Returns:
            bool: True if suspicious activity detected
        """
        return SecurityEventManager.detect_suspicious_activity(
            user_id, 'rate_limit_exceeded', max_violations, time_window_minutes
        )

    @classmethod
    def get_user_risk_score(cls, user_id: int, hours: int = 24) -> float:
        """
        Calculate a risk score for a user based on recent activity.

        Args:
            user_id: User ID to calculate risk for
            hours: Hours to look back

        Returns:
            float: Risk score (0.0 to 1.0)
        """
        # This is a simplified implementation
        # In production, this would use more sophisticated algorithms
        try:
            events = SecurityEventManager.get_user_events(user_id, hours)

            # Count different types of events
            critical_count = sum(1 for event in events if event.get('severity') == 'CRITICAL')
            warning_count = sum(1 for event in events if event.get('severity') == 'WARNING')

            # Calculate risk score
            total_events = len(events)
            if total_events == 0:
                return 0.0

            risk_score = (critical_count * 1.0 + warning_count * 0.5) / total_events
            return min(risk_score, 1.0)  # Cap at 1.0

        except Exception as e:
            logger.error(f"Failed to calculate risk score for user {user_id}: {e}")
            return 0.0
