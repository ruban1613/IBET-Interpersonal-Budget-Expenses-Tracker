"""
Secure wallet views for Couple Module.
Provides secure shared wallet operations with OTP protection and monitoring.
"""
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils.translation import gettext_lazy as _
from django.db import models
from core.throttling import OTPGenerationThrottle, OTPVerificationThrottle, WalletAccessThrottle, SensitiveOperationsThrottle
from core.security import OTPSecurityService, SecurityUtils
from core.security_monitoring import SecurityEventManager, AuditService
from core.permissions import OTPGenerationPermission, OTPVerificationPermission
from .models_wallet import CoupleWallet, CoupleWalletTransaction, CoupleWalletOTPRequest
from django.db.models import Sum
from django.utils import timezone
from decimal import Decimal


class CoupleWalletViewSet(viewsets.ModelViewSet):
    """
    Secure API endpoint for couple wallet management.
    """
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [WalletAccessThrottle]

    def get_queryset(self):
        # Users can only access wallets where they are a partner
        return CoupleWallet.objects.filter(
            models.Q(partner1=self.request.user) | models.Q(partner2=self.request.user)
        )

    def get_object(self):
        return CoupleWallet.objects.get(
            models.Q(partner1=self.request.user) | models.Q(partner2=self.request.user)
        )

    @action(detail=False, methods=['get'])
    def balance(self, request):
        """Get wallet balance securely"""
        try:
            wallet = self.get_object()
            SecurityEventManager.log_event(
                SecurityEventManager.EVENT_TYPES['WALLET_ACCESS'],
                request.user.id,
                {'action': 'balance_check', 'wallet_type': 'couple'}
            )

            return Response({
                'balance': wallet.balance,
                'emergency_fund': wallet.emergency_fund,
                'joint_goals': wallet.joint_goals,
                'available_balance': wallet.available_balance,
                'monthly_budget': wallet.monthly_budget,
                'is_locked': wallet.is_locked,
                'last_transaction_at': wallet.last_transaction_at,
                'partner1': wallet.partner1.username,
                'partner2': wallet.partner2.username
            })
        except CoupleWallet.DoesNotExist:
            return Response({'error': _('Couple wallet not found')}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['post'])
    def deposit(self, request):
        """Secure deposit to couple wallet"""
        try:
            wallet = self.get_object()
            amount = Decimal(request.data.get('amount', 0))
            description = request.data.get('description', 'Deposit')

            if amount <= 0:
                return Response({'error': _('Invalid amount')}, status=status.HTTP_400_BAD_REQUEST)

            # Check for suspicious activity
            if SecurityEventManager.detect_suspicious_activity(
                request.user.id, 'couple_wallet_deposit', threshold=5, time_window_minutes=30
            ):
                return Response(
                    {'error': _('Suspicious activity detected')},
                    status=status.HTTP_429_TOO_MANY_REQUESTS
                )

            new_balance = wallet.deposit(amount, description, request.user)

            # Audit the operation
            AuditService.audit_wallet_operation(
                request.user.id,
                'couple_deposit',
                amount,
                {'description': description, 'wallet_type': 'couple'}
            )

            SecurityEventManager.log_event(
                SecurityEventManager.EVENT_TYPES['FUND_TRANSFER'],
                request.user.id,
                {'amount': amount, 'new_balance': new_balance, 'wallet_type': 'couple', 'transfer_type': 'credit'}
            )

            return Response({
                'message': _('Deposit successful'),
                'new_balance': new_balance,
                'deposited_by': request.user.username
            })

        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def withdraw(self, request):
        """Secure withdrawal from couple wallet"""
        try:
            wallet = self.get_object()
            amount = Decimal(request.data.get('amount', 0))
            description = request.data.get('description', 'Withdrawal')

            if amount <= 0:
                return Response({'error': _('Invalid amount')}, status=status.HTTP_400_BAD_REQUEST)

            # Check for suspicious activity
            if SecurityEventManager.detect_suspicious_activity(
                request.user.id, 'couple_wallet_withdrawal', threshold=3, time_window_minutes=15
            ):
                return Response(
                    {'error': _('Suspicious activity detected')},
                    status=status.HTTP_429_TOO_MANY_REQUESTS
                )

            new_balance = wallet.withdraw(amount, description, request.user)

            # Audit the operation
            AuditService.audit_wallet_operation(
                request.user.id,
                'couple_withdrawal',
                amount,
                {'description': description, 'wallet_type': 'couple'}
            )

            SecurityEventManager.log_event(
                SecurityEventManager.EVENT_TYPES['FUND_TRANSFER'],
                request.user.id,
                {'amount': amount, 'new_balance': new_balance, 'wallet_type': 'couple', 'transfer_type': 'debit'}
            )

            return Response({
                'message': _('Withdrawal successful'),
                'new_balance': new_balance,
                'withdrawn_by': request.user.username
            })

        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def transfer_to_emergency(self, request):
        """Transfer money to emergency fund"""
        try:
            wallet = self.get_object()
            amount = Decimal(request.data.get('amount', 0))
            description = request.data.get('description', 'Emergency Fund Transfer')

            if amount <= 0:
                return Response({'error': _('Invalid amount')}, status=status.HTTP_400_BAD_REQUEST)

            new_balance = wallet.transfer_to_emergency(amount, description)

            # Audit the operation
            AuditService.audit_wallet_operation(
                request.user.id,
                'couple_emergency_transfer',
                amount,
                {'description': description, 'wallet_type': 'couple'}
            )

            SecurityEventManager.log_event(
                SecurityEventManager.EVENT_TYPES['FUND_TRANSFER'],
                request.user.id,
                {'amount': amount, 'new_balance': new_balance, 'type': 'emergency_fund', 'wallet_type': 'couple', 'transfer_type': 'transfer'}
            )

            return Response({
                'message': _('Transfer to emergency fund successful'),
                'new_balance': new_balance,
                'emergency_fund': wallet.emergency_fund
            })

        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def transfer_to_goals(self, request):
        """Transfer money to joint goals"""
        try:
            wallet = self.get_object()
            amount = Decimal(request.data.get('amount', 0))
            goal_name = request.data.get('goal_name', 'Joint Goal')

            if amount <= 0:
                return Response({'error': _('Invalid amount')}, status=status.HTTP_400_BAD_REQUEST)

            new_balance = wallet.transfer_to_goals(amount, goal_name)

            # Audit the operation
            AuditService.audit_wallet_operation(
                request.user.id,
                'couple_goal_transfer',
                amount,
                {'goal_name': goal_name, 'wallet_type': 'couple'}
            )

            SecurityEventManager.log_event(
                SecurityEventManager.EVENT_TYPES['FUND_TRANSFER'],
                request.user.id,
                {'amount': amount, 'new_balance': new_balance, 'type': 'joint_goals', 'wallet_type': 'couple', 'transfer_type': 'transfer'}
            )

            return Response({
                'message': _('Transfer to joint goals successful'),
                'new_balance': new_balance,
                'joint_goals': wallet.joint_goals,
                'goal_name': goal_name
            })

        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def monthly_summary(self, request):
        """Get monthly transaction summary"""
        try:
            wallet = self.get_object()
            current_month = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)

            # Get monthly transactions
            transactions = CoupleWalletTransaction.objects.filter(
                wallet=wallet,
                created_at__gte=current_month
            ).aggregate(
                total_deposits=Sum('amount', filter=models.Q(transaction_type='DEPOSIT')),
                total_withdrawals=Sum('amount', filter=models.Q(transaction_type='WITHDRAWAL')),
                total_transfers=Sum('amount', filter=models.Q(transaction_type__in=['EMERGENCY_TRANSFER', 'GOAL_TRANSFER'])),
                transaction_count=models.Count('id')
            )

            return Response({
                'total_deposits': transactions['total_deposits'] or Decimal('0.00'),
                'total_withdrawals': transactions['total_withdrawals'] or Decimal('0.00'),
                'total_transfers': transactions['total_transfers'] or Decimal('0.00'),
                'transaction_count': transactions['transaction_count'] or 0,
                'monthly_budget': wallet.monthly_budget,
                'budget_utilization': ((transactions['total_withdrawals'] or Decimal('0.00')) / wallet.monthly_budget * 100) if wallet.monthly_budget > 0 else 0
            })

        except CoupleWallet.DoesNotExist:
            return Response({'error': _('Couple wallet not found')}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['get'])
    def welcome(self, request):
        """Welcome endpoint for couple wallet API"""
        SecurityEventManager.log_event(
            SecurityEventManager.EVENT_TYPES['API_ACCESS'],
            request.user.id,
            {'action': 'welcome', 'method': request.method, 'path': request.path, 'wallet_type': 'couple'}
        )
        return Response({'message': 'Welcome to the Couple Wallet API Service!'})


class CoupleWalletTransactionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    View transaction history for couple wallets.
    """
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [WalletAccessThrottle]

    def get_queryset(self):
        return CoupleWalletTransaction.objects.filter(
            wallet__partner1=self.request.user
        ) | CoupleWalletTransaction.objects.filter(
            wallet__partner2=self.request.user
        )


class GenerateCoupleWalletOTPView(APIView):
    """
    Secure API endpoint for generating OTP for couple wallet operations.
    """
    permission_classes = [permissions.IsAuthenticated, OTPGenerationPermission]
    throttle_classes = [OTPGenerationThrottle, SensitiveOperationsThrottle]

    def post(self, request, *args, **kwargs):
        operation_type = request.data.get('operation_type')
        amount = request.data.get('amount')
        description = request.data.get('description', '')

        if not operation_type:
            return Response({'error': _('Operation type is required')}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Get couple wallet
            wallet = CoupleWallet.objects.get(
                models.Q(partner1=request.user) | models.Q(partner2=request.user)
            )
        except CoupleWallet.DoesNotExist:
            return Response({'error': _('Couple wallet not found')}, status=status.HTTP_404_NOT_FOUND)

        # Generate secure OTP
        otp_request_data = OTPSecurityService.create_otp_request(
            request.user.id,
            'couple_wallet_operation'
        )

        # Set expiration time (10 minutes from now)
        expires_at = timezone.now() + timezone.timedelta(minutes=10)

        # Create OTP request
        otp_request = CoupleWalletOTPRequest.objects.create(
            user=request.user,
            wallet=wallet,
            operation_type=operation_type,
            amount=amount,
            description=description,
            otp_code='',  # Don't store the actual OTP
            expires_at=expires_at,
            cache_key=otp_request_data['cache_key']
        )

        # Audit the OTP generation
        AuditService.audit_otp_operation(
            request.user.id,
            'generate',
            True,
            {
                'operation_type': operation_type,
                'amount': amount,
                'description': description,
                'wallet_type': 'couple'
            }
        )

        SecurityEventManager.log_event(
            SecurityEventManager.EVENT_TYPES['OTP_GENERATED'],
            request.user.id,
            {
                'operation_type': operation_type,
                'amount': amount,
                'expires_at': expires_at.isoformat(),
                'wallet_type': 'couple'
            }
        )

        return Response({
            'message': _('OTP generated successfully for couple wallet operation'),
            'otp_request_id': otp_request.id,
            'operation_type': operation_type,
            'expires_at': expires_at,
            'note': _('The OTP has been securely generated and must be shared with the user directly.')
        }, status=status.HTTP_201_CREATED)


class VerifyCoupleWalletOTPView(APIView):
    """
    Secure API endpoint for verifying OTP for couple wallet operations.
    """
    permission_classes = [permissions.IsAuthenticated, OTPVerificationPermission]
    throttle_classes = [OTPVerificationThrottle, SensitiveOperationsThrottle]

    def post(self, request, *args, **kwargs):
        otp_code = request.data.get('otp_code')
        otp_request_id = request.data.get('otp_request_id')

        if not otp_code or not otp_request_id:
            return Response({'error': _('OTP code and request ID are required')}, status=status.HTTP_400_BAD_REQUEST)

        try:
            otp_request = CoupleWalletOTPRequest.objects.get(
                id=otp_request_id,
                user=request.user,
                is_used=False
            )

            if otp_request.is_expired():
                otp_request.delete()
                SecurityEventManager.log_event(
                    SecurityEventManager.EVENT_TYPES['OTP_FAILED'],
                    request.user.id,
                    {'reason': 'OTP expired', 'wallet_type': 'couple'}
                )
                return Response({'error': _('OTP has expired')}, status=status.HTTP_400_BAD_REQUEST)

            # Validate OTP using security service
            cache_key = f"otp_request_{otp_request.id}"
            is_valid, error_message = OTPSecurityService.validate_otp(
                request.user.id,
                otp_code,
                cache_key,
                'couple_wallet_operation'
            )

            if not is_valid:
                SecurityEventManager.log_event(
                    SecurityEventManager.EVENT_TYPES['OTP_FAILED'],
                    request.user.id,
                    {'reason': error_message, 'wallet_type': 'couple'}
                )
                return Response({'error': error_message}, status=status.HTTP_400_BAD_REQUEST)

            # Mark OTP as used
            otp_request.mark_as_used()

            # Audit successful verification
            AuditService.audit_otp_operation(
                request.user.id,
                'verify',
                True,
                {
                    'operation_type': otp_request.operation_type,
                    'amount': otp_request.amount,
                    'wallet_type': 'couple'
                }
            )

            SecurityEventManager.log_event(
                SecurityEventManager.EVENT_TYPES['OTP_VERIFIED'],
                request.user.id,
                {
                    'operation_type': otp_request.operation_type,
                    'amount': otp_request.amount,
                    'success': True,
                    'wallet_type': 'couple'
                }
            )

            return Response({
                'message': _('OTP verified successfully'),
                'operation_type': otp_request.operation_type,
                'amount': otp_request.amount,
                'description': otp_request.description,
                'wallet_type': 'couple'
            })

        except CoupleWalletOTPRequest.DoesNotExist:
            SecurityEventManager.log_event(
                SecurityEventManager.EVENT_TYPES['OTP_FAILED'],
                request.user.id,
                {'reason': 'Invalid OTP request', 'wallet_type': 'couple'}
            )
            return Response({'error': _('Invalid OTP request')}, status=status.HTTP_400_BAD_REQUEST)
