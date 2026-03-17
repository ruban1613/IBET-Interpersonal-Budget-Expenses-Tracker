from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    IncomeSourceViewSet, EmergencyFundViewSet, IndividualDashboardViewSet,
    ExpenseAlertViewSet, FinancialGoalViewSet, InvestmentSuggestionViewSet,
    IndividualOverviewView, ExpenseTrackingView
)
from .views_enhanced import (
    get_individual_dashboard,
    deposit_to_main_wallet,
    withdraw_from_main_wallet,
    transfer_to_savings,
    record_expense,
    get_spending_alerts,
    mark_alert_read,
    get_expense_categories,
    get_spending_stats,
    generate_deposit_otp,
    generate_savings_otp,
    set_monthly_budget,
    set_savings_goal
)

router = DefaultRouter()
router.register(r'income-sources', IncomeSourceViewSet, basename='income-source')
router.register(r'emergency-fund', EmergencyFundViewSet, basename='emergency-fund')
router.register(r'dashboard', IndividualDashboardViewSet, basename='individual-dashboard')
router.register(r'expense-alerts', ExpenseAlertViewSet, basename='expense-alert')
router.register(r'financial-goals', FinancialGoalViewSet, basename='financial-goal')
router.register(r'investment-suggestions', InvestmentSuggestionViewSet, basename='investment-suggestion')

# The API URLs are now determined automatically by the router.
urlpatterns = [
    path('', include(router.urls)),
    path('overview/', IndividualOverviewView.as_view(), name='individual-overview'),
    path('expenses/', ExpenseTrackingView.as_view(), name='expense-tracking'),
]

# Enhanced Individual Module URLs
urlpatterns += [
    # Dashboard
    path('enhanced/dashboard/', get_individual_dashboard, name='individual-enhanced-dashboard'),
    
    # Main Wallet Operations - with 'enhanced' prefix
    path('enhanced/deposit/', deposit_to_main_wallet, name='individual-deposit'),
    path('enhanced/withdraw/', withdraw_from_main_wallet, name='individual-withdraw'),
    path('enhanced/generate-deposit-otp/', generate_deposit_otp, name='generate-deposit-otp'),
    
    # Savings Wallet Operations - with 'enhanced' prefix
    path('enhanced/transfer-to-savings/', transfer_to_savings, name='transfer-to-savings'),
    path('enhanced/generate-savings-otp/', generate_savings_otp, name='generate-savings-otp'),
    
    # Expense Tracking - with 'enhanced' prefix
    path('enhanced/record-expense/', record_expense, name='record-expense'),
    path('enhanced/expense-categories/', get_expense_categories, name='expense-categories'),
    path('enhanced/spending-stats/', get_spending_stats, name='spending-stats'),
    
    # Alerts - with 'enhanced' prefix
    path('enhanced/spending-alerts/', get_spending_alerts, name='spending-alerts'),
    path('enhanced/alerts/<int:alert_id>/mark_read/', mark_alert_read, name='mark-alert-read'),
    
    # Budget and Goals
    path('enhanced/set-budget/', set_monthly_budget, name='set-monthly-budget'),
    path('enhanced/set-savings-goal/', set_savings_goal, name='set-savings-goal'),
]

# Include wallet-specific URLs
urlpatterns += [
    path('', include('individual_module.urls_wallet')),
]
