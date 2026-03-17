"""
Fixed comprehensive test for wallet functionality across all modules.
Tests wallet operations for Individual, Couple, Retiree, Dailywage, Student, and Parent modules.
"""
import os
import sys
import django
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework.authtoken.models import Token
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

        # Create auth tokens for users
        self.individual_token = Token.objects.create(user=self.individual_user)
        self.couple_token = Token.objects.create(user=self.couple_user1)
        self.student_token = Token.objects.create(user=self.student_user)
        self.parent_token = Token.objects.create(user=self.parent_user)
        self.retiree_token = Token.objects.create(user=self.retiree_user)
        self.dailywage_token = Token.objects.create(user=self.dailywage_user)

    def get_authenticated_client(self, user):
        """Get authenticated API client for a user."""
        client = APIClient()
        token = Token.objects.get(user=user)
        client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
        return client

    def test_individual_wallet_functionality(self):
        """Test individual wallet operations."""
        client = self.get_authenticated_client(self.individual_user)

        # Test wallet balance
        response = client.get('/api/individual/wallet/balance/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('balance', response.data)

        # Test wallet deposit
        response = client.post('/api/individual/wallet/deposit/',
                              {'amount': '100.00', 'description': 'Test deposit'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('new_balance', response.data)

        # Test wallet withdrawal
        response = client.post('/api/individual/wallet/withdraw/',
                              {'amount': '50.00', 'description': 'Test withdrawal'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('new_balance', response.data)

    def test_couple_wallet_functionality(self):
        """Test couple wallet operations."""
        client = self.get_authenticated_client(self.couple_user1)

        # Test wallet balance
        response = client.get('/api/couple/wallet/balance/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('balance', response.data)

        # Test wallet deposit
        response = client.post('/api/couple/wallet/deposit/',
                              {'amount': '200.00', 'description': 'Test deposit'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('new_balance', response.data)

        # Test wallet withdrawal
        response = client.post('/api/couple/wallet/withdraw/',
                              {'amount': '100.00', 'description': 'Test withdrawal'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('new_balance', response.data)

    def test_retiree_wallet_functionality(self):
        """Test retiree wallet operations."""
        client = self.get_authenticated_client(self.retiree_user)

        # Test wallet balance
        response = client.get('/api/retiree/wallet/balance/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('balance', response.data)

        # Test wallet deposit
        response = client.post('/api/retiree/wallet/deposit/',
                              {'amount': '300.00', 'description': 'Test deposit'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('new_balance', response.data)

        # Test wallet withdrawal
        response = client.post('/api/retiree/wallet/withdraw/',
                              {'amount': '150.00', 'description': 'Test withdrawal'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('new_balance', response.data)

    def test_dailywage_wallet_functionality(self):
        """Test dailywage wallet operations."""
        client = self.get_authenticated_client(self.dailywage_user)

        # Test wallet balance
        response = client.get('/api/dailywage/wallet/balance/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('balance', response.data)

        # Test wallet deposit
        response = client.post('/api/dailywage/wallet/deposit/',
                              {'amount': '150.00', 'description': 'Test deposit'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('new_balance', response.data)

        # Test wallet withdrawal
        response = client.post('/api/dailywage/wallet/withdraw/',
                              {'amount': '75.00', 'description': 'Test withdrawal'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('new_balance', response.data)

    def test_student_wallet_functionality(self):
        """Test student wallet operations."""
        client = self.get_authenticated_client(self.student_user)

        # Test wallet balance
        response = client.get('/api/student/wallet/balance/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('balance', response.data)

        # Test wallet deposit
        response = client.post('/api/student/wallet/deposit/',
                              {'amount': '75.00', 'description': 'Test deposit'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('new_balance', response.data)

        # Test parent approval request
        response = client.post('/api/student/wallet/request_parent_approval/',
                              {'amount': '25.00', 'description': 'Test parent approval'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('otp_request_id', response.data)

    def test_parent_wallet_functionality(self):
        """Test parent wallet operations."""
        client = self.get_authenticated_client(self.parent_user)

        # Test wallet balance
        response = client.get('/api/parent/wallet/balance/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('balance', response.data)

        # Test wallet deposit
        response = client.post('/api/parent/wallet/deposit/',
                              {'amount': '400.00', 'description': 'Test deposit'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('new_balance', response.data)

        # Test linked students wallets
        response = client.get('/api/parent/wallet/linked_students_wallets/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('linked_students_wallets', response.data)

    def test_wallet_otp_generation_and_verification(self):
        """Test complete OTP generation and verification flow for all modules."""
        # Test individual wallet OTP generation and verification
        client = self.get_authenticated_client(self.individual_user)
        response = client.post(reverse('individual_wallet:generate-individual-wallet-otp'),
                              {'operation_type': 'deposit', 'amount': '50.00'})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('otp_request_id', response.data)
        otp_request_id = response.data['otp_request_id']

        # Mock OTP verification (in real scenario, OTP would be sent to user)
        # For testing, we'll simulate the verification process
        from individual_module.models_wallet import IndividualWalletOTPRequest
        otp_request = IndividualWalletOTPRequest.objects.get(id=otp_request_id)
        # Simulate OTP being set (normally done by security service)
        otp_request.otp_code = '123456'  # Mock OTP
        otp_request.save()

        # Verify OTP - need to get the actual OTP from cache using the correct cache key
        from core.security import OTPSecurityService
        from django.core.cache import cache

        # Get the cache key from the OTP request object, or create one for testing
        if not otp_request.cache_key:
            cache_key = f"otp_{otp_request.user.id}_individual_wallet_operation_test"
            otp_request.cache_key = cache_key
            otp_request.save()
        else:
            cache_key = otp_request.cache_key

        otp_data = cache.get(cache_key)
        if otp_data:
            # For testing, we'll use a known OTP that matches the hash
            # In real scenario, this would be sent to user
            test_otp = '123456'
            # Hash it and store in cache for testing
            hashed_otp = OTPSecurityService.hash_otp(test_otp)
            otp_data['otp_hash'] = hashed_otp
            cache.set(cache_key, otp_data, timeout=600)

            response = client.post(reverse('individual_wallet:verify-individual-wallet-otp'),
                                  {'otp_code': test_otp, 'otp_request_id': otp_request_id})
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn('message', response.data)
            self.assertEqual(response.data['operation_type'], 'deposit')
            self.assertEqual(Decimal(response.data['amount']), Decimal('50.00'))
        else:
            # If cache not found, create it for testing
            from django.utils import timezone
            test_otp = '123456'
            hashed_otp = OTPSecurityService.hash_otp(test_otp)
            otp_data = {
                'otp_hash': hashed_otp,
                'expires_at': timezone.now() + timezone.timedelta(minutes=10),
                'attempts': 0,
                'purpose': 'individual_wallet_operation',
                'created_at': timezone.now()
            }
            cache.set(cache_key, otp_data, timeout=600)

            response = client.post(reverse('individual_wallet:verify-individual-wallet-otp'),
                                  {'otp_code': test_otp, 'otp_request_id': otp_request_id})
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn('message', response.data)
            self.assertEqual(response.data['operation_type'], 'deposit')
            self.assertEqual(Decimal(response.data['amount']), Decimal('50.00'))

        # Test student wallet OTP
        client = self.get_authenticated_client(self.student_user)
        response = client.post('/api/student/wallet/generate-otp/',
                              {'operation_type': 'deposit', 'amount': '25.00'})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('otp_request_id', response.data)

        # Test couple wallet OTP
        client = self.get_authenticated_client(self.couple_user1)
        response = client.post(reverse('generate-couple-wallet-otp'),
                              {'operation_type': 'deposit', 'amount': '50.00'})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('otp_request_id', response.data)

        # Test parent wallet OTP
        client = self.get_authenticated_client(self.parent_user)
        response = client.post('/api/parent/wallet/generate-otp/',
                              {'operation_type': 'deposit', 'amount': '100.00'})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('otp_request_id', response.data)

        # Test invalid OTP verification
        response = client.post('/api/individual/wallet/verify-otp/',
                              {'otp_code': '999999', 'otp_request_id': otp_request_id})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Test couple wallet OTP
        client = self.get_authenticated_client(self.couple_user1)
        response = client.post('/api/couple/wallet/generate-otp/',
                              {'operation_type': 'deposit', 'amount': '50.00'})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('otp_request_id', response.data)

        # Test parent wallet OTP
        client = self.get_authenticated_client(self.parent_user)
        response = client.post('/api/parent/wallet/generate-otp/',
                              {'operation_type': 'deposit', 'amount': '100.00'})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('otp_request_id', response.data)

        # Test invalid OTP verification
        response = client.post('/api/individual/wallet/verify-otp/',
                              {'otp_code': '999999', 'otp_request_id': otp_request_id})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cross_module_wallet_interactions(self):
        """Test interactions between different modules' wallets."""
        # Test parent-student wallet interaction
        parent_client = self.get_authenticated_client(self.parent_user)
        student_client = self.get_authenticated_client(self.student_user)

        # Parent requests OTP for student approval
        response = parent_client.post('/api/parent/generate-otp/',
                                     {'student_id': self.student_user.id,
                                      'amount_requested': '50.00',
                                      'reason': 'Test approval'})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        otp_request_id = response.data['otp_request_id']

        # Student requests parent approval
        response = student_client.post('/api/student/wallet/request_parent_approval/',
                                      {'amount': '50.00', 'description': 'Test approval request'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_wallet_security_features(self):
        """Test wallet security features like throttling and permissions."""
        client = self.get_authenticated_client(self.individual_user)

        # Test rapid requests (should be throttled after threshold)
        throttle_triggered = False
        for i in range(15):  # More requests to ensure throttling
            response = client.get('/api/individual/wallet/balance/')
            if response.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
                throttle_triggered = True
                break

        # Should be throttled after threshold
        self.assertTrue(throttle_triggered, "Throttling should be triggered after rapid requests")

        # Test invalid operations - insufficient funds
        response = client.post('/api/individual/wallet/withdraw/',
                              {'amount': '10000.00', 'description': 'Over withdrawal'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Test invalid amount formats
        response = client.post('/api/individual/wallet/deposit/',
                              {'amount': '-100.00', 'description': 'Negative amount'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        response = client.post('/api/individual/wallet/deposit/',
                              {'amount': '0.00', 'description': 'Zero amount'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        response = client.post('/api/individual/wallet/deposit/',
                              {'amount': 'abc', 'description': 'Invalid format'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Test missing required fields
        response = client.post('/api/individual/wallet/deposit/',
                              {'description': 'Missing amount'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Test unauthorized access (different user)
        other_client = self.get_authenticated_client(self.couple_user1)
        response = other_client.get('/api/individual/wallet/balance/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)  # Should not access other user's wallet

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

        # Define deposit amounts per module for variety
        deposit_amounts = {
            'individual': Decimal('100.00'),
            'couple': Decimal('200.00'),
            'retiree': Decimal('300.00'),
            'dailywage': Decimal('150.00'),
            'student': Decimal('75.00'),
            'parent': Decimal('400.00'),
        }

        for module_name, user in modules:
            with self.subTest(module=module_name):
                client = self.get_authenticated_client(user)

                # URL prefix logic for couple/parent modules (no extra /wallet/)
                url_prefix = 'wallet/' if module_name not in ['couple', 'parent'] else ''

                # Test balance retrieval
                if module_name == 'student':
                    balance_url = f'/api/student/wallet/balance/'
                else:
                    balance_url = f'/api/{module_name}/wallet/balance/'
                response = client.get(balance_url)
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.assertIn('balance', response.data)
                initial_balance = Decimal(response.data['balance'])

                # Test deposit
                if module_name == 'student':
                    deposit_url = f'/api/student/wallet/deposit/'
                else:
                    deposit_url = f'/api/{module_name}/wallet/deposit/'
                amount = deposit_amounts[module_name]
                response = client.post(deposit_url, {'amount': str(amount), 'description': f'Test deposit for {module_name}'})
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.assertIn('new_balance', response.data)
                self.assertEqual(Decimal(response.data['new_balance']), initial_balance + amount)

                # Test withdrawal (skip for student as they may need parent approval)
                if module_name != 'student':
                    if module_name == 'student':
                        withdrawal_url = f'/api/student/wallet/withdraw/'
                    else:
                        withdrawal_url = f'/api/{module_name}/wallet/withdraw/'
                    withdraw_amount = amount / 2
                    response = client.post(withdrawal_url, {'amount': str(withdraw_amount), 'description': f'Test withdrawal for {module_name}'})
                    self.assertEqual(response.status_code, status.HTTP_200_OK)
                    self.assertIn('new_balance', response.data)
                    self.assertEqual(Decimal(response.data['new_balance']), initial_balance + amount - withdraw_amount)

                # Test parent approval for student
                if module_name == 'student':
                    approval_url = f'/api/student/wallet/request_parent_approval/'
                    response = client.post(approval_url, {'amount': '25.00', 'description': 'Test parent approval'})
                    self.assertEqual(response.status_code, status.HTTP_200_OK)
                    self.assertIn('otp_request_id', response.data)

                # Test linked students wallets for parent
                if module_name == 'parent':
                    linked_url = f'/api/{module_name}/wallet/linked-students-wallets/'
                    response = client.get(linked_url)
                    self.assertEqual(response.status_code, status.HTTP_200_OK)
                    self.assertIn('linked_students_wallets', response.data)

    def test_wallet_concurrent_operations(self):
        """Test concurrent wallet operations using threading to simulate race conditions."""
        import threading
        import time

        results = {'deposits': 0, 'withdrawals': 0, 'errors': 0}
        lock = threading.Lock()

        def perform_operation(operation_type, amount, description):
            """Perform wallet operation in a thread."""
            try:
                client = self.get_authenticated_client(self.individual_user)
                if operation_type == 'deposit':
                    response = client.post('/api/individual/wallet/deposit/',
                                          {'amount': str(amount), 'description': description})
                else:  # withdrawal
                    response = client.post('/api/individual/wallet/withdraw/',
                                          {'amount': str(amount), 'description': description})

                with lock:
                    if response.status_code == status.HTTP_200_OK:
                        if operation_type == 'deposit':
                            results['deposits'] += 1
                        else:
                            results['withdrawals'] += 1
                    else:
                        results['errors'] += 1
            except Exception as e:
                with lock:
                    results['errors'] += 1

        # Create multiple threads for concurrent operations
        threads = []
        for i in range(10):
            # Alternate between deposits and withdrawals
            if i % 2 == 0:
                t = threading.Thread(target=perform_operation,
                                   args=('deposit', Decimal('10.00'), f'Concurrent deposit {i}'))
            else:
                t = threading.Thread(target=perform_operation,
                                   args=('withdrawal', Decimal('5.00'), f'Concurrent withdrawal {i}'))
            threads.append(t)

        # Start all threads
        for t in threads:
            t.start()

        # Wait for all threads to complete
        for t in threads:
            t.join()

        # Verify results - should have some successful operations
        self.assertGreater(results['deposits'], 0, "Should have successful deposits")
        self.assertGreater(results['withdrawals'], 0, "Should have successful withdrawals")

        # Check final balance is consistent
        client = self.get_authenticated_client(self.individual_user)
        response = client.get('/api/individual/wallet/balance/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        final_balance = Decimal(response.data['balance'])

        # Expected balance: (5 deposits * 10) - (5 withdrawals * 5) = 50 - 25 = 25
        expected_balance = Decimal('25.00')
        self.assertEqual(final_balance, expected_balance,
                        f"Final balance {final_balance} should equal expected {expected_balance}")
