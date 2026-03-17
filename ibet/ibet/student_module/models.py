# c:\Users\Hp\Documents\budget\IBET\student_module\models.py

from django.contrib.auth.models import AbstractUser
from django.db import models, transaction
from django.conf import settings
from django.db.models import Sum
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from modeltranslation.translator import translator, TranslationOptions

# Step 1: Define User Personas using a TextChoices class for clarity.
class UserPersona(models.TextChoices):
    STUDENT = 'STUDENT', 'Student'
    STUDENT_ACADEMIC = 'STUDENT_ACADEMIC', 'Student (Academic)'
    PARENT = 'PARENT', 'Parent'
    INDIVIDUAL = 'INDIVIDUAL', 'Individual'
    COUPLE = 'COUPLE', 'Couple'
    INSTITUTE_OWNER = 'INSTITUTE_OWNER', 'Institute Owner'
    INSTITUTE_TEACHER = 'INSTITUTE_TEACHER', 'Institute Teacher'
    RETIREE = 'RETIREE', 'Retiree'


# New models for Daily Allowance System
class DailyAllowance(models.Model):
    """
    Tracks individual daily allowance for each day of the month.
    This implements the cumulative daily allowance system where:
    - Monthly allowance is divided equally across days
    - Students can spend from available days
    - Future days get locked if overspent
    - At midnight, new day's allowance becomes available
    """
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='daily_allowances'
    )
    date = models.DateField()
    daily_amount = models.DecimalField(max_digits=10, decimal_places=2)
    amount_spent = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    remaining_amount = models.DecimalField(max_digits=10, decimal_places=2)
    is_available = models.BooleanField(default=True)
    is_locked = models.BooleanField(default=False)
    lock_reason = models.CharField(max_length=255, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['student', 'date']
        ordering = ['date']

    def __str__(self):
        return f"Daily allowance for {self.student.username} on {self.date}: {self.remaining_amount}/{self.daily_amount}"

    @property
    def is_fully_spent(self):
        return self.remaining_amount <= 0

    @property
    def spending_percentage(self):
        if self.daily_amount > 0:
            return (self.amount_spent / self.daily_amount) * 100
        return 0


class CumulativeSpendingTracker(models.Model):
    """
    Tracks the cumulative spending across all available days.
    This helps quickly determine total available funds.
    """
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='cumulative_spending'
    )
    month = models.IntegerField()
    year = models.IntegerField()
    total_allocated = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_spent = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_available = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    days_available = models.IntegerField(default=0)
    current_day_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['student', 'month', 'year']

    def __str__(self):
        return f"Cumulative spending for {self.student.username} ({self.month}/{self.year}): {self.total_available} available"


class PendingSpendingRequest(models.Model):
    """
    Tracks pending spending requests that require parent approval.
    When student exceeds available funds, they can request parent OTP.
    """
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        APPROVED = 'APPROVED', 'Approved'
        REJECTED = 'REJECTED', 'Rejected'
        EXPIRED = 'EXPIRED', 'Expired'

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='pending_spending_requests'
    )
    parent = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='student_spending_requests'
    )
    amount_requested = models.DecimalField(max_digits=10, decimal_places=2)
    amount_used_today = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    otp_code = models.CharField(max_length=6, null=True, blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    request_message = models.TextField(blank=True, default="")
    response_message = models.TextField(blank=True, default="")
    expires_at = models.DateTimeField(null=True, blank=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Spending request from {self.student.username}: {self.amount_requested} ({self.status})"

    def is_expired(self):
        """Check if the request has expired based on current time."""
        if not self.expires_at:
            return False
        from django.utils import timezone
        return timezone.now() > self.expires_at

class User(AbstractUser):
    # Unique Identification Number (e.g., IBET-123456)
    uid = models.CharField(max_length=20, unique=True, null=True, blank=True)
    phone = models.CharField(max_length=20, null=True, blank=True)
    
    # This field is the core of your multi-persona system.
    persona = models.CharField(
        max_length=20,
        choices=UserPersona.choices,
        null=True, # Allow null until the user selects their persona after registration.
        blank=True
    )
    transaction_pin = models.CharField(max_length=128, null=True, blank=True) # Hashed PIN for parents

    def save(self, *args, **kwargs):
        if not self.uid:
            self.uid = self.generate_unique_uid()
        super().save(*args, **kwargs)

    def generate_unique_uid(self):
        import random
        import string
        while True:
            # Format: IBET- followed by 6 random digits
            new_uid = 'IBET-' + ''.join(random.choices(string.digits, k=6))
            if not User.objects.filter(uid=new_uid).exists():
                return new_uid

    def set_transaction_pin(self, raw_pin):
        from django.contrib.auth.hashers import make_password
        self.transaction_pin = make_password(raw_pin)
        self.save()

    def check_transaction_pin(self, raw_pin):
        from django.contrib.auth.hashers import check_password
        if not self.transaction_pin:
            return False
        return check_password(raw_pin, self.transaction_pin)

# Step 3: Create a Wallet model. This is a central concept for many personas.
class Wallet(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='wallet')
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00) # Main Allowance Balance
    special_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00) # Pocket Money Balance
    last_transaction_at = models.DateTimeField(null=True, blank=True)
    is_locked = models.BooleanField(default=False)
    locked_at = models.DateTimeField(null=True, blank=True)
    failed_attempts = models.IntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username}'s Wallet: {self.balance} (Main), {self.special_balance} (Special)"

    @transaction.atomic
    def deposit_main(self, amount, description="Main Deposit"):
        if amount <= 0:
            raise ValueError("Deposit amount must be positive")
        self.balance += amount
        self.last_transaction_at = timezone.now()
        self.save()
        WalletTransaction.objects.create(
            wallet=self,
            wallet_type=WalletTransaction.WalletType.MAIN,
            transaction_type=WalletTransaction.TransactionType.DEPOSIT,
            amount=amount,
            balance_after=self.balance,
            description=description
        )
        return self.balance

    @transaction.atomic
    def withdraw_main(self, amount, description="Main Withdrawal"):
        if amount <= 0:
            raise ValueError("Withdrawal amount must be positive")
        if self.balance < amount:
            raise ValueError(f"Core Wallet: Insufficient balance (Current: ₹{self.balance}, Requested: ₹{amount})")
        if self.is_locked:
            raise ValueError("Wallet is locked")
        self.balance -= amount
        self.last_transaction_at = timezone.now()
        self.save()
        WalletTransaction.objects.create(
            wallet=self,
            wallet_type=WalletTransaction.WalletType.MAIN,
            transaction_type=WalletTransaction.TransactionType.WITHDRAWAL,
            amount=amount,
            balance_after=self.balance,
            description=description
        )
        return self.balance

    @transaction.atomic
    def deposit_special(self, amount, description="Special Deposit"):
        if amount <= 0:
            raise ValueError("Deposit amount must be positive")
        self.special_balance += amount
        self.last_transaction_at = timezone.now()
        self.save()
        
        # 1. WalletTransaction (Internal tracking)
        WalletTransaction.objects.create(
            wallet=self,
            wallet_type=WalletTransaction.WalletType.SPECIAL,
            transaction_type=WalletTransaction.TransactionType.DEPOSIT,
            amount=amount,
            balance_after=self.special_balance,
            description=description
        )
        
        # 2. General Transaction (History visibility)
        Transaction.objects.create(
            user=self.user,
            amount=amount,
            transaction_type=Transaction.TransactionType.INCOME,
            description=f"[Pocket Money] {description}",
            transaction_date=timezone.now().date()
        )
        return self.special_balance

    @transaction.atomic
    def withdraw_special(self, amount, description="Special Withdrawal"):
        if amount <= 0:
            raise ValueError("Withdrawal amount must be positive")
        if self.special_balance < amount:
            raise ValueError("Insufficient special balance")
        self.special_balance -= amount
        self.last_transaction_at = timezone.now()
        self.save()
        
        # 1. WalletTransaction (Internal tracking)
        WalletTransaction.objects.create(
            wallet=self,
            wallet_type=WalletTransaction.WalletType.SPECIAL,
            transaction_type=WalletTransaction.TransactionType.WITHDRAWAL,
            amount=amount,
            balance_after=self.special_balance,
            description=description
        )
        
        # 2. General Transaction (History visibility)
        Transaction.objects.create(
            user=self.user,
            amount=amount,
            transaction_type=Transaction.TransactionType.EXPENSE,
            description=f"[Pocket Money] {description}",
            transaction_date=timezone.now().date()
        )
        return self.special_balance


class WalletTransaction(models.Model):
    """
    History of wallet transactions for both Main and Special wallets.
    """
    class WalletType(models.TextChoices):
        MAIN = 'MAIN', 'Main Allowance'
        SPECIAL = 'SPECIAL', 'Special Pocket Money'

    class TransactionType(models.TextChoices):
        DEPOSIT = 'DEPOSIT', 'Deposit'
        WITHDRAWAL = 'WITHDRAWAL', 'Withdrawal'
        TRANSFER = 'TRANSFER', 'Transfer'
        ALLOWANCE = 'ALLOWANCE', 'Monthly Allowance'

    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='transactions')
    wallet_type = models.CharField(max_length=10, choices=WalletType.choices, default=WalletType.MAIN)
    transaction_type = models.CharField(max_length=10, choices=TransactionType.choices)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    balance_after = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.wallet.user.username} - {self.wallet_type} - {self.transaction_type}: {self.amount}"

# Step 4: Model for the Parent-Student relationship.
class ParentStudentLink(models.Model):
    parent = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='linked_students')
    student = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='linked_parent')

    def __str__(self):
        return f"Parent: {self.parent.username} -> Student: {self.student.username}"


class AllowanceContribution(models.Model):
    """
    History of parent contributions to student allowance.
    Used for showing the "Monthly Budget" history in Parent Section.
    """
    parent = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_allowances')
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='received_allowances')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    day = models.IntegerField()
    month = models.IntegerField()
    year = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Contribution of {self.amount} to {self.student.username} on {self.day}/{self.month}/{self.year}"

# Step 5: Model for the "Couples" spending approval workflow.
class SpendingRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        APPROVED = 'APPROVED', 'Approved'
        REJECTED = 'REJECTED', 'Rejected'

    # A shared wallet would be ideal here, but for simplicity, we can link to the requester's partner.
    requester = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_requests')
    approver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='received_requests')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=255)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

# Your existing models are great. We just need to ensure they link to the User.
class Category(models.Model):
    # Make categories user-specific so one user doesn't see another's categories.
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, verbose_name=_("Name"), help_text=_("Enter your name"))

    def __str__(self):
        return self.name

class Budget(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    start_date = models.DateField()
    end_date = models.DateField()

    def __str__(self):
        return f"{self.user.username}'s budget for {self.category.name}"

class Transaction(models.Model):
    class TransactionType(models.TextChoices):
        INCOME = 'INC', 'Income'
        EXPENSE = 'EXP', 'Expense'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_type = models.CharField(max_length=3, choices=TransactionType.choices)
    transaction_date = models.DateField()
    description = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"{self.transaction_type} of {self.amount} for {self.user.username}"

# New models for student features
class Reminder(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    budget = models.ForeignKey(Budget, on_delete=models.CASCADE, null=True, blank=True)
    alert_percentage = models.IntegerField(choices=[(50, '50%'), (70, '70%'), (100, '100%')], default=50)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Reminder for {self.user.username} at {self.alert_percentage}%"

class ChatMessage(models.Model):
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='received_messages')
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"Message from {self.sender.username} to {self.receiver.username}"

class DailyLimit(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    daily_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    current_spent = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    date = models.DateField(default=timezone.now)

    def __str__(self):
        return f"Daily limit for {self.user.username}: {self.daily_amount}"

class OTPRequest(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='student_otp_requests')
    parent = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='parent_otp_responses')
    otp_code = models.CharField(max_length=6)
    amount_requested = models.DecimalField(max_digits=10, decimal_places=2)
    is_used = models.BooleanField(default=False)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"OTP for {self.student.username} from {self.parent.username}"

    def is_expired(self):
        return timezone.now() > self.expires_at

    def mark_as_used(self):
        self.is_used = True
        self.save()

    def mark_as_expired(self):
        # We don't have a status field here like in StudentWalletOTPRequest, 
        # but we can mark it as used to effectively invalidate it.
        self.is_used = True
        self.save()


class StudentWalletOTPRequest(models.Model):
    """
    OTP requests for student wallet operations (deposit, withdraw, transfer).
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='student_wallet_otp_requests')
    operation_type = models.CharField(max_length=50, help_text="Type of operation requiring OTP")
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    description = models.TextField(blank=True, default="")
    otp_code = models.CharField(max_length=6)
    is_used = models.BooleanField(default=False)
    expires_at = models.DateTimeField()
    cache_key = models.CharField(max_length=255, null=True, blank=True, help_text="Cache key for OTP validation")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Wallet OTP for {self.user.username} - {self.operation_type}"

    def is_expired(self):
        return timezone.now() > self.expires_at

    def mark_as_used(self):
        self.is_used = True
        self.save()


# New models for Student Module with Parent Allowance System

class ParentStudentRequest(models.Model):
    """
    Request from student to connect to a parent.
    """
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        APPROVED = 'APPROVED', 'Approved'
        REJECTED = 'REJECTED', 'Rejected'

    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='parent_requests')
    parent = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='student_requests')
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    message = models.CharField(max_length=255, blank=True, default="")

    def __str__(self):
        return f"Request from {self.student.username} to {self.parent.username}: {self.status}"


class MonthlyAllowance(models.Model):
    """
    Stores monthly allowance configuration for students.
    Parent sets the monthly amount, system auto-calculates daily allowance.
    """
    parent = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='monthly_allowances')
    student = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='monthly_allowance')
    monthly_amount = models.DecimalField(max_digits=10, decimal_places=2)
    daily_limit_override = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Manual override for daily spending limit")
    days_in_month = models.IntegerField(default=30)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Monthly allowance for {self.student.username}: {self.monthly_amount}"

    def get_daily_allowance(self):
        if self.daily_limit_override and self.daily_limit_override > 0:
            return self.daily_limit_override
        from decimal import Decimal
        return Decimal(str(self.monthly_amount)) / Decimal(str(self.days_in_month))


class DailySpending(models.Model):
    """
    Tracks daily spending for students.
    """
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='daily_spendings')
    date = models.DateField(default=timezone.now)
    daily_limit = models.DecimalField(max_digits=10, decimal_places=2)
    amount_spent = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    remaining_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_locked = models.BooleanField(default=False)
    locked_by_parent = models.BooleanField(default=False)
    lock_reason = models.CharField(max_length=255, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Daily spending for {self.student.username} on {self.date}"


class SpendingLock(models.Model):
    """
    Tracks spending locks when student exceeds limits.
    """
    class LockType(models.TextChoices):
        DAILY_LIMIT = 'DAILY_LIMIT', 'Daily Limit Exceeded'
        MONTHLY_LIMIT = 'MONTHLY_LIMIT', 'Monthly Limit Exceeded'
        PARENT_LOCKED = 'PARENT_LOCKED', 'Locked by Parent'

    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='spending_locks')
    lock_type = models.CharField(max_length=20, choices=LockType.choices)
    amount_locked = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)
    unlock_otp = models.CharField(max_length=6, null=True, blank=True)
    unlock_expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    unlocked_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Spending lock for {self.student.username}: {self.lock_type}"


class StudentNotification(models.Model):
    """
    Notifications for students about spending, locks, and alerts.
    """
    class NotificationType(models.TextChoices):
        DAILY_80_PERCENT = 'DAILY_80%', 'Daily 80% Used'
        MONTHLY_80_PERCENT = 'MONTHLY_80%', 'Monthly 80% Used'
        WALLET_LOCKED = 'WALLET_LOCKED', 'Wallet Locked'
        WALLET_UNLOCKED = 'WALLET_UNLOCKED', 'Wallet Unlocked'
        PARENT_APPROVAL = 'PARENT_APPROVAL', 'Parent Approval'
        NEW_ALLOWANCE = 'NEW_ALLOWANCE', 'New Allowance Set'

    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=NotificationType.choices)
    title = models.CharField(max_length=100)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    is_sent = models.BooleanField(default=False)
    data = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Notification for {self.student.username}: {self.notification_type}"


class MonthlySpendingSummary(models.Model):
    """
    Tracks monthly spending summary for students.
    """
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='monthly_summaries')
    month = models.IntegerField()
    year = models.IntegerField()
    total_allowance = models.DecimalField(max_digits=10, decimal_places=2)
    total_spent = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    remaining_amount = models.DecimalField(max_digits=10, decimal_places=2)
    days_elapsed = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['student', 'month', 'year']

    def __str__(self):
        return f"Monthly summary for {self.student.username}: {self.month}/{self.year}"


# Translation options are now in translation.py



