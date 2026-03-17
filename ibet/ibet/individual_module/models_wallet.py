"""
Wallet functionality for Individual Module.
Provides secure wallet operations with OTP protection and monitoring.
"""
from django.db import models, transaction
from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from decimal import Decimal
from modeltranslation.translator import translator, TranslationOptions


class IndividualWallet(models.Model):
    """
    Secure wallet model for individual users.
    """
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='individual_wallet')
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    total_deposits = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    monthly_budget = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    savings_goal = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    current_savings = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    alert_threshold = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), help_text="Threshold for low balance alerts")
    is_locked = models.BooleanField(default=False, help_text="Lock wallet for security reasons")
    last_transaction_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Individual Wallet: {self.user.username} - Balance: {self.balance}"

    @transaction.atomic
    def deposit(self, amount, description="Deposit"):
        """Securely deposit money to wallet"""
        # Lock the wallet row for the duration of the transaction
        wallet = IndividualWallet.objects.select_for_update().get(pk=self.pk)

        if amount <= 0:
            raise ValueError("Deposit amount must be positive")

        self.balance += amount
        self.total_deposits += amount
        self.last_transaction_at = timezone.now()
        self.save()

        # Create transaction record
        IndividualWalletTransaction.objects.create(
            wallet=self,
            amount=amount,
            transaction_type='DEPOSIT',
            description=description,
            balance_after=self.balance
        )
        return self.balance

    @transaction.atomic
    def withdraw(self, amount, description="Withdrawal"):
        """Securely withdraw money from wallet"""
        # Lock the wallet row for the duration of the transaction
        wallet = IndividualWallet.objects.select_for_update().get(pk=self.pk)

        if amount <= 0:
            raise ValueError("Withdrawal amount must be positive")

        if self.balance < amount:
            raise ValueError("Individual Wallet: Insufficient balance")

        if self.is_locked:
            raise ValueError("Wallet is locked")

        self.balance -= amount
        self.last_transaction_at = timezone.now()
        self.save()

        # Create transaction record
        IndividualWalletTransaction.objects.create(
            wallet=self,
            amount=amount,
            transaction_type='WITHDRAWAL',
            description=description,
            balance_after=self.balance
        )
        return self.balance

    @transaction.atomic
    def transfer_to_goal(self, amount, goal_name):
        """Transfer money to savings goal"""
        # Lock the wallet row for the duration of the transaction
        wallet = IndividualWallet.objects.select_for_update().get(pk=self.pk)

        if amount <= 0:
            raise ValueError("Transfer amount must be positive")

        if self.balance < amount:
            raise ValueError("Individual Wallet: Insufficient balance")

        self.balance -= amount
        self.current_savings += amount
        self.last_transaction_at = timezone.now()
        self.save()

        # Create transaction record
        IndividualWalletTransaction.objects.create(
            wallet=self,
            amount=amount,
            transaction_type='SAVINGS',
            description=f"Transfer to {goal_name}",
            balance_after=self.balance
        )
        return self.balance

    @transaction.atomic
    def withdraw_from_savings(self, amount, description="Savings Withdrawal"):
        """Securely withdraw money from savings wallet"""
        # Lock the wallet row for the duration of the transaction
        wallet = IndividualWallet.objects.select_for_update().get(pk=self.pk)

        if amount <= 0:
            raise ValueError("Withdrawal amount must be positive")

        if self.current_savings < amount:
            raise ValueError("Insufficient savings balance")

        if self.is_locked:
            raise ValueError("Wallet is locked")

        self.current_savings -= amount
        self.balance += amount  # Transfer back to main balance or just withdraw
        self.last_transaction_at = timezone.now()
        self.save()

        # Create transaction record
        IndividualWalletTransaction.objects.create(
            wallet=self,
            amount=amount,
            transaction_type='WITHDRAWAL',
            description=f"Savings: {description}",
            balance_after=self.balance
        )
        return self.current_savings

    @property
    def available_balance(self):
        """Get available balance (excluding locked funds)"""
        return self.balance if not self.is_locked else Decimal('0.00')


class IndividualWalletTransaction(models.Model):
    """
    Transaction history for individual wallets.
    """
    TRANSACTION_TYPES = [
        ('DEPOSIT', _('Deposit')),
        ('WITHDRAWAL', _('Withdrawal')),
        ('SAVINGS', _('Savings Transfer')),
        ('BUDGET', _('Budget Allocation')),
        ('INCOME', _('Income Addition')),
    ]

    wallet = models.ForeignKey(IndividualWallet, on_delete=models.CASCADE, related_name='transactions')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    description = models.TextField()
    balance_after = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.wallet.user.username} - {self.transaction_type}: {self.amount}"


class IndividualWalletOTPRequest(models.Model):
    """
    OTP requests for individual wallet operations.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='individual_otp_requests')
    operation_type = models.CharField(max_length=50, help_text="Type of operation requiring OTP")
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    description = models.TextField()
    otp_code = models.CharField(max_length=6)
    is_used = models.BooleanField(default=False)
    expires_at = models.DateTimeField()
    cache_key = models.CharField(max_length=255, null=True, blank=True, help_text="Cache key for OTP validation")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"OTP for {self.user.username} - {self.operation_type}"

    def is_expired(self):
        return timezone.now() > self.expires_at

    def mark_as_used(self):
        self.is_used = True
        self.save()


# Translation options for model fields
class IndividualWalletTransactionTranslationOptions(TranslationOptions):
    fields = ('description',)

# Translation options are now in translation.py
