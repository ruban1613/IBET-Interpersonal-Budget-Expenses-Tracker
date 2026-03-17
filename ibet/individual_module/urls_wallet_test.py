"""
URL configuration for Individual Module wallet functionality.
"""
from django.urls import path
from .views_wallet import (
    IndividualWalletViewSet, IndividualWalletTransactionViewSet,
    GenerateIndividualWalletOTPView, VerifyIndividualWalletOTPView
)

app_name = 'individual_wallet'

urlpatterns = [
    # Wallet endpoints matching test expectations
    path('wallet/wallet/balance/', IndividualWalletViewSet.as_view({'get': 'balance'}), name='individual-wallet-balance'),
    path('wallet/wallet/deposit/', IndividualWalletViewSet.as_view({'post': 'deposit'}), name='individual-wallet-deposit'),
    path('wallet/wallet/withdraw/', IndividualWalletViewSet.as_view({'post': 'withdraw'}), name='individual-wallet-withdraw'),
    path('wallet/wallet/transfer-to-goal/', IndividualWalletViewSet.as_view({'post': 'transfer_to_goal'}), name='individual-wallet-transfer-goal'),

    # Transaction endpoints
    path('wallet/transactions/', IndividualWalletTransactionViewSet.as_view({'get': 'list', 'post': 'create'}), name='individual-wallet-transactions-list'),
    path('wallet/transactions/<int:pk>/', IndividualWalletTransactionViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='individual-wallet-transactions-detail'),

    # OTP endpoints
    path('generate-otp/', GenerateIndividualWalletOTPView.as_view(), name='generate-individual-wallet-otp'),
    path('verify-otp/', VerifyIndividualWalletOTPView.as_view(), name='verify-individual-wallet-otp'),
]
