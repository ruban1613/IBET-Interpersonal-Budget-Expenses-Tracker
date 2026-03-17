from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from unittest.mock import patch
from .models import ParentOTPRequest, StudentMonitoring
from student_module.models import ParentStudentLink

User = get_user_model()


@override_settings(
    SECURE_SSL_REDIRECT=False,
    CSRF_COOKIE_SECURE=False,
    SESSION_COOKIE_SECURE=False
)
class ParentModuleTestCase(APITestCase):
    def setUp(self):
        # Create test users
        self.parent = User.objects.create_user(
            username='parent_test',
            email='parent@test.com',
            password='testpass123',
            persona='PARENT'
        )
        self.student = User.objects.create_user(
            username='student_test',
            email='student@test.com',
            password='testpass123',
            persona='STUDENT'
        )

        # Create parent-student link
        ParentStudentLink.objects.create(parent=self.parent, student=self.student)

    @patch('parent_module.views.OTPGenerationThrottle')
    @patch('parent_module.views.SensitiveOperationsThrottle')
    def test_generate_otp(self, mock_sensitive_throttle, mock_otp_throttle):
        """Test OTP generation for parent"""
        # Mock throttling to always allow requests
        mock_otp_throttle.return_value.allow_request.return_value = True
        mock_sensitive_throttle.return_value.allow_request.return_value = True

        self.client.force_authenticate(user=self.parent)
        url = reverse('generate-otp')
        data = {
            'student_id': self.student.id,
            'amount_requested': 500.00,
            'reason': 'Weekly allowance'
        }
        response = self.client.post(url, data, format='json', follow=True)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('otp_code', response.data)

    def test_linked_students_view(self):
        """Test getting linked students"""
        self.client.force_authenticate(user=self.parent)
        url = reverse('linked-students')
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['linked_students']), 1)
        self.assertEqual(response.data['linked_students'][0]['id'], self.student.id)

    @patch('parent_module.views.WalletAccessThrottle')
    def test_student_overview(self, mock_wallet_throttle):
        """Test student overview view"""
        # Mock throttling to always allow requests
        mock_wallet_throttle.return_value.allow_request.return_value = True

        self.client.force_authenticate(user=self.parent)
        url = reverse('student-overview', kwargs={'student_id': self.student.id})
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('wallet_balance', response.data)


class ParentOTPRequestModelTest(TestCase):
    def setUp(self):
        self.parent = User.objects.create_user(
            username='parent_model',
            email='parent@model.com',
            password='testpass123',
            persona='PARENT'
        )
        self.student = User.objects.create_user(
            username='student_model',
            email='student@model.com',
            password='testpass123',
            persona='STUDENT'
        )

    def test_otp_request_creation(self):
        """Test creating OTP request"""
        from django.utils import timezone
        from datetime import timedelta
        expires_at = timezone.now() + timedelta(minutes=10)
        otp_request = ParentOTPRequest.objects.create(
            parent=self.parent,
            student=self.student,
            otp_code='123456',
            amount_requested=300.00,
            reason='Test allowance',
            expires_at=expires_at
        )
        self.assertEqual(otp_request.status, 'PENDING')
        self.assertEqual(otp_request.otp_code, '123456')
        self.assertIsNotNone(otp_request.expires_at)

    def test_otp_expiration(self):
        """Test OTP expiration logic"""
        from django.utils import timezone
        from datetime import timedelta
        expires_at = timezone.now() + timedelta(minutes=10)
        otp_request = ParentOTPRequest.objects.create(
            parent=self.parent,
            student=self.student,
            otp_code='654321',
            amount_requested=300.00,
            reason='Test allowance',
            expires_at=expires_at
        )
        self.assertFalse(otp_request.is_expired())

        # Manually expire the OTP
        otp_request.expires_at = timezone.now() - timedelta(minutes=1)
        otp_request.save()
        self.assertTrue(otp_request.is_expired())
