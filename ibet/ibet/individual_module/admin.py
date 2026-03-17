from django.contrib import admin
from .models import (
    IncomeSource, EmergencyFund, IndividualDashboard,
    ExpenseAlert, FinancialGoal
)


@admin.register(IncomeSource)
class IncomeSourceAdmin(admin.ModelAdmin):
    list_display = ['user', 'name', 'income_type', 'amount', 'frequency', 'is_active']
    list_filter = ['income_type', 'frequency', 'is_active']
    search_fields = ['user__username', 'name']
    ordering = ['-created_at']


@admin.register(EmergencyFund)
class EmergencyFundAdmin(admin.ModelAdmin):
    list_display = ['user', 'target_amount', 'current_amount', 'progress_percentage', 'monthly_contribution']
    list_filter = ['target_months']
    search_fields = ['user__username']
    readonly_fields = ['progress_percentage', 'months_covered']


@admin.register(IndividualDashboard)
class IndividualDashboardAdmin(admin.ModelAdmin):
    list_display = ['user', 'total_income', 'total_expenses', 'monthly_budget', 'remaining_budget']
    search_fields = ['user__username']
    readonly_fields = ['remaining_budget', 'savings_progress']


@admin.register(ExpenseAlert)
class ExpenseAlertAdmin(admin.ModelAdmin):
    list_display = ['user', 'alert_type', 'title', 'is_active', 'is_read', 'created_at']
    list_filter = ['alert_type', 'is_active', 'is_read']
    search_fields = ['user__username', 'title']
    readonly_fields = ['read_at']


@admin.register(FinancialGoal)
class FinancialGoalAdmin(admin.ModelAdmin):
    list_display = ['user', 'name', 'goal_type', 'target_amount', 'current_amount', 'progress_percentage', 'status']
    list_filter = ['goal_type', 'status']
    search_fields = ['user__username', 'name']
    readonly_fields = ['progress_percentage', 'days_remaining']
