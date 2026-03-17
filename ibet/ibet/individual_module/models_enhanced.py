"""
Enhanced Individual Module Models
Includes dual wallet system (main + savings), expense tracking, and smart alerts.
"""
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from decimal import Decimal
from modeltranslation.translator import translator, TranslationOptions
from django.db.models import Sum, Avg, Count
from datetime import timedelta
import random


class IndividualSavingsWallet(models.Model):
    """
    Separate Savings Wallet for individuals.
    Money can be transferred from main wallet to savings with OTP verification.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='individual_savings_wallet'
    )
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    total_deposits = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    total_withdrawals = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Savings Wallet: {self.user.username} - Balance: {self.balance}"

    @transaction.atomic
    def deposit(self, amount, description="Savings Deposit"):
        """Deposit money into savings wallet"""
        wallet = IndividualSavingsWallet.objects.select_for_update().get(pk=self.pk)
        
        if amount <= 0:
            raise ValueError("Deposit amount must be positive")
        
        wallet.balance += amount
        wallet.total_deposits += amount
        wallet.last_transaction_at = timezone.now()
        wallet.save()
        
        # Create transaction record
        SavingsTransaction.objects.create(
            savings_wallet=self,
            amount=amount,
            transaction_type='DEPOSIT',
            description=description,
            balance_after=wallet.balance
        )
        return wallet.balance

    @transaction.atomic
    def withdraw(self, amount, description="Savings Withdrawal"):
        """Withdraw money from savings wallet"""
        wallet = IndividualSavingsWallet.objects.select_for_update().get(pk=self.pk)
        
        if amount <= 0:
            raise ValueError("Withdrawal amount must be positive")
        
        if wallet.balance < amount:
            raise ValueError("Insufficient savings balance")
        
        wallet.balance -= amount
        wallet.total_withdrawals += amount
        wallet.last_transaction_at = timezone.now()
        wallet.save()
        
        # Create transaction record
        SavingsTransaction.objects.create(
            savings_wallet=self,
            amount=amount,
            transaction_type='WITHDRAWAL',
            description=description,
            balance_after=wallet.balance
        )
        return wallet.balance


class SavingsTransaction(models.Model):
    """Transaction history for savings wallet"""
    TRANSACTION_TYPES = [
        ('DEPOSIT', _('Deposit')),
        ('WITHDRAWAL', _('Withdrawal')),
    ]
    
    savings_wallet = models.ForeignKey(
        IndividualSavingsWallet, 
        on_delete=models.CASCADE, 
        related_name='transactions'
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    description = models.TextField()
    balance_after = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.savings_wallet.user.username} - {self.transaction_type}: {self.amount}"


class ExpenseCategory(models.Model):
    """Categories for expense tracking"""
    name = models.CharField(max_length=50, unique=True)
    icon = models.CharField(max_length=20, default='💰')
    color = models.CharField(max_length=10, default='#3498db')
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name


class IndividualExpense(models.Model):
    """
    Expense tracking with categories for individual users.
    Tracks spending against deposited amount.
    """
    CATEGORY_CHOICES = [
        ('FOOD', 'Food & Dining'),
        ('TRANSPORT', 'Transportation'),
        ('UTILITIES', 'Utilities'),
        ('ENTERTAINMENT', 'Entertainment'),
        ('SHOPPING', 'Shopping'),
        ('HEALTH', 'Healthcare'),
        ('EDUCATION', 'Education'),
        ('BILLS', 'Bills & Payments'),
        ('OTHER', 'Other'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='individual_expenses'
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    description = models.TextField(blank=True, default='')
    expense_date = models.DateField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-expense_date', '-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.category}: {self.amount}"


class SpendingAlert(models.Model):
    """
    Alerts for spending thresholds and anomalies.
    """
    ALERT_TYPES = [
        ('SPENT_50', '50% Spent'),
        ('SPENT_80', '80% Spent'),
        ('SPENT_100', '100% Spent'),
        ('ANOMALY', 'Unusual Spending Detected'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='individual_spending_alerts'
    )
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPES)
    title = models.CharField(max_length=100)
    message = models.TextField()
    amount_spent = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    total_deposited = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    is_read = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def mark_as_read(self):
        self.is_read = True
        self.read_at = timezone.now()
        self.save()
    
    def __str__(self):
        return f"{self.user.username} - {self.alert_type}: {self.percentage}%"


class SpendingAnomalyDetector:
    """
    Detects unusual spending patterns.
    Currently detects: unusually large single transactions
    """
    
    # Threshold for anomaly detection (amount greater than this × average = anomaly)
    ANOMALY_MULTIPLIER = 3.0
    
    # Minimum number of transactions needed for anomaly detection
    MIN_TRANSACTIONS = 3
    
    @classmethod
    def detect_anomaly(cls, user, amount):
        """
        Check if the given amount is unusually large for this user.
        Returns True if anomaly detected, False otherwise.
        """
        # Get user's average spending
        expenses = IndividualExpense.objects.filter(user=user)
        
        if expenses.count() < cls.MIN_TRANSACTIONS:
            # Not enough data for anomaly detection
            return False
        
        avg_spending = expenses.aggregate(avg=Avg('amount'))['avg'] or Decimal('0')
        
        if avg_spending == 0:
            return False
        
        # Check if current amount is unusually large
        threshold = avg_spending * Decimal(str(cls.ANOMALY_MULTIPLIER))
        
        return amount > threshold
    
    @classmethod
    def get_average_spending(cls, user):
        """Get average spending amount for user"""
        result = IndividualExpense.objects.filter(user=user).aggregate(
            avg=Avg('amount'),
            total=Sum('amount'),
            count=Count('id')
        )
        return {
            'average': result['avg'] or Decimal('0'),
            'total': result['total'] or Decimal('0'),
            'count': result['count'] or 0
        }


class SpendingTracker:
    """
    Tracks spending against deposited amount and triggers alerts.
    """
    
    @classmethod
    def check_spending_threshold(cls, user):
        """
        Check if spending has crossed 50% or 80% threshold.
        Returns list of triggered alerts.
        """
        # Get total deposited (sum of all deposits)
        from individual_module.models_wallet import IndividualWallet
        
        try:
            wallet = IndividualWallet.objects.get(user=user)
            total_deposited = wallet.balance  # Current balance + withdrawn = total deposited
            
            # Calculate total spent from expenses
            total_spent = IndividualExpense.objects.filter(
                user=user
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
            
            if total_deposited <= 0:
                return []
            
            spent_percentage = (total_spent / total_deposited) * 100
            
            alerts_created = []
            
            # Check 50% threshold
            if spent_percentage >= 50:
                alert, created = SpendingAlert.objects.get_or_create(
                    user=user,
                    alert_type='SPENT_50',
                    is_active=True,
                    defaults={
                        'title': '50% Spending Alert',
                        'message': f'You have spent 50% (₹{total_spent}) of your total deposited amount (₹{total_deposited}).',
                        'amount_spent': total_spent,
                        'total_deposited': total_deposited,
                        'percentage': spent_percentage
                    }
                )
                if created:
                    alerts_created.append(alert)
            
            # Check 80% threshold
            if spent_percentage >= 80:
                alert, created = SpendingAlert.objects.get_or_create(
                    user=user,
                    alert_type='SPENT_80',
                    is_active=True,
                    defaults={
                        'title': '80% Spending Alert',
                        'message': f'Warning! You have spent 80% (₹{total_spent}) of your total deposited amount (₹{total_deposited}).',
                        'amount_spent': total_spent,
                        'total_deposited': total_deposited,
                        'percentage': spent_percentage
                    }
                )
                if created:
                    alerts_created.append(alert)
            
            return alerts_created
            
        except IndividualWallet.DoesNotExist:
            return []
    
    @classmethod
    @transaction.atomic
    def record_expense_and_check_alerts(cls, user, amount, category, description=''):
        """
        Record an expense and check for alerts/anomalies.
        Automatically deducts the amount from the individual's wallet.
        Returns expense object and list of alerts created.
        """
        from individual_module.models_wallet import IndividualWallet
        
        # 1. Deduct from wallet first to ensure sufficient funds
        try:
            wallet = IndividualWallet.objects.select_for_update().get(user=user)
            wallet.withdraw(amount, description=f"Expense ({category}): {description}")
        except IndividualWallet.DoesNotExist:
            # Fallback for users without a wallet
            pass
        except ValueError as e:
            # Re-raise insufficient funds or invalid amount errors
            raise e

        # 2. Create expense record
        expense = IndividualExpense.objects.create(
            user=user,
            amount=amount,
            category=category,
            description=description
        )
        
        # Use IndividualDashboard from models.py if possible, but here we'll assume it exists or can be created
        from .models import IndividualDashboard
        try:
            dashboard = IndividualDashboard.objects.select_for_update().get(user=user)
            dashboard.total_expenses += amount
            dashboard.save()
        except IndividualDashboard.DoesNotExist:
            IndividualDashboard.objects.create(
                user=user,
                total_expenses=amount,
                monthly_budget=wallet.monthly_budget if 'wallet' in locals() else Decimal('0.00'),
                savings_goal=wallet.savings_goal if 'wallet' in locals() else Decimal('0.00'),
                current_savings=wallet.current_savings if 'wallet' in locals() else Decimal('0.00')
            )
        
        alerts_created = []
        
        # Check for anomaly
        if SpendingAnomalyDetector.detect_anomaly(user, amount):
            avg_data = SpendingAnomalyDetector.get_average_spending(user)
            alert = SpendingAlert.objects.create(
                user=user,
                alert_type='ANOMALY',
                title='Unusual Spending Detected',
                message=f'This expense (₹{amount}) is unusually large. Your average spending is ₹{avg_data["average"]:.2f}.',
                amount_spent=amount,
                percentage=(amount / avg_data['average'] * 100) if avg_data['average'] > 0 else 0
            )
            alerts_created.append(alert)
        
        # Check spending thresholds
        threshold_alerts = cls.check_spending_threshold(user)
        alerts_created.extend(threshold_alerts)
        
        return expense, alerts_created


# Translation options
class IndividualExpenseTranslationOptions(TranslationOptions):
    fields = ('description',)

class SpendingAlertTranslationOptions(TranslationOptions):
    fields = ('title', 'message')
