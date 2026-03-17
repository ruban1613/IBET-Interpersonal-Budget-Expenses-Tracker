"""
Secure URL configuration for parent module.
Uses enhanced security views with OTP protection and monitoring.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ParentDashboardViewSet, AlertSettingsViewSet, StudentMonitoringViewSet,
    ParentAlertViewSet, StudentWalletAccessView, StudentOverviewView, LinkedStudentsView,
    ParentOTPRequestViewSet
)
from .views_secure import SecureGenerateOTPView

# Create router for standard viewsets
router = DefaultRouter()
router.register(r'dashboard', ParentDashboardViewSet, basename='parent-dashboard')
router.register(r'alert-settings', AlertSettingsViewSet, basename='alert-settings')
router.register(r'monitoring', StudentMonitoringViewSet, basename='student-monitoring')
router.register(r'alerts', ParentAlertViewSet, basename='parent-alerts')
router.register(r'otp-requests', ParentOTPRequestViewSet, basename='otp-requests')

# Secure URL patterns with enhanced security
urlpatterns = [
    path('', include(router.urls)),
    path('wallet-access/', StudentWalletAccessView.as_view(), name='student-wallet-access'),
    path('students/', LinkedStudentsView.as_view(), name='linked-students'),
    path('students/<int:student_id>/overview/', StudentOverviewView.as_view(), name='student-overview'),

    # Secure OTP generation endpoint (CRITICAL SECURITY FIX)
    path('generate-otp/', SecureGenerateOTPView.as_view(), name='generate-otp'),
]
