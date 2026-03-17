"""
Serializers for Parent Module wallet functionality.
"""
from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from .models import ParentOTPRequest, StudentMonitoring
from student_module.models import Wallet, WalletTransaction
from decimal import Decimal


class ParentWalletTransactionSerializer(serializers.ModelSerializer):
    """Serializer for wallet transaction history."""
    class Meta:
        model = WalletTransaction
        fields = [
            'id', 'amount', 'transaction_type', 'description', 
            'balance_after', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class ParentWalletSerializer(serializers.ModelSerializer):
    """Serializer for parent wallet model."""

    class Meta:
        model = Wallet
        fields = [
            'id', 'balance', 'last_transaction_at'
        ]
        read_only_fields = ['id', 'last_transaction_at']


class ParentWalletDepositSerializer(serializers.Serializer):
    """Serializer for wallet deposit operations."""
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal('0.01'))
    description = serializers.CharField(max_length=255, required=False, default=_('Deposit'))


class ParentWalletWithdrawalSerializer(serializers.Serializer):
    """Serializer for wallet withdrawal operations."""
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal('0.01'))
    description = serializers.CharField(max_length=255, required=False, default=_('Withdrawal'))


class GenerateParentWalletOTPSerializer(serializers.Serializer):
    """Serializer for generating OTP for wallet operations."""
    operation_type = serializers.ChoiceField(choices=[
        ('deposit', _('Deposit')),
        ('withdrawal', _('Withdrawal')),
        ('student_approval', _('Student Approval')),
    ])
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    description = serializers.CharField(max_length=255, required=False)


class VerifyParentWalletOTPSerializer(serializers.Serializer):
    """Serializer for verifying OTP for wallet operations."""
    otp_code = serializers.CharField(max_length=6, min_length=6)
    otp_request_id = serializers.IntegerField()


class StudentWalletApprovalSerializer(serializers.Serializer):
    """Serializer for student wallet approval requests."""
    student_id = serializers.IntegerField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal('0.01'))
    otp_code = serializers.CharField(max_length=6, min_length=6)


class LinkedStudentWalletSerializer(serializers.Serializer):
    """Serializer for linked student wallet information."""
    student_id = serializers.IntegerField(read_only=True)
    student_username = serializers.CharField(read_only=True)
    wallet_balance = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    is_locked = serializers.BooleanField(read_only=True)
    last_transaction_at = serializers.DateTimeField(read_only=True)
