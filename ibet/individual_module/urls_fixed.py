from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    IncomeSourceViewSet, EmergencyFundViewSet, IndividualDashboardViewSet,
    ExpenseAlertViewSet, FinancialGoalViewSet, IndividualOverviewView,
    WalletManagementView, ExpenseTrackingView
)

router = DefaultRouter()
router.register(r'income-sources', IncomeSourceViewSet, basename='income-source')
router.register(r'emergency-fund', EmergencyFundViewSet, basename='emergency-fund')
router.register(r'dashboard', IndividualDashboardViewSet, basename='individual-dashboard')
router.register(r'expense-alerts', ExpenseAlertViewSet, basename='expense-alert')
router.register(r'financial-goals', FinancialGoalViewSet, basename='financial-goal')

# The API URLs are now determined automatically by the router.
urlpatterns = [
    path('', include(router.urls)),
    path('overview/', IndividualOverviewView.as_view(), name='individual-overview'),
    path('wallet/', WalletManagementView.as_view(), name='wallet-management'),
    path('expenses/', ExpenseTrackingView.as_view(), name='expense-tracking'),
]

# Include wallet-specific URLs
urlpatterns += [
    path('wallet/', include('individual_module.urls_wallet_fixed')),
]
