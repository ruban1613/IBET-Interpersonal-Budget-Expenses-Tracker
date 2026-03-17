"""
URL configuration for Student Module wallet functionality.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views_wallet_new import (
    StudentWalletViewSet, GenerateStudentWalletOTPView, VerifyStudentWalletOTPView
)

app_name = 'student_wallet'

router = DefaultRouter()
router.register(r'', StudentWalletViewSet, basename='student-wallet')

# IMPORTANT: Explicit paths must come BEFORE router.urls to avoid being captured as detail routes
urlpatterns = [
    path('generate-otp/', GenerateStudentWalletOTPView.as_view(), name='generate-student-wallet-otp'),
    path('verify-otp/', VerifyStudentWalletOTPView.as_view(), name='verify-student-wallet-otp'),
    path('verify-parent-otp/', StudentWalletViewSet.as_view({'post': 'verify_parent_otp'}), name='verify-parent-otp'),
    path('request-parent-approval/', StudentWalletViewSet.as_view({'post': 'request_parent_approval'}), name='request-parent-approval'),
    path('daily-status/', StudentWalletViewSet.as_view({'get': 'daily_status'}), name='daily-status'),
    path('', include(router.urls)),
]
