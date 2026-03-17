"""
Complete URL patterns for Couple Module wallet functionality.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views_wallet_final import (
    CoupleWalletViewSet,
    CoupleWalletTransactionViewSet,
    GenerateCoupleWalletOTPView,
    VerifyCoupleWalletOTPView
)

app_name = 'couple_wallet'

# Create router for couple wallet endpoints
router = DefaultRouter()
router.register(r'wallet', CoupleWalletViewSet, basename='couple-wallet')
router.register(r'wallet/transactions', CoupleWalletTransactionViewSet, basename='couple-wallet-transactions')

urlpatterns = [
    # Include router URLs
    path('', include(router.urls)),

    # OTP endpoints
    path('generate-otp/', GenerateCoupleWalletOTPView.as_view(), name='generate-couple-wallet-otp'),
    path('verify-otp/', VerifyCoupleWalletOTPView.as_view(), name='verify-couple-wallet-otp'),

    # Additional wallet endpoints that need explicit routing
    path('balance/', CoupleWalletViewSet.as_view({'get': 'balance'}), name='couple-wallet-balance'),
    path('deposit/', CoupleWalletViewSet.as_view({'post': 'deposit'}), name='couple-wallet-deposit'),
    path('withdraw/', CoupleWalletViewSet.as_view({'post': 'withdraw'}), name='couple-wallet-withdraw'),
    path('transfer-to-emergency/', CoupleWalletViewSet.as_view({'post': 'transfer_to_emergency'}), name='couple-wallet-transfer-emergency'),
    path('transfer-to-goals/', CoupleWalletViewSet.as_view({'post': 'transfer_to_goals'}), name='couple-wallet-transfer-goals'),
    path('monthly-summary/', CoupleWalletViewSet.as_view({'get': 'monthly_summary'}), name='couple-wallet-monthly-summary'),
]
