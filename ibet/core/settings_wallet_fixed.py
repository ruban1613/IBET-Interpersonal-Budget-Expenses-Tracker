"""
Django settings for core project - Testing Configuration
This file contains increased throttling rates for testing purposes.
"""

from .settings import *

# Override throttling rates for testing
THROTTLE_RATES = {
    'otp_generation': '20/hour',  # Max 20 OTP requests per hour per user (increased for testing)
    'otp_verification': '10/minute',  # Max 10 verification attempts per minute (increased for testing)
    'wallet_access': '50/minute',  # Max 50 wallet access requests per minute (increased for testing)
    'sensitive_operations': '50/hour',  # Max 50 sensitive operations per hour (increased for testing)
    'strict_anon': '20/hour',  # Increased for anonymous users
    'burst': '100/minute',  # Allow bursts up to 100 per minute (increased for testing)
}

# Override URL configuration for testing
ROOT_URLCONF = 'core.urls_wallet_fixed'
