"""
Wallet functionality for Couple Module.
Provides secure shared wallet operations with OTP protection and monitoring.
"""
from django.db import models, transaction
from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from decimal import Decimal
from modeltranslation.translator import translator, TranslationOptions


class CoupleWallet(models.Model):
    """
    Secure shared wallet model for couples.
    """
    partner1 = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='couple_wallet_partner1')
    partner2 = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='couple_wallet_partner2')
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    monthly_budget = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    emergency_fund = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    joint_goals = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    is_locked = models.BooleanField(default=False, help_text="Lock wallet for security reasons")
    alert_threshold = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), help_text="Threshold for low balance alerts")
    last_transaction_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['partner1', 'partner2']

    def __str__(self):
        return f"Couple Wallet: {self.partner1.username} & {self.partner2.username} - Balance: {self.balance}"

    @transaction.atomic
    def deposit(self, amount, description="Deposit", deposited_by=None):
        """Securely deposit money to shared wallet"""
        # Lock the wallet row for the duration of the transaction
        wallet = CoupleWallet.objects.select_for_update().get(pk=self.pk)

        if amount <= 0:
            raise ValueError("Deposit amount must be positive")

        self.balance += amount
        self.last_transaction_at = timezone.now()
        self.save()

        # Create transaction record
        CoupleWalletTransaction.objects.create(
            wallet=self,
            amount=amount,
            transaction_type='DEPOSIT',
            description=description,
            deposited_by=deposited_by,
            balance_after=self.balance
        )
        return self.balance

    @transaction.atomic
    def withdraw(self, amount, category='OTHER', description="Withdrawal", withdrawn_by=None):
        """Securely withdraw money from shared wallet"""
        # Lock the wallet row for the duration of the transaction
        wallet = CoupleWallet.objects.select_for_update().get(pk=self.pk)

        if amount <= 0:
            raise ValueError("Withdrawal amount must be positive")

        if self.balance < amount:
            raise ValueError("Insufficient balance")

        if self.is_locked:
            raise ValueError("Wallet is locked")

        self.balance -= amount
        self.last_transaction_at = timezone.now()
        self.save()

        # Create transaction record
        CoupleWalletTransaction.objects.create(
            wallet=self,
            amount=amount,
            transaction_type='WITHDRAWAL',
            category=category,
            description=description,
            withdrawn_by=withdrawn_by,
            balance_after=self.balance
        )
        return self.balance

    @transaction.atomic
    def transfer_to_emergency(self, amount, description="Emergency Fund Transfer"):
        """Transfer money to emergency fund"""
        # Lock the wallet row for the duration of the transaction
        wallet = CoupleWallet.objects.select_for_update().get(pk=self.pk)

        if amount <= 0:
            raise ValueError("Transfer amount must be positive")

        if self.balance < amount:
            raise ValueError("Insufficient balance")

        self.balance -= amount
        self.emergency_fund += amount
        self.last_transaction_at = timezone.now()
        self.save()

        # Create transaction record
        CoupleWalletTransaction.objects.create(
            wallet=self,
            amount=amount,
            transaction_type='EMERGENCY_TRANSFER',
            description=description,
            balance_after=self.balance,
            emergency_fund_after=self.emergency_fund
        )
        return self.balance

    @transaction.atomic
    def transfer_to_goals(self, amount, goal_name="Joint Goal"):
        """Transfer money to joint goals"""
        # Lock the wallet row for the duration of the transaction
        wallet = CoupleWallet.objects.select_for_update().get(pk=self.pk)

        if amount <= 0:
            raise ValueError("Transfer amount must be positive")

        if self.balance < amount:
            raise ValueError("Insufficient balance")

        self.balance -= amount
        self.joint_goals += amount
        self.last_transaction_at = timezone.now()
        self.save()

        # Create transaction record
        CoupleWalletTransaction.objects.create(
            wallet=self,
            amount=amount,
            transaction_type='GOAL_TRANSFER',
            description=f"Transfer to {goal_name}",
            balance_after=self.balance,
            joint_goals_after=self.joint_goals
        )
        return self.balance

    @property
    def available_balance(self):
        """Get available balance (excluding locked funds)"""
        return self.balance if not self.is_locked else Decimal('0.00')

    @property
    def total_savings(self):
        """Get total savings (emergency + goals)"""
        return self.emergency_fund + self.joint_goals


class CoupleWalletTransaction(models.Model):
    """
    Transaction history for couple wallets.
    """
    TRANSACTION_TYPES = [
        ('DEPOSIT', _('Deposit')),
        ('WITHDRAWAL', _('Withdrawal')),
        ('EMERGENCY_TRANSFER', _('Emergency Fund Transfer')),
        ('GOAL_TRANSFER', _('Joint Goal Transfer')),
        ('BUDGET_ALLOCATION', _('Budget Allocation')),
        ('EXPENSE_SPLIT', _('Expense Split')),
    ]

    wallet = models.ForeignKey(CoupleWallet, on_delete=models.CASCADE, related_name='transactions')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    category = models.CharField(max_length=50, default='OTHER', help_text="Expense category (Rent, Groceries, etc.)")
    description = models.TextField()
    deposited_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='couple_deposits')
    withdrawn_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='couple_withdrawals')
    balance_after = models.DecimalField(max_digits=12, decimal_places=2)
    emergency_fund_after = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    joint_goals_after = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.wallet.partner1.username} & {self.wallet.partner2.username} - {self.transaction_type}: {self.amount}"


class CoupleWalletOTPRequest(models.Model):
    """
    OTP requests for couple wallet operations.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='couple_otp_requests')
    wallet = models.ForeignKey(CoupleWallet, on_delete=models.CASCADE, related_name='otp_requests')
    operation_type = models.CharField(max_length=50, help_text="Type of operation requiring OTP")
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    description = models.TextField()
    otp_code = models.CharField(max_length=6)
    cache_key = models.CharField(max_length=255, default='', help_text="Cache key for OTP validation")
    is_used = models.BooleanField(default=False)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Couple OTP for {self.user.username} - {self.operation_type}"

    def is_expired(self):
        return timezone.now() > self.expires_at

    def mark_as_used(self):
        self.is_used = True
        self.save()


class CouplePersonalWallet(models.Model):
    """
    Private account for individual spending within a couple context.
    """
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='couple_personal_wallet')
    couple_link = models.ForeignKey('couple_module.CoupleLink', on_delete=models.CASCADE, related_name='personal_wallets', null=True, blank=True)
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    is_visible_to_partner = models.BooleanField(default=False, help_text="Allow partner to view this balance")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Personal Wallet: {self.user.username} - Balance: {self.balance}"


class JointGoal(models.Model):
    """
    Model for tracking shared goals like Vacation, Home Down Payment, etc.
    """
    couple = models.ForeignKey('couple_module.CoupleLink', on_delete=models.CASCADE, related_name='joint_goals_list')
    name = models.CharField(max_length=100)
    target_amount = models.DecimalField(max_digits=12, decimal_places=2)
    current_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    deadline = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def progress_percentage(self):
        if self.target_amount > 0:
            return round(min((self.current_amount / self.target_amount) * 100, Decimal('100.00')), 2)
        return 0

    def __str__(self):
        return f"Goal: {self.name} ({self.current_amount}/{self.target_amount})"

# Translation options for model fields
class CoupleWalletTransactionTranslationOptions(TranslationOptions):
    fields = ('description',)

# Translation options are now in translation.py
