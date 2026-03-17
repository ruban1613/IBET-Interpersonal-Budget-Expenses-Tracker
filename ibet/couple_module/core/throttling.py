from rest_framework.throttling import UserRateThrottle, AnonRateThrottle
from django.conf import settings

class OTPGenerationThrottle(UserRateThrottle):
    """
    Custom throttle for OTP generation requests.
    Limits to 5 requests per hour per user.
    """
    scope = 'otp_generation'
    rate = settings.THROTTLE_RATES.get('otp_generation', '5/hour')


class OTPVerificationThrottle(UserRateThrottle):
    """
    Custom throttle for OTP verification attempts.
    Limits to 3 attempts per minute per user.
    """
    scope = 'otp_verification'
    rate = settings.THROTTLE_RATES.get('otp_verification', '3/minute')


class WalletAccessThrottle(UserRateThrottle):
    """
    Custom throttle for wallet access operations.
    Limits to 10 requests per minute per user.
    """
    scope = 'wallet_access'
    rate = settings.THROTTLE_RATES.get('wallet_access', '10/minute')


class SensitiveOperationsThrottle(UserRateThrottle):
    """
    Custom throttle for sensitive operations like fund transfers.
    Limits to 20 requests per hour per user.
    """
    scope = 'sensitive_operations'
    rate = settings.THROTTLE_RATES.get('sensitive_operations', '20/hour')


class StrictAnonThrottle(AnonRateThrottle):
    """
    Stricter anonymous throttling for public endpoints.
    """
    scope = 'strict_anon'
    rate = '10/hour'  # Very limited for anonymous users


class BurstThrottle(UserRateThrottle):
    """
    Allows bursts of requests but limits sustained usage.
    """
    scope = 'burst'
    rate = '60/minute'  # Allow bursts up to 60 per minute
