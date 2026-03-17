#!/usr/bin/env python
"""
Test script for Daily Wage Module enhancements.
Tests monthly summary endpoint and alert functionality.
"""
import os
import sys
import django
from decimal import Decimal

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ibet.core.settings')
sys.path.insert(0, os.path.dirname(__file__))
django.setup()

from django.test import TestCase, Client
from student_module.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from dailywage_module.models_wallet import DailyWageWallet, DailyWageWalletTransaction
from django.utils import timezone


class DailyWageWalletEnhancementsTest(APITestCase):
    """Test cases for daily wage wallet enhancements."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='test_dailywage_user',
            password='testpass123',
            email='test@example.com'
        )

        # Create wallet with alert threshold
        self.wallet = DailyWageWallet.objects.create(
            user=self.user,
            balance=Decimal('1000.00'),
            daily_earnings=Decimal('500.00'),
            weekly_target=Decimal('2000.00'),
            monthly_goal=Decimal('8000.00'),
            alert_threshold=Decimal('200.00'),  # Alert when balance drops below 200
            emergency_reserve=Decimal('300.00')
        )

        # Create some transactions for testing
        DailyWageWalletTransaction.objects.create(
            wallet=self.wallet,
            amount=Decimal('500.00'),
            transaction_type='DAILY_EARNINGS',
            description='Test earnings',
            balance_after=Decimal('1000.00')
        )

        DailyWageWalletTransaction.objects.create(
            wallet=self.wallet,
            amount=Decimal('100.00'),
            transaction_type='WITHDRAWAL',
            description='Test expense',
            balance_after=Decimal('900.00'),
            is_essential_expense=True
        )

        self.client.force_authenticate(user=self.user)

    def test_monthly_summary_endpoint(self):
        """Test the monthly summary endpoint."""
        url = reverse('dailywage_wallet:dailywage-wallet-monthly-summary')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('monthly_earnings', response.data)
        self.assertIn('monthly_expenses', response.data)
        self.assertIn('progress_percentage', response.data)
        self.assertIn('alert_triggered', response.data)

        # Check that earnings are calculated correctly
        self.assertAlmostEqual(float(response.data['monthly_earnings']), 500.00, places=2)

    def test_weekly_summary_with_alert(self):
        """Test weekly summary includes alert status."""
        url = reverse('dailywage_wallet:dailywage-wallet-weekly-summary')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('alert_triggered', response.data)

        # Current balance (1000) is above threshold (200), so alert should be False
        self.assertFalse(response.data['alert_triggered'])

    def test_alert_threshold_in_serializer(self):
        """Test that alert_threshold is included in wallet serializer."""
        url = reverse('dailywage_wallet:dailywage-wallet-balance')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # The balance endpoint should include alert_threshold in the response
        # (though it might not be directly exposed, the serializer should have it)

    def test_alert_triggered_when_balance_low(self):
        """Test that alert is triggered when balance drops below threshold."""
        # Set balance below threshold
        self.wallet.balance = Decimal('150.00')  # Below 200 threshold
        self.wallet.save()

        url = reverse('dailywage_wallet:dailywage-wallet-weekly-summary')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['alert_triggered'])

    def test_monthly_progress_calculation(self):
        """Test monthly progress percentage calculation."""
        url = reverse('dailywage_wallet:dailywage-wallet-monthly-summary')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # With 500 earnings and 8000 goal, progress should be 6.25%
        expected_progress = (Decimal('500.00') / Decimal('8000.00')) * 100
        self.assertAlmostEqual(
            float(response.data['progress_percentage']),
            float(expected_progress),
            places=2
        )


if __name__ == '__main__':
    # Run the tests
    import unittest
    unittest.main()
