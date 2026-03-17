"""
Serializers for Individual Module wallet functionality.
"""
from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from .models_wallet import IndividualWallet, IndividualWalletTransaction, IndividualWalletOTPRequest
from decimal import Decimal


class IndividualWalletSerializer(serializers.ModelSerializer):
    """Serializer for individual wallet model."""

    class Meta:
        model = IndividualWallet
        fields = [
            'id', 'balance', 'total_deposits', 'monthly_budget', 'savings_goal', 'current_savings',
            'is_locked', 'last_transaction_at', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'last_transaction_at', 'total_deposits']


class IndividualWalletTransactionSerializer(serializers.ModelSerializer):
    """Serializer for individual wallet transactions."""

    class Meta:
        model = IndividualWalletTransaction
        fields = [
            'id', 'amount', 'transaction_type', 'description', 'balance_after', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'balance_after']


class IndividualWalletOTPRequestSerializer(serializers.ModelSerializer):
    """Serializer for individual wallet OTP requests."""

    class Meta:
        model = IndividualWalletOTPRequest
        fields = [
            'id', 'operation_type', 'amount', 'description', 'expires_at', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'expires_at']


class IndividualWalletDepositSerializer(serializers.Serializer):
    """Serializer for wallet deposit operations."""
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal('0.01'))
    description = serializers.CharField(max_length=255, required=False, default=_('Deposit'))


class IndividualWalletWithdrawalSerializer(serializers.Serializer):
    """Serializer for wallet withdrawal operations."""
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal('0.01'))
    description = serializers.CharField(max_length=255, required=False, default=_('Withdrawal'))


class IndividualWalletTransferSerializer(serializers.Serializer):
    """Serializer for wallet transfer to savings operations."""
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal('0.01'))
    goal_name = serializers.CharField(max_length=100, default=_('Savings Goal'))


class IndividualWalletSavingsWithdrawalSerializer(serializers.Serializer):
    """Serializer for wallet withdrawal from savings operations."""
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal('0.01'))
    description = serializers.CharField(max_length=255, required=False, default=_('Savings Withdrawal'))


class IndividualWalletBudgetSerializer(serializers.Serializer):
    """Serializer for setting monthly budget."""
    monthly_budget = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal('0.00'))


class IndividualWalletSavingsGoalSerializer(serializers.Serializer):
    """Serializer for setting savings goal."""
    savings_goal = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal('0.00'))


class GenerateIndividualWalletOTPSerializer(serializers.Serializer):
    """Serializer for generating OTP for wallet operations."""
    operation_type = serializers.ChoiceField(choices=[
        ('deposit', _('Deposit')),
        ('withdrawal', _('Withdrawal')),
        ('transfer', _('Transfer to Savings')),
    ])
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    description = serializers.CharField(max_length=255, required=False)


class VerifyIndividualWalletOTPSerializer(serializers.Serializer):
    """Serializer for verifying OTP for wallet operations."""
    otp_code = serializers.CharField(max_length=6, min_length=6)
    otp_request_id = serializers.IntegerField()
