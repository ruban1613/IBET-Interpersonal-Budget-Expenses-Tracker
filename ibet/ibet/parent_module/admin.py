from django.contrib import admin
from .models import ParentOTPRequest, StudentMonitoring


@admin.register(ParentOTPRequest)
class ParentOTPRequestAdmin(admin.ModelAdmin):
    list_display = ['parent', 'student', 'amount_requested', 'otp_code', 'status', 'created_at', 'expires_at']
    list_filter = ['status', 'created_at']
    search_fields = ['parent__username', 'student__username', 'otp_code']
    readonly_fields = ['otp_code', 'created_at', 'expires_at']


@admin.register(StudentMonitoring)
class StudentMonitoringAdmin(admin.ModelAdmin):
    list_display = ['parent', 'student', 'accessed_at', 'wallet_accessed', 'otp_generated']
    list_filter = ['accessed_at', 'wallet_accessed', 'otp_generated']
    search_fields = ['parent__username', 'student__username']
    readonly_fields = ['accessed_at']
