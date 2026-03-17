from django.http import HttpResponse
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware:
    """
    Middleware to add security headers to all responses.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Add security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'

        # Add Content Security Policy for additional protection
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self'; "
            "frame-ancestors 'none';"
        )
        response['Content-Security-Policy'] = csp

        return response


class RequestLoggingMiddleware:
    """
    Middleware to log all requests for security monitoring.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Log the request
        logger.info(
            f"Request: {request.method} {request.path} from {request.META.get('REMOTE_ADDR')} "
            f"User-Agent: {request.META.get('HTTP_USER_AGENT', 'Unknown')}"
        )

        response = self.get_response(request)

        # Log the response status
        logger.info(f"Response: {response.status_code} for {request.path}")

        return response


class RateLimitExceededMiddleware:
    """
    Middleware to handle rate limit exceeded responses with custom messages.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Check if this is a rate limit response
        if response.status_code == 429:
            # Customize the rate limit response
            response.content = b'{"error": "Too many requests. Please try again later.", "retry_after": 60}'
            response['Content-Type'] = 'application/json'
            response['Retry-After'] = '60'  # seconds

        return response


class SensitiveDataMaskingMiddleware:
    """
    Middleware to mask sensitive data in logs and responses.
    """

    SENSITIVE_FIELDS = ['password', 'token', 'otp', 'secret', 'key']

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Mask sensitive data in request body for logging
        if hasattr(request, 'body') and request.body:
            try:
                import json
                body_data = json.loads(request.body.decode('utf-8'))
                masked_data = self._mask_sensitive_data(body_data)
                logger.debug(f"Request body: {json.dumps(masked_data)}")
            except (json.JSONDecodeError, UnicodeDecodeError):
                logger.debug("Request body: [binary or non-JSON data]")

        response = self.get_response(request)

        # Mask sensitive data in response content for logging
        if hasattr(response, 'content') and response.content:
            try:
                import json
                content_data = json.loads(response.content.decode('utf-8'))
                masked_data = self._mask_sensitive_data(content_data)
                logger.debug(f"Response content: {json.dumps(masked_data)}")
            except (json.JSONDecodeError, UnicodeDecodeError, AttributeError):
                logger.debug("Response content: [binary or non-JSON data]")

        return response

    def _mask_sensitive_data(self, data):
        """Recursively mask sensitive fields in data."""
        if isinstance(data, dict):
            masked = {}
            for key, value in data.items():
                if any(sensitive in key.lower() for sensitive in self.SENSITIVE_FIELDS):
                    masked[key] = '***MASKED***'
                else:
                    masked[key] = self._mask_sensitive_data(value)
            return masked
        elif isinstance(data, list):
            return [self._mask_sensitive_data(item) for item in data]
        else:
            return data
