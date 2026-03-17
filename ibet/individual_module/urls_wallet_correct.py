"""
URL configuration for Individual Module wallet functionality.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views_wallet import (
    IndividualWalletViewSet, IndividualWalletTransactionViewSet,
    GenerateIndividualWalletOTPView, VerifyIndividualWalletOTPView
)

app_name = 'individual_wallet'

router = DefaultRouter()
router.register(r'wallet', IndividualWalletViewSet, basename='individual-wallet')
router.register(r'wallet/transactions', IndividualWalletTransactionViewSet, basename='individual-wallet-transactions')

urlpatterns = [
    path('', include(router.urls)),
    path('generate-otp/', GenerateIndividualWalletOTPView.as_view(), name='generate-individual-wallet-otp'),
    path('verify-otp/', VerifyIndividualWalletOTPView.as_view(), name='verify-individual-wallet-otp'),

    # Additional wallet endpoints that need explicit routing
    path('balance/', IndividualWalletViewSet.as_view({'get': 'balance'}), name='individual-wallet-balance'),
    path('deposit/', IndividualWalletViewSet.as_view({'post': 'deposit'}), name='individual-wallet-deposit'),
    path('withdraw/', IndividualWalletViewSet.as_view({'post': 'withdraw'}), name='individual-wallet-withdraw'),
    path('transfer-to-goal/', IndividualWalletViewSet.as_view({'post': 'transfer_to_goal'}), name='individual-wallet-transfer-goal'),
]
