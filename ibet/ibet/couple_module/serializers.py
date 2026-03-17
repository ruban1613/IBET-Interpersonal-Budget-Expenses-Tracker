from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from .models import (
    CoupleLink, SharedWallet, SpendingRequest, SharedTransaction,
    CoupleDashboard, CoupleAlert
)
from django.contrib.auth import get_user_model

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """
    Basic user serializer for couple relationships
    """
    class Meta:
        model = User
        fields = ['id', 'username', 'email']


class CoupleLinkSerializer(serializers.ModelSerializer):
    """
    Serializer for CoupleLink model
    """
    user1 = UserSerializer(read_only=True)
    user2 = UserSerializer(read_only=True)

    class Meta:
        model = CoupleLink
        fields = ['id', 'user1', 'user2', 'linked_date', 'is_active']
        read_only_fields = ['id', 'linked_date']


class SharedWalletSerializer(serializers.ModelSerializer):
    """
    Serializer for SharedWallet model
    """
    couple = CoupleLinkSerializer(read_only=True)

    class Meta:
        model = SharedWallet
        fields = [
            'id', 'couple', 'balance', 'monthly_budget',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class SpendingRequestSerializer(serializers.ModelSerializer):
    """
    Serializer for SpendingRequest model
    """
    requester = UserSerializer(read_only=True)
    couple = CoupleLinkSerializer(read_only=True)
    is_expired = serializers.ReadOnlyField()

    class Meta:
        model = SpendingRequest
        fields = [
            'id', 'requester', 'couple', 'amount', 'description',
            'category', 'status', 'requested_at', 'responded_at',
            'expires_at', 'is_expired'
        ]
        read_only_fields = ['id', 'requested_at', 'responded_at', 'expires_at']


class SharedTransactionSerializer(serializers.ModelSerializer):
    """
    Serializer for SharedTransaction model
    """
    performed_by = UserSerializer(read_only=True)

    class Meta:
        model = SharedTransaction
        fields = [
            'id', 'wallet', 'amount', 'transaction_type',
            'description', 'performed_by', 'transaction_date'
        ]
        read_only_fields = ['id', 'transaction_date']


class CoupleDashboardSerializer(serializers.ModelSerializer):
    """
    Serializer for CoupleDashboard model
    """
    couple = CoupleLinkSerializer(read_only=True)
    net_balance = serializers.ReadOnlyField()

    class Meta:
        model = CoupleDashboard
        fields = [
            'id', 'couple', 'total_contributions', 'total_expenses',
            'pending_requests', 'net_balance', 'last_updated'
        ]
        read_only_fields = ['id', 'last_updated']


class CoupleAlertSerializer(serializers.ModelSerializer):
    """
    Serializer for CoupleAlert model
    """
    couple = CoupleLinkSerializer(read_only=True)
    is_read_by_both = serializers.ReadOnlyField()

    class Meta:
        model = CoupleAlert
        fields = [
            'id', 'couple', 'alert_type', 'title', 'message',
            'is_read_user1', 'is_read_user2', 'is_read_by_both',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class CoupleOverviewSerializer(serializers.Serializer):
    """
    Serializer for couple financial overview
    """
    couple_info = CoupleLinkSerializer(read_only=True)
    wallet_balance = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    monthly_budget = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    pending_requests_count = serializers.IntegerField(read_only=True)
    recent_transactions = SharedTransactionSerializer(many=True, read_only=True)
    unread_alerts_count = serializers.IntegerField(read_only=True)


class CreateSpendingRequestSerializer(serializers.Serializer):
    """
    Serializer for creating spending requests
    """
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    description = serializers.CharField()
    category = serializers.CharField(max_length=100)


class ApproveRejectRequestSerializer(serializers.Serializer):
    """
    Serializer for approving/rejecting spending requests
    """
    action = serializers.ChoiceField(choices=['approve', 'reject'])


class AddFundsSerializer(serializers.Serializer):
    """
    Serializer for adding funds to shared wallet
    """
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    description = serializers.CharField(required=False)
