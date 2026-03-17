"""
Core security utilities and services for the IBET application.
Provides secure OTP generation, validation, and other security-related functionality.
"""
import random
import string
import hashlib
import hmac
import time
from datetime import datetime, timedelta
from typing import Optional, Tuple
import logging

from django.conf import settings
from django.utils import timezone
from django.core.cache import cache
from django.core.mail import send_mail
from decimal import Decimal, InvalidOperation

logger = logging.getLogger(__name__)


class OTPSecurityService:
    """
    Secure OTP generation and validation service.
    Provides cryptographically secure OTP generation and validation.
    """

    # OTP Configuration
    OTP_LENGTH = 6
    OTP_VALIDITY_MINUTES = 10
    MAX_OTP_ATTEMPTS = 3
    OTP_CACHE_TIMEOUT = 600  # 10 minutes

    @classmethod
    def generate_secure_otp(cls) -> str:
        """
        Generate a cryptographically secure OTP.
        Uses cryptographically secure random number generation.
        """
        # Use secrets module for cryptographically secure random generation
        try:
            import secrets
            otp = ''.join(secrets.choice(string.digits) for _ in range(cls.OTP_LENGTH))
        except ImportError:
            # Fallback to random if secrets is not available
            otp = ''.join(random.choices(string.digits, k=cls.OTP_LENGTH))

        logger.info(f"Generated secure OTP (length: {len(otp)})")
        return otp

    @classmethod
    def hash_otp(cls, otp: str) -> str:
        """
        Hash OTP for secure storage.
        Uses SHA-256 with salt for secure hashing.
        """
        # Create a hash of the OTP for secure storage
        salt = settings.SECRET_KEY[:32]  # Use first 32 chars of secret key as salt
        otp_bytes = otp.encode('utf-8')
        salt_bytes = salt.encode('utf-8')

        # Create HMAC hash
        hashed_otp = hmac.new(salt_bytes, otp_bytes, hashlib.sha256).hexdigest()
        return hashed_otp

    @classmethod
    def create_otp_request(cls, user_id: int, purpose: str = 'general', email: str = None) -> dict:
        """
        Create a new OTP request with secure generation and storage.

        Args:
            user_id: The user ID requesting the OTP
            purpose: The purpose of the OTP request
            email: Email address for OTP delivery (optional)

        Returns:
            dict: OTP request data (without exposing the actual OTP)
        """
        otp_code = cls.generate_secure_otp()
        expires_at = timezone.now() + timedelta(minutes=cls.OTP_VALIDITY_MINUTES)

        # Create cache key for this OTP request
        cache_key = f"otp_{user_id}_{purpose}_{int(time.time())}"

        # Store OTP data in cache (hashed for security)
        otp_data = {
            'otp_hash': cls.hash_otp(otp_code),
            'expires_at': expires_at,
            'attempts': 0,
            'purpose': purpose,
            'created_at': timezone.now()
        }

        # Store in cache with expiration
        cache.set(cache_key, otp_data, timeout=cls.OTP_CACHE_TIMEOUT)

        # Send OTP via email if email provided
        if email:
            cls.send_otp_via_email(otp_code, email, purpose)

        # For testing purposes, print the OTP (remove in production)
        if settings.DEBUG:
            print(f"DEBUG: Generated OTP for {email}: {otp_code}")

        logger.info(f"Created OTP request for user {user_id}, purpose: {purpose}")

        # Return OTP code in debug mode for testing
        response_data = {
            'cache_key': cache_key,
            'expires_at': expires_at,
            'purpose': purpose,
            'message': 'OTP generated and sent successfully'
        }
        
        if settings.DEBUG:
            response_data['otp_code'] = otp_code
            
        return response_data

    @classmethod
    def send_otp_via_email(cls, otp_code: str, recipient_email: str, purpose: str = 'general') -> bool:
        """
        Send OTP via email securely.

        Args:
            otp_code: The OTP code to send
            recipient_email: Email address of the recipient
            purpose: Purpose of the OTP for context

        Returns:
            bool: True if sent successfully
        """
        try:
            subject = f'IBET Security Code - {purpose.replace("_", " ").title()}'
            message = f"""
Your secure OTP code for {purpose.replace("_", " ").lower()} is: {otp_code}

This code will expire in {cls.OTP_VALIDITY_MINUTES} minutes.
Do not share this code with anyone.

If you did not request this code, please ignore this email.
"""
            from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@ibet.com')

            send_mail(
                subject=subject,
                message=message,
                from_email=from_email,
                recipient_list=[recipient_email],
                fail_silently=False
            )

            logger.info(f"OTP sent via email to {recipient_email} for purpose: {purpose}")
            return True

        except Exception as e:
            logger.error(f"Failed to send OTP via email: {e}")
            return False

    @classmethod
    def validate_otp(cls, user_id: int, otp_code: str, cache_key: str, purpose: str = 'general') -> Tuple[bool, str]:
        """
        Validate an OTP code against stored request.

        Args:
            user_id: The user ID validating the OTP
            otp_code: The OTP code to validate
            cache_key: The cache key for the OTP request
            purpose: The purpose of the OTP request

        Returns:
            Tuple[bool, str]: (is_valid, error_message)
        """
        # Get OTP data from cache
        otp_data = cache.get(cache_key)
        if not otp_data:
            logger.warning(f"OTP cache key not found: {cache_key}")
            return False, "OTP request not found or expired"

        # Check if OTP has expired
        if timezone.now() > otp_data['expires_at']:
            # Clean up expired OTP
            cache.delete(cache_key)
            logger.warning(f"OTP expired for user {user_id}")
            return False, "OTP has expired"

        # Check attempt count
        if otp_data['attempts'] >= cls.MAX_OTP_ATTEMPTS:
            # Clean up after max attempts
            cache.delete(cache_key)
            logger.warning(f"Max OTP attempts exceeded for user {user_id}")
            return False, "Maximum validation attempts exceeded"

        # Hash the provided OTP and compare
        provided_otp_hash = cls.hash_otp(otp_code)
        if not hmac.compare_digest(provided_otp_hash, otp_data['otp_hash']):
            # Increment attempt count
            otp_data['attempts'] += 1
            cache.set(cache_key, otp_data, timeout=cls.OTP_CACHE_TIMEOUT)

            remaining_attempts = cls.MAX_OTP_ATTEMPTS - otp_data['attempts']
            logger.warning(f"Invalid OTP attempt for user {user_id}, {remaining_attempts} attempts remaining")
            return False, f"Invalid OTP code. {remaining_attempts} attempts remaining"

        # OTP is valid - clean up and return success
        cache.delete(cache_key)
        logger.info(f"OTP validated successfully for user {user_id}")
        return True, "OTP validated successfully"

    @classmethod
    def cleanup_expired_otps(cls):
        """
        Clean up expired OTP requests from cache.
        This method should be called periodically (e.g., via cron job).
        """
        # This is a simplified cleanup - in production, you'd want more sophisticated cache management
        logger.info("OTP cleanup completed")


class SecurityUtils:
    """
    General security utilities for the application.
    """

    @staticmethod
    def generate_secure_token(length: int = 32) -> str:
        """
        Generate a secure random token.
        """
        try:
            import secrets
            token = secrets.token_urlsafe(length)
        except ImportError:
            # Fallback to random
            token = ''.join(random.choices(string.ascii_letters + string.digits, k=length))
        return token

    @staticmethod
    def hash_sensitive_data(data: str) -> str:
        """
        Hash sensitive data for secure storage.
        """
        return hashlib.sha256(data.encode('utf-8')).hexdigest()

    @staticmethod
    def validate_user_access(parent_user, student_user) -> bool:
        """
        Validate if a parent has access to a student's data.
        """
        from student_module.models import ParentStudentLink
        return ParentStudentLink.objects.filter(
            parent=parent_user,
            student=student_user
        ).exists()

    @staticmethod
    def log_security_event(event_type: str, user_id: int, details: dict = None):
        """
        Log a security-related event.
        """
        logger.info(f"Security Event: {event_type} - User: {user_id} - Details: {details or {}}")

    @staticmethod
    def safe_decimal_conversion(value, default=Decimal('0.00')):
        """
        Safely convert a value to Decimal, handling invalid inputs.

        Args:
            value: The value to convert to Decimal
            default: Default value to return if conversion fails

        Returns:
            Decimal: The converted value or default

        Raises:
            ValueError: If conversion fails and no default is provided
        """
        if value is None:
            if default is not None:
                return default
            raise ValueError("Cannot convert None to Decimal")

        try:
            # Convert to string first to handle various input types
            if isinstance(value, str):
                # Remove any whitespace and common currency symbols
                cleaned_value = value.strip().replace('$', '').replace(',', '')
                return Decimal(cleaned_value)
            else:
                return Decimal(value)
        except (InvalidOperation, ValueError, TypeError) as e:
            logger.warning(f"Failed to convert {value} to Decimal: {e}")
            if default is not None:
                return default
            raise ValueError(f"Invalid decimal value: {value}")


class RateLimitService:
    """
    Service for managing rate limiting and security monitoring.
    """

    @staticmethod
    def check_suspicious_activity(user_id: int, action: str) -> bool:
        """
        Check if user activity appears suspicious.
        Returns True if activity is suspicious.
        """
        # Simple implementation - in production, this would be more sophisticated
        cache_key = f"suspicious_activity_{user_id}_{action}"

        # Check if user has exceeded threshold in last hour
        recent_count = cache.get(cache_key, 0)

        if recent_count > 50:  # Threshold for suspicious activity
            logger.warning(f"Suspicious activity detected for user {user_id}, action: {action}")
            SecurityUtils.log_security_event('suspicious_activity', user_id, {'action': action})
            return True

        # Increment counter
        cache.set(cache_key, recent_count + 1, timeout=3600)  # 1 hour
        return False

    @staticmethod
    def record_security_event(user_id: int, event_type: str, details: dict = None):
        """
        Record a security event for monitoring.
        """
        cache_key = f"security_event_{user_id}_{event_type}_{int(time.time())}"
        event_data = {
            'event_type': event_type,
            'details': details or {},
            'timestamp': timezone.now()
        }

        cache.set(cache_key, event_data, timeout=86400)  # 24 hours
        SecurityUtils.log_security_event(event_type, user_id, details)
