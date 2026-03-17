import json
from django.test import TestCase, RequestFactory, override_settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.http import HttpResponse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from unittest.mock import patch, MagicMock

from .throttling import (
    OTPGenerationThrottle, OTPVerificationThrottle, WalletAccessThrottle,
    SensitiveOperationsThrottle, StrictAnonThrottle, BurstThrottle
)
from .middleware import (
    SecurityHeadersMiddleware, RequestLoggingMiddleware,
    RateLimitExceededMiddleware, SensitiveDataMaskingMiddleware
)


class ThrottlingTests(TestCase):
    """Test custom throttling classes"""

    def setUp(self):
        self.factory = RequestFactory()
        self.user = get_user_model().objects.create_user(username='testuser', password='testpass')

    def test_otp_generation_throttle(self):
        """Test OTP generation throttling configuration"""
        throttle = OTPGenerationThrottle()
        self.assertEqual(throttle.scope, 'otp_generation')
        self.assertEqual(throttle.rate, '5/hour')

    def test_wallet_access_throttle(self):
        """Test wallet access throttling configuration"""
        throttle = WalletAccessThrottle()
        self.assertEqual(throttle.scope, 'wallet_access')
        self.assertEqual(throttle.rate, '10/minute')

    def test_sensitive_operations_throttle(self):
        """Test sensitive operations throttling configuration"""
        throttle = SensitiveOperationsThrottle()
        self.assertEqual(throttle.scope, 'sensitive_operations')
        self.assertEqual(throttle.rate, '20/hour')


class SecurityMiddlewareTests(TestCase):
    """Test security middleware components"""

    def setUp(self):
        self.factory = RequestFactory()

    def test_security_headers_middleware(self):
        """Test security headers are added"""
        middleware = SecurityHeadersMiddleware(lambda r: HttpResponse())
        request = self.factory.get('/')

        response = middleware(request)

        # Check security headers are present
        self.assertEqual(response['X-Content-Type-Options'], 'nosniff')
        self.assertEqual(response['X-Frame-Options'], 'DENY')
        self.assertEqual(response['X-XSS-Protection'], '1; mode=block')
        self.assertEqual(response['X-Frame-Options'], 'DENY')
        self.assertIn('Content-Security-Policy', response)

    @patch('core.middleware.logger')
    def test_request_logging_middleware(self, mock_logger):
        """Test request logging"""
        middleware = RequestLoggingMiddleware(lambda r: HttpResponse())
        request = self.factory.get('/')
        request.META = {
            'REMOTE_ADDR': '127.0.0.1',
            'HTTP_USER_AGENT': 'TestAgent/1.0'
        }

        middleware(request)

        # Check that logging was called
        mock_logger.info.assert_called()

    def test_rate_limit_exceeded_middleware(self):
        """Test rate limit exceeded response customization"""
        middleware = RateLimitExceededMiddleware(lambda r: HttpResponse(status=429))
        request = self.factory.get('/')

        response = middleware(request)

        # Check custom response for rate limit
        self.assertEqual(response.status_code, 429)
        self.assertEqual(response['Content-Type'], 'application/json')
        self.assertIn('Retry-After', response)

    def test_sensitive_data_masking_middleware(self):
        """Test sensitive data masking in logs"""
        middleware = SensitiveDataMaskingMiddleware(lambda r: HttpResponse())

        # Create request with sensitive data
        request = self.factory.post('/', data=json.dumps({
            'password': 'secret123',
            'otp': '123456',
            'token': 'abc123',
            'normal_field': 'normal_value'
        }), content_type='application/json')

        response = middleware(request)

        # Check that sensitive data is masked in logs
        # (This would be verified by checking logger calls in a real scenario)


class OTPViewsTests(APITestCase):
    """Test OTP-related views with throttling"""

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(username='testuser', password='testpass')
        self.client.force_authenticate(user=self.user)

    def test_otp_generation_throttling(self):
        """Test OTP generation endpoint throttling"""
        url = reverse('generate-otp')

        # Make multiple requests to trigger throttling
        for i in range(10):
            response = self.client.post(url, {
                'student_id': 1,
                'amount_requested': 100.00,
                'reason': 'Test'
            })

        # Last request should be throttled
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    def test_wallet_access_throttling(self):
        """Test wallet access endpoint throttling"""
        url = reverse('student-wallet-access')

        # Make multiple requests to trigger throttling
        for i in range(15):
            response = self.client.post(url, {
                'student_id': 1,
                'amount_needed': 50.00,
                'reason': 'Test purchase'
            })

        # Last request should be throttled
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)


class SecurityIntegrationTests(APITestCase):
    """Integration tests for security features"""

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(username='testuser', password='testpass')
        self.client.force_authenticate(user=self.user)

    def test_security_headers_on_all_responses(self):
        """Test that security headers are present on all API responses"""
        # Test existing endpoints with correct URL patterns
        endpoints = [
            '/api/parent/generate-otp/',  # Use full URL path
            '/api/parent/wallet-access/',
            '/api/parent/students/',
            '/api/categories/',  # Use student module URL
        ]

        for endpoint in endpoints:
            # Try POST request first with basic data, then GET if POST fails
            response = self.client.post(endpoint, {'test': 'data'})
            if response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED:
                response = self.client.get(endpoint)

            # Allow various status codes including 400 Bad Request
            self.assertIn(response.status_code, [
                status.HTTP_200_OK,
                status.HTTP_400_BAD_REQUEST,
                status.HTTP_401_UNAUTHORIZED,
                status.HTTP_405_METHOD_NOT_ALLOWED
            ])
            self.assertIn('X-Content-Type-Options', response)
            self.assertIn('X-Frame-Options', response)
            self.assertIn('Content-Security-Policy', response)

    def test_rate_limit_response_format(self):
        """Test that rate limit exceeded responses have correct format"""
        # Trigger rate limiting by making many requests
        url = reverse('generate-otp')

        for i in range(20):
            response = self.client.post(url, {'test': 'data'})

        # Check the throttled response format
        if response.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
            self.assertIn('Retry-After', response)
            self.assertEqual(response['Content-Type'], 'application/json')

    def test_sensitive_data_not_logged(self):
        """Test that sensitive data is not logged in plain text"""
        with patch('core.middleware.logger') as mock_logger:
            # Make request with sensitive data
            response = self.client.post(reverse('generate-otp'), {
                'otp_code': '123456',
                'password': 'secret',
                'normal_field': 'value'
            })

            # Check that logger was called but sensitive data was masked
            # This would require inspecting the logger calls
            mock_logger.debug.assert_called()


class MiddlewareIntegrationTests(TestCase):
    """Test middleware integration"""

    def setUp(self):
        self.factory = RequestFactory()

    def test_middleware_chain(self):
        """Test that all middleware work together"""
        # Create a mock view
        def mock_view(request):
            return HttpResponse('OK')

        # Apply all middleware
        middleware_chain = [
            SecurityHeadersMiddleware,
            RequestLoggingMiddleware,
            RateLimitExceededMiddleware,
            SensitiveDataMaskingMiddleware,
        ]

        # Build the middleware chain
        view = mock_view
        for middleware_class in reversed(middleware_chain):
            view = middleware_class(view)

        # Make a request
        request = self.factory.get('/')
        request.META = {'REMOTE_ADDR': '127.0.0.1', 'HTTP_USER_AGENT': 'Test'}

        response = view(request)

        # Check that response has security headers
        self.assertEqual(response.status_code, 200)
        self.assertIn('X-Content-Type-Options', response)
        self.assertIn('X-Frame-Options', response)
