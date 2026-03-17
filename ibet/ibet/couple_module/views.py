from decimal import Decimal
from django.db import transaction
from rest_framework import viewsets, permissions, status, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Sum, Q
from django.utils import timezone
from datetime import datetime, timedelta
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from .models import (
    CoupleLink, SharedWallet, SpendingRequest, SharedTransaction,
    CoupleDashboard, CoupleAlert
)
from .serializers import (
    CoupleLinkSerializer, SharedWalletSerializer, SpendingRequestSerializer,
    SharedTransactionSerializer, CoupleDashboardSerializer, CoupleAlertSerializer,
    CoupleOverviewSerializer, CreateSpendingRequestSerializer,
    ApproveRejectRequestSerializer, AddFundsSerializer
)

User = get_user_model()


class CoupleLinkViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows couple links to be viewed or edited.
    """
    serializer_class = CoupleLinkSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return CoupleLink.objects.filter(
            Q(user1=self.request.user) | Q(user2=self.request.user),
            is_active=True
        )

    def perform_create(self, serializer):
        # This would typically be handled by a more complex linking process
        # For now, we'll assume the user provides the partner ID
        partner_id = self.request.data.get('partner_id')
        if not partner_id:
            raise serializers.ValidationError(_("Partner ID is required"))

        try:
            partner = User.objects.get(id=partner_id)
        except User.DoesNotExist:
            raise serializers.ValidationError(_("Partner not found"))

        # Check if either user is already in a couple
        if CoupleLink.objects.filter(
            Q(user1=self.request.user) | Q(user2=self.request.user) |
            Q(user1=partner) | Q(user2=partner),
            is_active=True
        ).exists():
            raise serializers.ValidationError(_("One or both users are already in a couple"))

        serializer.save(user1=self.request.user, user2=partner)


class SharedWalletViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows shared wallets to be viewed or edited.
    """
    serializer_class = SharedWalletSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return SharedWallet.objects.filter(
            couple__user1=self.request.user) | SharedWallet.objects.filter(
            couple__user2=self.request.user
        )

    @action(detail=True, methods=['post'])
    def add_funds(self, request, pk=None):
        """Add funds to the shared wallet"""
        wallet = self.get_object()
        serializer = AddFundsSerializer(data=request.data)

        if serializer.is_valid():
            amount = serializer.validated_data['amount']
            description = serializer.validated_data.get('description', 'Wallet deposit')

            wallet.add_funds(amount, request.user)
            return Response({
                'message': _('Successfully added %(amount)s to shared wallet') % {'amount': amount},
                'new_balance': wallet.balance
            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SpendingRequestViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows spending requests to be viewed or edited.
    """
    serializer_class = SpendingRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return SpendingRequest.objects.filter(
            Q(requester=self.request.user) |
            Q(couple__user1=self.request.user) |
            Q(couple__user2=self.request.user)
        )

    def perform_create(self, serializer):
        # Get the user's couple
        try:
            couple = CoupleLink.objects.get(
                Q(user1=self.request.user) | Q(user2=self.request.user),
                is_active=True
            )
        except CoupleLink.DoesNotExist:
            raise serializers.ValidationError(_("You must be part of a couple to create spending requests"))

        serializer.save(requester=self.request.user, couple=couple)

    @action(detail=True, methods=['post'])
    def respond(self, request, pk=None):
        """Approve or reject a spending request"""
        spending_request = self.get_object()
        serializer = ApproveRejectRequestSerializer(data=request.data)

        if serializer.is_valid():
            action = serializer.validated_data['action']

            if action == 'approve':
                if spending_request.approve(request.user):
                    return Response({'message': _('Request approved successfully')}, status=status.HTTP_200_OK)
                else:
                    return Response({'error': _('Could not approve request')}, status=status.HTTP_400_BAD_REQUEST)
            elif action == 'reject':
                if spending_request.reject(request.user):
                    return Response({'message': _('Request rejected successfully')}, status=status.HTTP_200_OK)
                else:
                    return Response({'error': _('Could not reject request')}, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SharedTransactionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows shared transactions to be viewed.
    """
    serializer_class = SharedTransactionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return SharedTransaction.objects.filter(
            Q(wallet__couple__user1=self.request.user) |
            Q(wallet__couple__user2=self.request.user)
        ).order_by('-transaction_date')


class CoupleDashboardViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows couple dashboards to be viewed or edited.
    """
    serializer_class = CoupleDashboardSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return CoupleDashboard.objects.filter(
            Q(couple__user1=self.request.user) |
            Q(couple__user2=self.request.user)
        )


class CoupleAlertViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows couple alerts to be viewed or edited.
    """
    serializer_class = CoupleAlertSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return CoupleAlert.objects.filter(
            Q(couple__user1=self.request.user) |
            Q(couple__user2=self.request.user)
        )

    @action(detail=True, methods=['patch'])
    def mark_as_read(self, request, pk=None):
        """Mark an alert as read for the current user."""
        alert = self.get_object()
        alert.mark_as_read(request.user)
        return Response({'status': _('Alert marked as read')})

    @action(detail=False, methods=['patch'])
    def mark_all_read(self, request):
        """Mark all alerts as read for the current user."""
        alerts = self.get_queryset()
        for alert in alerts:
            alert.mark_as_read(request.user)
        return Response({'status': _(' %(count)s alerts marked as read') % {'count': alerts.count()}})


class CoupleOverviewView(APIView):
    """
    API endpoint for couple financial overview.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user

        # Get couple information
        try:
            couple = CoupleLink.objects.get(
                Q(user1=user) | Q(user2=user),
                is_active=True
            )
        except CoupleLink.DoesNotExist:
            return Response(
                {'error': _('You are not part of an active couple')},
                status=status.HTTP_404_NOT_FOUND
            )

        # Get wallet information (Use CoupleWallet instead of legacy SharedWallet)
        from .models_wallet import CoupleWallet
        try:
            wallet = CoupleWallet.objects.get(
                Q(partner1=couple.user1, partner2=couple.user2) |
                Q(partner1=couple.user2, partner2=couple.user1)
            )
            wallet_balance = wallet.balance
            monthly_budget = wallet.monthly_budget
        except CoupleWallet.DoesNotExist:
            wallet_balance = 0.00
            monthly_budget = 0.00

        # Count pending requests
        pending_requests_count = SpendingRequest.objects.filter(
            couple=couple,
            status='PENDING'
        ).count()

        # Get recent transactions (last 10)
        from .models_wallet import CoupleWalletTransaction
        recent_transactions = []
        if 'wallet' in locals():
            recent_transactions = CoupleWalletTransaction.objects.filter(
                wallet=wallet
            ).order_by('-created_at')[:10]

        # Count unread alerts for current user
        unread_alerts_count = CoupleAlert.objects.filter(
            couple=couple
        ).exclude(
            Q(is_read_user1=True) if user == couple.user1 else Q(is_read_user2=True)
        ).count()

        # Create the response data
        response_data = {
            'couple_info': CoupleLinkSerializer(couple).data,
            'wallet_balance': float(wallet_balance),
            'monthly_budget': float(monthly_budget),
            'pending_requests_count': pending_requests_count,
            'unread_alerts_count': unread_alerts_count,
            'recent_transactions': []
        }
        
        # Handle transaction serialization robustly
        if recent_transactions:
            try:
                from .serializers_wallet import CoupleWalletTransactionSerializer
                response_data['recent_transactions'] = CoupleWalletTransactionSerializer(recent_transactions, many=True).data
            except ImportError:
                # Fallback to general serializer if specific one fails to import
                response_data['recent_transactions'] = SharedTransactionSerializer(recent_transactions, many=True).data

        return Response(response_data)


class CreateCoupleView(APIView):
    """
    API endpoint for creating a couple relationship.
    """
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        partner_username = request.data.get('partner_username')

        if not partner_username:
            return Response(
                {'error': _('Partner username is required')},
                status=status.HTTP_400_BAD_REQUEST
            )

        if partner_username == request.user.username:
            return Response(
                {'error': _('You cannot link with yourself')},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            partner = User.objects.get(username=partner_username)
        except User.DoesNotExist:
            return Response(
                {'error': _('Partner not found')},
                status=status.HTTP_404_NOT_FOUND
            )

        # Check if either user is already in a couple
        if CoupleLink.objects.filter(
            Q(user1=request.user) | Q(user2=request.user) |
            Q(user1=partner) | Q(user2=partner),
            is_active=True
        ).exists():
            return Response(
                {'error': _('One or both users are already in a couple')},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create couple link
        couple = CoupleLink.objects.create(user1=request.user, user2=partner)

        # Create couple wallet (from models_wallet.py)
        from .models_wallet import CoupleWallet
        # Ensure consistent ordering for partner1/partner2 to respect unique_together
        p1, p2 = (request.user, partner) if request.user.id < partner.id else (partner, request.user)
        
        CoupleWallet.objects.get_or_create(
            partner1=p1,
            partner2=p2,
            defaults={
                'balance': Decimal('0.00'),
                'monthly_budget': Decimal('0.00')
            }
        )

        # Create dashboard
        CoupleDashboard.objects.get_or_create(couple=couple)

        return Response(
            CoupleLinkSerializer(couple).data,
            status=status.HTTP_201_CREATED
        )


class UnlinkCoupleView(APIView):
    """
    API endpoint for unlinking a couple relationship.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        try:
            couple = CoupleLink.objects.get(
                Q(user1=request.user) | Q(user2=request.user),
                is_active=True
            )
            
            # Delete shared resources (or mark as inactive)
            # For a clean reset, we'll delete the link and associated wallet
            from .models_wallet import CoupleWallet
            CoupleWallet.objects.filter(
                Q(partner1=request.user) | Q(partner2=request.user)
            ).delete()
            
            couple.delete()
            
            return Response({'message': _('Successfully unlinked from partner')})
        except CoupleLink.DoesNotExist:
            return Response(
                {'error': _('No active couple link found')},
                status=status.HTTP_404_NOT_FOUND
            )
