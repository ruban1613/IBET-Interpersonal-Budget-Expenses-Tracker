from django.contrib import admin
from .models import Institute, TeacherProfile, InstituteStudentProfile, FeePayment, SalaryPayment, InstituteNotification, TeacherAttendance, StudentAttendance

@admin.register(Institute)
class InstituteAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'created_at')
    search_fields = ('name', 'owner__username')

@admin.register(TeacherProfile)
class TeacherProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'institute', 'base_monthly_salary', 'working_days_per_month', 'is_active')
    list_filter = ('institute', 'is_active')

@admin.register(InstituteStudentProfile)
class InstituteStudentProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'institute', 'monthly_fee', 'due_day', 'is_active')
    list_filter = ('institute', 'is_active')

@admin.register(FeePayment)
class FeePaymentAdmin(admin.ModelAdmin):
    list_display = ('student_profile', 'total_amount', 'paid_amount', 'month', 'year', 'status', 'payment_date')
    list_filter = ('status', 'month', 'year')

@admin.register(SalaryPayment)
class SalaryPaymentAdmin(admin.ModelAdmin):
    list_display = ('teacher_profile', 'amount', 'month', 'year', 'status', 'payment_date')
    list_filter = ('status', 'month', 'year')

@admin.register(InstituteNotification)
class InstituteNotificationAdmin(admin.ModelAdmin):
    list_display = ('notification_type', 'recipient', 'sent_at', 'is_delivered')
    list_filter = ('notification_type', 'is_delivered')

@admin.register(TeacherAttendance)
class TeacherAttendanceAdmin(admin.ModelAdmin):
    list_display = ('teacher', 'date', 'status', 'extra_sessions')
    list_filter = ('status', 'date', 'teacher__institute')

@admin.register(StudentAttendance)
class StudentAttendanceAdmin(admin.ModelAdmin):
    list_display = ('student_profile', 'date', 'status', 'marked_by')
    list_filter = ('status', 'date', 'student_profile__institute')
