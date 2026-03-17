from django.db import models
from django.conf import settings
from django.db.models import Sum
from modeltranslation.translator import translator, TranslationOptions
from django.utils.translation import gettext_lazy as _

# Parent-specific models
class ParentDashboard(models.Model):
    parent = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='parent_dashboard')
    total_students = models.PositiveIntegerField(default=0)
    total_alerts_sent = models.PositiveIntegerField(default=0)
    last_accessed = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.parent.username}'s Parent Dashboard"

    def get_total_student_spending(self):
        """Calculate total spending across all linked students"""
        # Import here to avoid circular dependency
        from student_module.models import ParentStudentLink, Transaction
        linked_students = ParentStudentLink.objects.filter(parent=self.parent).values_list('student', flat=True)
        return Transaction.objects.filter(
            user__in=linked_students,
            transaction_type='EXP'
        ).aggregate(total=Sum('amount'))['total'] or 0.00


class AlertSettings(models.Model):
    class AlertType(models.TextChoices):
        BUDGET_50 = '50%', _('50% Budget Used')
        BUDGET_70 = '70%', _('70% Budget Used')
        BUDGET_100 = '100%', _('100% Budget Used')
        DAILY_LIMIT_EXCEEDED = 'DAILY_LIMIT', _('Daily Limit Exceeded')
        WEEKLY_SPENDING_HIGH = 'WEEKLY_HIGH', _('Weekly Spending High')

    parent = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='alert_settings')
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='parent_alerts')
    alert_type = models.CharField(max_length=20, choices=AlertType.choices)
    is_enabled = models.BooleanField(default=True)
    email_notification = models.BooleanField(default=True)
    sms_notification = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.parent.username} - {self.alert_type} for {self.student.username}"

    class Meta:
        unique_together = ['parent', 'student', 'alert_type']


class StudentMonitoring(models.Model):
    parent = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='monitoring_sessions')
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='monitored_by')
    accessed_at = models.DateTimeField(auto_now_add=True)
    wallet_accessed = models.BooleanField(default=False)
    otp_generated = models.BooleanField(default=False)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.parent.username} monitored {self.student.username} at {self.accessed_at}"


class ParentAlert(models.Model):
    class AlertStatus(models.TextChoices):
        SENT = 'SENT', _('Sent')
        READ = 'READ', _('Read')
        ACTION_TAKEN = 'ACTION_TAKEN', _('Action Taken')

    parent = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='received_alerts')
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='generated_alerts')
    alert_type = models.CharField(max_length=20)
    message = models.TextField()
    status = models.CharField(max_length=15, choices=AlertStatus.choices, default=AlertStatus.SENT)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Alert for {self.parent.username}: {self.alert_type}"


class ParentOTPRequest(models.Model):
    class OTPStatus(models.TextChoices):
        PENDING = 'PENDING', _('Pending')
        USED = 'USED', _('Used')
        EXPIRED = 'EXPIRED', _('Expired')

    parent = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='otp_requests')
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='received_otps', null=True, blank=True)
    otp_code = models.CharField(max_length=6)
    amount_requested = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    reason = models.CharField(max_length=255, null=True, blank=True)
    status = models.CharField(max_length=10, choices=OTPStatus.choices, default=OTPStatus.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)
    operation_type = models.CharField(max_length=50, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    cache_key = models.CharField(max_length=255, null=True, blank=True)
    is_used = models.BooleanField(default=False)

    def __str__(self):
        student_name = self.student.username if self.student else "General"
        return f"OTP {self.otp_code} for {self.parent.username} -> {student_name}"

    def is_expired(self):
        from django.utils import timezone
        return timezone.now() > self.expires_at

    def mark_as_used(self):
        from django.utils import timezone
        self.status = self.OTPStatus.USED
        self.used_at = timezone.now()
        self.save()

    def mark_as_expired(self):
        self.status = self.OTPStatus.EXPIRED
        self.save()


# Translation options are now in translation.py
