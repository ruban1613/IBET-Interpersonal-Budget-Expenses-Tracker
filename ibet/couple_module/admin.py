from django.contrib import admin
from .models import (
    CoupleLink, SharedWallet, SpendingRequest, SharedTransaction,
    CoupleDashboard, CoupleAlert
)


@admin.register(CoupleLink)
class CoupleLinkAdmin(admin.ModelAdmin):
    list_display = ['user1', 'user2', 'linked_date', 'is_active']
    list_filter = ['is_active', 'linked_date']
    search_fields = ['user1__username', 'user2__username']
    readonly_fields = ['linked_date']


@admin.register(SharedWallet)
class SharedWalletAdmin(admin.ModelAdmin):
    list_display = ['couple', 'balance', 'monthly_budget', 'updated_at']
    list_filter = ['monthly_budget']
    search_fields = ['couple__user1__username', 'couple__user2__username']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(SpendingRequest)
class SpendingRequestAdmin(admin.ModelAdmin):
    list_display = ['requester', 'amount', 'description', 'status', 'requested_at']
    list_filter = ['status', 'category', 'requested_at']
    search_fields = ['requester__username', 'description']
    readonly_fields = ['requested_at', 'responded_at', 'expires_at']


@admin.register(SharedTransaction)
class SharedTransactionAdmin(admin.ModelAdmin):
    list_display = ['wallet', 'amount', 'transaction_type', 'performed_by', 'transaction_date']
    list_filter = ['transaction_type', 'transaction_date']
    search_fields = ['performed_by__username', 'description']
    readonly_fields = ['transaction_date']


@admin.register(CoupleDashboard)
class CoupleDashboardAdmin(admin.ModelAdmin):
    list_display = ['couple', 'total_contributions', 'total_expenses', 'pending_requests', 'last_updated']
    search_fields = ['couple__user1__username', 'couple__user2__username']
    readonly_fields = ['last_updated']


@admin.register(CoupleAlert)
class CoupleAlertAdmin(admin.ModelAdmin):
    list_display = ['couple', 'alert_type', 'title', 'is_read_user1', 'is_read_user2', 'created_at']
    list_filter = ['alert_type', 'is_read_user1', 'is_read_user2']
    search_fields = ['couple__user1__username', 'couple__user2__username', 'title']
    readonly_fields = ['created_at']
