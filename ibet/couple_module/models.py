from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from decimal import Decimal
from modeltranslation.translator import translator, TranslationOptions

User = get_user_model()


class CoupleLink(models.Model):
    """
    Model to link two users as a couple
    """
    user1 = models.OneToOneField(User, on_delete=models.CASCADE, related_name='couple_user1')
    user2 = models.OneToOneField(User, on_delete=models.CASCADE, related_name='couple_user2')
    linked_date = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user1.username} & {self.user2.username}"

    @property
    def partner_of(self):
        """Get the partner of a given user"""
        def get_partner(user):
            if user == self.user1:
                return self.user2
            elif user == self.user2:
                return self.user1
            return None
        return get_partner


class SharedWallet(models.Model):
    """
    Model for shared wallet between couples
    """
    couple = models.OneToOneField(CoupleLink, on_delete=models.CASCADE, related_name='shared_wallet')
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    monthly_budget = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Shared Wallet: {self.couple} - Balance: {self.balance}"

    def add_funds(self, amount, contributor):
        """Add funds to the shared wallet"""
        self.balance += amount
        self.save()

        # Create transaction record
        SharedTransaction.objects.create(
            wallet=self,
            amount=amount,
            transaction_type='DEPOSIT',
            description=f"Deposit by {contributor.username}",
            performed_by=contributor
        )

    def withdraw_funds(self, amount, withdrawer):
        """Withdraw funds from the shared wallet"""
        if self.balance >= amount:
            self.balance -= amount
            self.save()

            # Create transaction record
            SharedTransaction.objects.create(
                wallet=self,
                amount=amount,
                transaction_type='WITHDRAWAL',
                description=f"Withdrawal by {withdrawer.username}",
                performed_by=withdrawer
            )
            return True
        return False


class SpendingRequest(models.Model):
    """
    Model for spending requests that require partner approval
    """
    STATUS_CHOICES = [
        ('PENDING', _('Pending')),
        ('APPROVED', _('Approved')),
        ('REJECTED', _('Rejected')),
        ('EXPIRED', _('Expired')),
    ]

    requester = models.ForeignKey(User, on_delete=models.CASCADE, related_name='spending_requests')
    couple = models.ForeignKey(CoupleLink, on_delete=models.CASCADE, related_name='spending_requests')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()
    category = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    requested_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField()

    class Meta:
        ordering = ['-requested_at']

    def __str__(self):
        return f"Request by {self.requester.username}: {self.amount} for {self.description}"

    def approve(self, approver):
        """Approve the spending request"""
        if self.status == 'PENDING' and approver in [self.couple.user1, self.couple.user2]:
            # Withdraw from shared wallet (CoupleWallet)
            from .models_wallet import CoupleWallet
            try:
                wallet = CoupleWallet.objects.get(
                    models.Q(partner1=self.couple.user1, partner2=self.couple.user2) |
                    models.Q(partner1=self.couple.user2, partner2=self.couple.user1)
                )
                if wallet.withdraw(amount=self.amount, category=self.category, description=self.description, withdrawn_by=self.requester):
                    # Only mark as APPROVED if withdrawal was successful
                    self.status = 'APPROVED'
                    self.responded_at = timezone.now()
                    self.save()
                    return True
            except CoupleWallet.DoesNotExist:
                return False
        return False

    def reject(self, rejector):
        """Reject the spending request"""
        if self.status == 'PENDING' and rejector in [self.couple.user1, self.couple.user2]:
            self.status = 'REJECTED'
            self.responded_at = timezone.now()
            self.save()
            return True
        return False

    @property
    def is_expired(self):
        """Check if the request has expired"""
        return timezone.now() > self.expires_at

    def save(self, *args, **kwargs):
        # Set expiration to 7 days from creation if not set
        if not self.expires_at:
            if not self.requested_at:
                self.requested_at = timezone.now()
            self.expires_at = self.requested_at + timezone.timedelta(days=7)
        super().save(*args, **kwargs)


class SharedTransaction(models.Model):
    """
    Model to track all transactions in the shared wallet
    """
    TRANSACTION_TYPES = [
        ('DEPOSIT', _('Deposit')),
        ('WITHDRAWAL', _('Withdrawal')),
        ('EXPENSE', _('Expense')),
    ]

    wallet = models.ForeignKey(SharedWallet, on_delete=models.CASCADE, related_name='transactions')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    description = models.TextField()
    performed_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='shared_transactions')
    transaction_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-transaction_date']

    def __str__(self):
        return f"{self.transaction_type}: {self.amount} by {self.performed_by.username}"


class CoupleDashboard(models.Model):
    """
    Dashboard model for couple financial overview
    """
    couple = models.OneToOneField(CoupleLink, on_delete=models.CASCADE, related_name='dashboard')
    total_contributions = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_expenses = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    pending_requests = models.PositiveIntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)

    @property
    def net_balance(self):
        """Calculate net balance"""
        return self.total_contributions - self.total_expenses

    def __str__(self):
        return f"Dashboard for {self.couple}"


class CoupleAlert(models.Model):
    """
    Model for couple-specific alerts and notifications
    """
    ALERT_TYPES = [
        ('BUDGET_WARNING', _('Budget Warning')),
        ('REQUEST_APPROVAL', _('Request Needs Approval')),
        ('LOW_BALANCE', _('Low Balance Alert')),
        ('MONTHLY_REPORT', _('Monthly Report')),
    ]

    couple = models.ForeignKey(CoupleLink, on_delete=models.CASCADE, related_name='alerts')
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPES)
    title = models.CharField(max_length=100)
    message = models.TextField()
    is_read_user1 = models.BooleanField(default=False)
    is_read_user2 = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Alert for {self.couple}: {self.title}"

    def mark_as_read(self, user):
        """Mark alert as read for a specific user"""
        if user == self.couple.user1:
            self.is_read_user1 = True
        elif user == self.couple.user2:
            self.is_read_user2 = True
        self.save()

    @property
    def is_read_by_both(self):
        """Check if both partners have read the alert"""
        return self.is_read_user1 and self.is_read_user2


# Translation options for model fields
class SpendingRequestTranslationOptions(TranslationOptions):
    fields = ('description', 'category')

class SharedTransactionTranslationOptions(TranslationOptions):
    fields = ('description',)

class CoupleAlertTranslationOptions(TranslationOptions):
    fields = ('title', 'message')

# Translation options are now in translation.py
