"""
URL configuration for Couple Module - Wallet Testing Configuration
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views_wallet import CoupleWalletViewSet, CoupleWalletTransactionViewSet, GenerateCoupleWalletOTPView, VerifyCoupleWalletOTPView

router = DefaultRouter()
router.register(r'wallet', CoupleWalletViewSet, basename='couple-wallet')
router.register(r'transactions', CoupleWalletTransactionViewSet, basename='couple-wallet-transactions')

urlpatterns = [
    path('', include(router.urls)),
    path('generate-otp/', GenerateCoupleWalletOTPView.as_view(), name='generate-couple-wallet-otp'),
    path('verify-otp/', VerifyCoupleWalletOTPView.as_view(), name='verify-couple-wallet-otp'),
]
