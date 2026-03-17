"""
Main URL patterns for Couple Module.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CoupleLinkViewSet, SharedWalletViewSet, SpendingRequestViewSet,
    SharedTransactionViewSet, CoupleDashboardViewSet, CoupleAlertViewSet,
    CoupleOverviewView, CreateCoupleView
)

# Create router for couple endpoints
router = DefaultRouter()
router.register(r'couples', CoupleLinkViewSet, basename='couple')
router.register(r'wallets', SharedWalletViewSet, basename='shared-wallet')
router.register(r'spending-requests', SpendingRequestViewSet, basename='spending-request')
router.register(r'transactions', SharedTransactionViewSet, basename='shared-transaction')
router.register(r'dashboards', CoupleDashboardViewSet, basename='couple-dashboard')
router.register(r'alerts', CoupleAlertViewSet, basename='couple-alert')

# The API URLs are now determined automatically by the router.
urlpatterns = [
    path('', include(router.urls)),
    path('overview/', CoupleOverviewView.as_view(), name='couple-overview'),
    path('create-couple/', CreateCoupleView.as_view(), name='create-couple'),

    # Include wallet-specific URLs
    path('wallet/', include('couple_module.urls_wallet_final')),
]
