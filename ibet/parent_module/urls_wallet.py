"""
URL configuration for Parent Module wallet functionality.
"""
from django.urls import path
from .views_wallet import (
    ParentWalletViewSet, GenerateParentWalletOTPView, VerifyParentWalletOTPView, StudentWalletApprovalView
)

app_name = 'parent_wallet'

# Define all URLs explicitly to avoid routing conflicts
# NOTE: The order matters - more specific paths should come first
urlpatterns = [
    # OTP endpoints - these must come BEFORE generic paths
    path('generate-otp/', GenerateParentWalletOTPView.as_view(), name='generate-parent-wallet-otp'),
    path('verify-otp/', VerifyParentWalletOTPView.as_view(), name='verify-parent-wallet-otp'),
    
    # Student approval endpoint
    path('approve-student/', StudentWalletApprovalView.as_view(), name='approve-student-wallet'),
    
    # Wallet ViewSet actions - mapped to explicit paths
    path('statement/', ParentWalletViewSet.as_view({'get': 'statement'}), name='parent-statement'),
    path('student_statement/', ParentWalletViewSet.as_view({'get': 'student_statement'}), name='student-statement'),
    path('record_expense/', ParentWalletViewSet.as_view({'post': 'record_expense'}), name='parent-record-expense'),
    path('linked-students-wallets/', ParentWalletViewSet.as_view({'get': 'linked_students_wallets'}), name='linked-students-wallets'),
    path('balance/', ParentWalletViewSet.as_view({'get': 'balance'}), name='parent-wallet-balance'),
    path('welcome/', ParentWalletViewSet.as_view({'get': 'welcome'}), name='parent-wallet-welcome'),
    path('deposit/', ParentWalletViewSet.as_view({'post': 'deposit'}), name='parent-wallet-deposit'),
    path('withdraw/', ParentWalletViewSet.as_view({'post': 'withdraw'}), name='parent-wallet-withdraw'),
    path('', ParentWalletViewSet.as_view({'get': 'list', 'post': 'create'}), name='parent-wallet-list'),
]
