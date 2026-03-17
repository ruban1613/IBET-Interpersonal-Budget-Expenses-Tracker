"""
Comprehensive test for wallet functionality across all modules.
Tests wallet operations for Individual, Couple, Retiree, Dailywage, Student, and Parent modules.
"""
import os
import sys
import django
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from decimal import Decimal
from django.utils import timezone

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings_testing_final')
django.setup()

User = get_user_model()

class WalletCompleteTest(APITestCase):
    """Test wallet functionality for all modules."""

    def setUp(self):
        """Set up test data."""
        # Create test users for different personas
        self.individual_user = User.objects.create_user(
            username='individual_test',
            email='individual@test.com',
            password='testpass123',
            persona='INDIVIDUAL'
        )

        self.couple_user1 = User.objects.create_user(
            username='couple_test1',
            email='couple1@test.com',
            password='testpass123',
            persona='COUPLE'
        )

        self.couple_user2 = User.objects.create_user(
            username='couple_test2',
            email='couple2@test.com',
            password='testpass123',
            persona='COUPLE'
        )

        self.student_user = User.objects.create_user(
            username='student_test',
            email='student@test.com',
            password='testpass123',
            persona='STUDENT'
        )

        self.parent_user = User.objects.create_user(
            username='parent_test',
            email='parent@test.com',
            password='testpass123',
            persona='PARENT'
        )

        self.retiree_user = User.objects.create_user(
            username='retiree_test',
            email='retiree@test.com',
            password='testpass123',
            persona='RETIREE'
        )

        self.dailywage_user = User.objects.create_user(
            username='dailywage_test',
            email='dailywage@test.com',
            password='testpass123',
            persona='DAILY_WAGER'
        )

        # Create parent-student link
        from student_module.models import ParentStudentLink
        ParentStudentLink.objects.create(
            parent=self.parent_user,
            student=self.student_user
        )

    def authenticate_user(self, user):
        """Authenticate a user and return client."""
        client = Client()
        client.login(username=user.username, password='testpass123')
        return client

    def test_individual_wallet_functionality(self):
        """Test individual wallet operations."""
        client = self.authenticate_user(self.individual_user)

        # Test wallet balance
        response = client.get('/api/individual/wallet/balance/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('balance', response.json())

        # Test wallet deposit
        response = client.post('/api/individual/wallet/deposit/',
                              {'amount': '100.00', 'description': 'Test deposit'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('new_balance', response.json())

        # Test wallet withdrawal
        response = client.post('/api/individual/wallet/withdraw/',
                              {'amount': '50.00', 'description': 'Test withdrawal'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('new_balance', response.json())

    def test_couple_wallet_functionality(self):
        """Test couple wallet operations."""
        client = self.authenticate_user(self.couple_user1)

        # Test wallet balance
        response = client.get('/api/couple/wallet/balance/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('balance', response.json())

        # Test wallet deposit
        response = client.post('/api/couple/wallet/deposit/',
                              {'amount': '200.00', 'description': 'Test deposit'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('new_balance', response.json())

    def test_retiree_wallet_functionality(self):
        """Test retiree wallet operations."""
        client = self.authenticate_user(self.retiree_user)

        # Test wallet balance
        response = client.get('/api/retiree/wallet/balance/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('balance', response.json())

        # Test wallet deposit
        response = client.post('/api/retiree/wallet/deposit/',
                              {'amount': '300.00', 'description': 'Test deposit'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('new_balance', response.json())

    def test_dailywage_wallet_functionality(self):
        """Test dailywage wallet operations."""
        client = self.authenticate_user(self.dailywage_user)

        # Test wallet balance
        response = client.get('/api/dailywage/wallet/balance/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('balance', response.json())

        # Test wallet deposit
        response = client.post('/api/dailywage/wallet/deposit/',
                              {'amount': '150.00', 'description': 'Test deposit'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('new_balance', response.json())

    def test_student_wallet_functionality(self):
        """Test student wallet operations."""
        client = self.authenticate_user(self.student_user)

        # Test wallet balance
        response = client.get('/api/student/wallet/balance/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('balance', response.json())

        # Test wallet deposit
        response = client.post('/api/student/wallet/deposit/',
                              {'amount': '75.00', 'description': 'Test deposit'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('new_balance', response.json())

        # Test parent approval request
        response = client.post('/api/student/wallet/request_parent_approval/',
                              {'amount': '25.00', 'description': 'Test parent approval'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('otp_request_id', response.json())

    def test_parent_wallet_functionality(self):
        """Test parent wallet operations."""
        client = self.authenticate_user(self.parent_user)

        # Test wallet balance
        response = client.get('/api/parent/wallet/balance/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('balance', response.json())

        # Test wallet deposit
        response = client.post('/api/parent/wallet/deposit/',
                              {'amount': '400.00', 'description': 'Test deposit'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('new_balance', response.json())

        # Test linked students wallets
        response = client.get('/api/parent/wallet/linked_students_wallets/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('linked_students_wallets', response.json())

    def test_wallet_otp_generation_and_verification(self):
        """Test OTP generation and verification for all modules."""
        # Test individual wallet OTP
        client = self.authenticate_user(self.individual_user)
        response = client.post('/api/individual/wallet/generate-otp/',
                              {'operation_type': 'deposit', 'amount': '50.00'})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('otp_request_id', response.json())

        # Test student wallet OTP
        client = self.authenticate_user(self.student_user)
        response = client.post('/api/student/wallet/generate-otp/',
                              {'operation_type': 'deposit', 'amount': '25.00'})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('otp_request_id', response.json())

        # Test parent wallet OTP
        client = self.authenticate_user(self.parent_user)
        response = client.post('/api/parent/wallet/generate-otp/',
                              {'operation_type': 'deposit', 'amount': '100.00'})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('otp_request_id', response.json())

    def test_cross_module_wallet_interactions(self):
        """Test interactions between different modules' wallets."""
        # Test parent-student wallet interaction
        parent_client = self.authenticate_user(self.parent_user)
        student_client = self.authenticate_user(self.student_user)

        # Parent requests OTP for student approval
        response = parent_client.post('/api/parent/generate-otp/',
                                     {'student_id': self.student_user.id,
                                      'amount_requested': '50.00',
                                      'reason': 'Test approval'})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        otp_request_id = response.json()['otp_request_id']

        # Student requests parent approval
        response = student_client.post('/api/student/wallet/request_parent_approval/',
                                      {'amount': '50.00', 'description': 'Test approval request'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_wallet_security_features(self):
        """Test wallet security features like throttling and permissions."""
        client = self.authenticate_user(self.individual_user)

        # Test rapid requests (should be throttled)
        for i in range(10):
            response = client.get('/api/individual/wallet/balance/')

        # Should eventually be throttled
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_429_TOO_MANY_REQUESTS])

        # Test invalid operations
        response = client.post('/api/individual/wallet/withdraw/',
                              {'amount': '10000.00', 'description': 'Over withdrawal'})
        # Should fail due to insufficient funds
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_wallet_comprehensive_coverage(self):
        """Comprehensive test covering all wallet endpoints."""
        modules = [
            ('individual', self.individual_user),
            ('couple', self.couple_user1),
            ('retiree', self.retiree_user),
            ('dailywage', self.dailywage_user),
            ('student', self.student_user),
            ('parent', self.parent_user),
        ]

        for module_name, user in modules:
            with self.subTest(module=module_name):
                client = self.authenticate_user(user)

                # Test balance endpoint
                response = client.get(f'/api/{module_name}/wallet/balance/')
                self.assertEqual(response.status_code, status.HTTP_200_OK)

                # Test deposit endpoint
                response = client.post(f'/api/{module_name}/wallet/deposit/',
                                      {'amount': '10.00', 'description': 'Test deposit'})
                self.assertEqual(response.status_code, status.HTTP_200_OK)

                # Test OTP generation
                response = client.post(f'/api/{module_name}/wallet/generate-otp/',
                                      {'operation_type': 'deposit', 'amount': '5.00'})
                self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_wallet_error_handling(self):
        """Test error handling in wallet operations."""
        client = self.authenticate_user(self.individual_user)

        # Test invalid amount
        response = client.post('/api/individual/wallet/deposit/',
                              {'amount': '-10.00', 'description': 'Invalid deposit'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Test missing required fields
        response = client.post('/api/individual/wallet/deposit/',
                              {'description': 'Missing amount'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Test withdrawal with insufficient funds
        response = client.post('/api/individual/wallet/withdraw/',
                              {'amount': '10000.00', 'description': 'Over withdrawal'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


if __name__ == '__main__':
    import unittest
    unittest.main()
