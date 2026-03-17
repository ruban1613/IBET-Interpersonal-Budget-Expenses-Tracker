from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from .models import IncomeSource, EmergencyFund, FinancialGoal, ExpenseAlert
from .models_wallet import IndividualWallet

User = get_user_model()


class IndividualModuleTestCase(TestCase):
    """Test cases for individual module models"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_income_source_creation(self):
        """Test creating an income source"""
        income = IncomeSource.objects.create(
            user=self.user,
            name='Salary',
            amount=50000.00,
            frequency='MONTHLY'
        )
        self.assertEqual(income.user, self.user)
        self.assertEqual(income.amount, 50000.00)

    def test_emergency_fund_creation(self):
        """Test creating an emergency fund"""
        fund = EmergencyFund.objects.create(
            user=self.user,
            target_amount=200000.00,
            current_amount=50000.00,
            monthly_contribution=10000.00
        )
        self.assertEqual(fund.progress_percentage, 25.0)

    def test_financial_goal_creation(self):
        """Test creating a financial goal"""
        from datetime import date
        goal = FinancialGoal.objects.create(
            user=self.user,
            name='Vacation Fund',
            target_amount=100000.00,
            target_date=date.today()
        )
        self.assertEqual(goal.status, 'ACTIVE')


class IndividualModuleAPITestCase(APITestCase):
    """Test cases for individual module API endpoints"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)

    def test_income_source_list(self):
        """Test listing income sources"""
        IncomeSource.objects.create(
            user=self.user,
            name='Salary',
            amount=50000.00
        )
        url = reverse('income-source-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_emergency_fund_create(self):
        """Test creating emergency fund"""
        url = reverse('emergency-fund-list')
        data = {
            'target_amount': 200000.00,
            'current_amount': 50000.00,
            'monthly_contribution': 10000.00
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_financial_goal_create(self):
        """Test creating financial goal"""
        from datetime import date
        url = reverse('financial-goal-list')
        data = {
            'name': 'New Car',
            'target_amount': 500000.00,
            'target_date': date.today().isoformat()
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_wallet_management(self):
        """Test wallet management operations"""
        # Create IndividualWallet instead of Wallet
        IndividualWallet.objects.create(user=self.user, balance=1000.00)

        url = reverse('individual_wallet:individual-wallet-balance')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(str(response.data['balance']), '1000.00')
