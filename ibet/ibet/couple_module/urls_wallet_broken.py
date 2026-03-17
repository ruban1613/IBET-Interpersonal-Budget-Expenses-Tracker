"""
URL patterns for Couple Module wallet functionality.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views_wallet import (
    CoupleWalletViewSet,
    CoupleWalletTransactionViewSet,
    GenerateCoupleWalletOTPView,
    VerifyCoupleWalletOTPView
)

# Create router for couple wallet endpoints
router = DefaultRouter()
router.register(r'wallet', CoupleWalletViewSet, basename='couple-wallet')
router.register(r'wallet/transactions', CoupleWalletTransactionViewSet, basename='couple-wallet-transactions')

urlpatterns = [
    # Include router URLs
    path('', include(router.urls)),

    # OTP endpoints
    path('wallet/generate-otp/', GenerateCoupleWalletOTPView.as_view(), name='generate-couple-wallet-otp'),
    path('wallet/verify-otp/', VerifyCoupleWalletOTPView.as_view(), name='verify-couple-wallet-otp'),
]
