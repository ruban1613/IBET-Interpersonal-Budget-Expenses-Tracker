"""
New model for tracking daily allowances in the new system.
This implements the cumulative daily allowance system where:
- Monthly allowance is divided equally across days
- Students can spend from available days
- Future days get locked if overspent
- At midnight, new day's allowance becomes available
"""
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class DailyAllowance(models.Model):
    """
    Tracks individual daily allowance for each day of the month.
    This replaces the simple daily_limit in DailySpending.
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
    student = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='cumulative_spending'
    )
    month = models.IntegerField()
    year = models.IntegerField()
    total_allocated = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_spent = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_available = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    days_available = models.IntegerField(default=0)  # Number of days with available funds
    current_day_date = models.DateField(null=True, blank=True)  # Today's date reference
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
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False
