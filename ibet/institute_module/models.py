from django.db import models, transaction
from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from decimal import Decimal
from modeltranslation.translator import TranslationOptions

class Institute(models.Model):
    """
    Main model for an educational institute.
    Owned by a User with INSTITUTE_OWNER persona.
    """
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='owned_institutes')
    name = models.CharField(max_length=255)
    address = models.TextField(blank=True)
    contact_number = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class TeacherProfile(models.Model):
    """
    Profile for teachers within an institute.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='teacher_profiles')
    institute = models.ForeignKey(Institute, on_delete=models.CASCADE, related_name='teachers')
    base_monthly_salary = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    working_days_per_month = models.PositiveIntegerField(default=26)
    extra_session_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_active = models.BooleanField(default=True)
    joining_date = models.DateField(default=timezone.localdate)
    assigned_students = models.ManyToManyField('InstituteStudentProfile', blank=True, related_name='assigned_teachers')

    def __str__(self):
        return f"{self.user.username} - {self.institute.name} (Teacher)"

    @property
    def daily_rate(self):
        if self.working_days_per_month > 0:
            return self.base_monthly_salary / Decimal(str(self.working_days_per_month))
        return Decimal('0.00')

class TeacherAttendance(models.Model):
    """
    Daily attendance and extra session tracking for teachers.
    """
    class Status(models.TextChoices):
        PRESENT = 'PRESENT', _('Present')
        ABSENT = 'ABSENT', _('Absent')
        HALF_DAY = 'HALF_DAY', _('Half Day')
        OVERTIME = 'OVERTIME', _('Overtime / Weekend')

    teacher = models.ForeignKey(TeacherProfile, on_delete=models.CASCADE, related_name='attendance_records')
    date = models.DateField(default=timezone.localdate)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PRESENT)
    extra_sessions = models.PositiveIntegerField(default=0, help_text="Number of extra classes/hours taken")
    remarks = models.CharField(max_length=255, blank=True)

    class Meta:
        unique_together = ['teacher', 'date']

    def __str__(self):
        return f"{self.teacher.user.username} - {self.date} - {self.status}"

class InstituteStudentProfile(models.Model):
    """
    Profile for students within an institute.
    Note: Link to User model (persona=STUDENT).
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='institute_student_profiles')
    institute = models.ForeignKey(Institute, on_delete=models.CASCADE, related_name='students')
    student_name = models.CharField(max_length=255, default="", help_text="Full name of the student")
    parent_mobile = models.CharField(max_length=20)
    monthly_fee = models.DecimalField(max_digits=10, decimal_places=2)
    due_day = models.PositiveIntegerField(default=5, help_text="Day of the month fee is due")
    is_active = models.BooleanField(default=True)
    enrolled_date = models.DateField(default=timezone.localdate)

    class Meta:
        # Unique student name per parent mobile within the same institute
        unique_together = ['institute', 'student_name', 'parent_mobile']

    def __str__(self):
        return f"{self.student_name} ({self.institute.name})"

class FeePayment(models.Model):
    """
    Tracks fee payments from students.
    """
    class Status(models.TextChoices):
        PAID = 'PAID', _('Paid')
        PARTIAL = 'PARTIAL', _('Partial')
        PENDING = 'PENDING', _('Pending')
        OVERDUE = 'OVERDUE', _('Overdue')

    student_profile = models.ForeignKey(InstituteStudentProfile, on_delete=models.CASCADE, related_name='fee_payments')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, help_text="Total fee for the month")
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    month = models.PositiveIntegerField() # 1-12
    year = models.PositiveIntegerField()
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    payment_date = models.DateTimeField(null=True, blank=True)
    transaction_id = models.CharField(max_length=100, blank=True)
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def pending_amount(self):
        return self.total_amount - self.paid_amount

    class Meta:
        unique_together = ['student_profile', 'month', 'year']

    def __str__(self):
        return f"Fee: {self.student_profile.student_name} - {self.month}/{self.year} (Paid: {self.paid_amount}/{self.total_amount})"

class SalaryPayment(models.Model):
    """
    Tracks salary payments to teachers.
    """
    class Status(models.TextChoices):
        PAID = 'PAID', _('Paid')
        PENDING = 'PENDING', _('Pending')

    teacher_profile = models.ForeignKey(TeacherProfile, on_delete=models.CASCADE, related_name='salary_payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    month = models.PositiveIntegerField()
    year = models.PositiveIntegerField()
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    payment_date = models.DateTimeField(null=True, blank=True)
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['teacher_profile', 'month', 'year']

    def __str__(self):
        return f"Salary: {self.teacher_profile.user.username} - {self.month}/{self.year} ({self.status})"

class InstituteNotification(models.Model):
    """
    Log of automated reminders and notifications.
    """
    class Type(models.TextChoices):
        FEE_REMINDER = 'FEE_REMINDER', _('Fee Reminder')
        SALARY_CREDIT = 'SALARY_CREDIT', _('Salary Credit')
        DUE_ALERT = 'DUE_ALERT', _('Due Alert')

    institute = models.ForeignKey(Institute, on_delete=models.CASCADE)
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    notification_type = models.CharField(max_length=20, choices=Type.choices)
    message = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
    is_delivered = models.BooleanField(default=True) # Mock delivery for now

    def __str__(self):
        return f"{self.notification_type} to {self.recipient.username}"

class StudentAttendance(models.Model):
    """
    Tracks daily attendance for students.
    """
    class Status(models.TextChoices):
        PRESENT = 'PRESENT', _('Present')
        ABSENT = 'ABSENT', _('Absent')
        LATE = 'LATE', _('Late')
        EXCUSED = 'EXCUSED', _('Excused')

    student_profile = models.ForeignKey(InstituteStudentProfile, on_delete=models.CASCADE, related_name='attendance_records')
    date = models.DateField(default=timezone.localdate)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PRESENT)
    remarks = models.TextField(blank=True)
    marked_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['student_profile', 'date']
        ordering = ['-date']

    def __str__(self):
        return f"{self.student_profile.student_name} - {self.date}: {self.status}"

# Translation options
class InstituteTranslationOptions(TranslationOptions):
    fields = ('name', 'address')
