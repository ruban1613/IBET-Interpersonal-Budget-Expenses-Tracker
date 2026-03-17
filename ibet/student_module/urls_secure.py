"""
Secure URL configuration for student module.
Uses enhanced security views with OTP protection and monitoring.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token
from .views import (
    BudgetViewSet, CategoryViewSet, TransactionViewSet, SelectPersonaView,
    ReminderViewSet, ChatMessageViewSet, DailyLimitViewSet, OTPRequestViewSet
)
from .views_secure import SecureVerifyOTPView

# Create router for standard viewsets
router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'budgets', BudgetViewSet, basename='budget')
router.register(r'transactions', TransactionViewSet, basename='transaction')
router.register(r'reminders', ReminderViewSet, basename='reminder')
router.register(r'chat-messages', ChatMessageViewSet, basename='chat-message')
router.register(r'daily-limits', DailyLimitViewSet, basename='daily-limit')
router.register(r'otp-requests', OTPRequestViewSet, basename='otp-request')

# Secure URL patterns with enhanced security
urlpatterns = [
    path('', include(router.urls)),
    path('users/select-persona/', SelectPersonaView.as_view(), name='select-persona'),
    # Add the token authentication endpoint here, it will be available at /api/token-auth/
    path('token-auth/', obtain_auth_token, name='api_token_auth'),

    # Secure OTP verification endpoint (ENHANCED SECURITY)
    path('verify-otp/', SecureVerifyOTPView.as_view(), name='verify-otp'),
]
