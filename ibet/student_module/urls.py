from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token
from .views import (
    BudgetViewSet, CategoryViewSet, TransactionViewSet, SelectPersonaView,
    ReminderViewSet, ChatMessageViewSet, DailyLimitViewSet, VerifyOTPView, OTPRequestViewSet,
    ParentStudentRequestViewSet, MonthlyAllowanceViewSet, DailySpendingViewSet,
    SpendingLockViewSet, StudentNotificationViewSet, MonthlySpendingSummaryViewSet,
    StudentDashboardView, UserViewSet
)

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'budgets', BudgetViewSet, basename='budget')
router.register(r'transactions', TransactionViewSet, basename='transaction')
router.register(r'reminders', ReminderViewSet, basename='reminder')
router.register(r'chat-messages', ChatMessageViewSet, basename='chat-message')
router.register(r'daily-limits', DailyLimitViewSet, basename='daily-limit')
router.register(r'otp-requests', OTPRequestViewSet, basename='otp-request')
router.register(r'parent-requests', ParentStudentRequestViewSet, basename='parent-request')
router.register(r'monthly-allowances', MonthlyAllowanceViewSet, basename='monthly-allowance')
router.register(r'daily-spending', DailySpendingViewSet, basename='daily-spending')
router.register(r'spending-locks', SpendingLockViewSet, basename='spending-lock')
router.register(r'notifications', StudentNotificationViewSet, basename='notification')
router.register(r'monthly-summaries', MonthlySpendingSummaryViewSet, basename='monthly-summary')

# The API URLs are now determined automatically by the router.
urlpatterns = [
    path('', include(router.urls)),
    path('users/select-persona/', SelectPersonaView.as_view(), name='select-persona'),
    # Add the token authentication endpoint here, it will be available at /api/token-auth/
    path('token-auth/', obtain_auth_token, name='api_token_auth'),
    path('verify-otp/', VerifyOTPView.as_view(), name='verify-otp'),
    # Include wallet URLs
    path('wallet/', include('student_module.urls_wallet')),
    # Student dashboard
    path('dashboard/', StudentDashboardView.as_view(), name='student-dashboard'),
]
