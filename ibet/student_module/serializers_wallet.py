"""
Serializers for Student Module wallet functionality.
"""
from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from .models import Wallet, WalletTransaction, OTPRequest, ParentStudentLink
from decimal import Decimal


class StudentWalletSerializer(serializers.ModelSerializer):
    """Serializer for student wallet model."""

    class Meta:
        model = Wallet
        fields = [
            'id', 'balance', 'special_balance', 'is_locked', 'last_transaction_at', 
            'locked_at', 'failed_attempts', 'locked_until'
        ]
        read_only_fields = ['id', 'last_transaction_at']


class WalletTransactionSerializer(serializers.ModelSerializer):
    """Serializer for wallet transactions."""
    wallet_type_display = serializers.CharField(source='get_wallet_type_display', read_only=True)
    transaction_type_display = serializers.CharField(source='get_transaction_type_display', read_only=True)

    class Meta:
        model = WalletTransaction
        fields = [
            'id', 'wallet_type', 'wallet_type_display', 'transaction_type', 
            'transaction_type_display', 'amount', 'balance_after', 
            'description', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'balance_after']


class StudentWalletDepositSerializer(serializers.Serializer):
    """Serializer for wallet deposit operations."""
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal('0.01'))
    description = serializers.CharField(max_length=255, required=False, default=_('Deposit'))


class StudentWalletWithdrawalSerializer(serializers.Serializer):
    """Serializer for wallet withdrawal operations."""
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal('0.01'))
    description = serializers.CharField(max_length=255, required=False, default=_('Withdrawal'))


class StudentWalletParentApprovalSerializer(serializers.Serializer):
    """Serializer for parent approval requests."""
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal('0.01'))
    description = serializers.CharField(max_length=255, required=False, default=_('Transaction request'))


class GenerateStudentWalletOTPSerializer(serializers.Serializer):
    """Serializer for generating OTP for wallet operations."""
    operation_type = serializers.ChoiceField(choices=[
        ('deposit', _('Deposit')),
        ('withdrawal', _('Withdrawal')),
        ('parent_approval', _('Parent Approval Request')),
    ])
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    description = serializers.CharField(max_length=255, required=False)


class VerifyStudentWalletOTPSerializer(serializers.Serializer):
    """Serializer for verifying OTP for wallet operations."""
    otp_code = serializers.CharField(max_length=6, min_length=6)
    otp_request_id = serializers.IntegerField()


class StudentOTPRequestSerializer(serializers.ModelSerializer):
    """Serializer for student OTP requests."""

    class Meta:
        model = OTPRequest
        fields = [
            'id', 'student', 'parent', 'amount_requested', 'is_used',
            'expires_at', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'expires_at', 'is_used']
