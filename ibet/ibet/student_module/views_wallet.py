"""
Secure wallet views for Student Module.
Provides secure wallet operations with parent approval and OTP protection.
"""
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils.translation import gettext_lazy as _
from django.db import transaction
from core.throttling import OTPGenerationThrottle, OTPVerificationThrottle, WalletAccessThrottle, SensitiveOperationsThrottle
from core.security import OTPSecurityService, SecurityUtils
from core.security_monitoring_fixed import SecurityEventManager, AuditService
from core.permissions import OTPGenerationPermission, OTPVerificationPermission
from .models import Wallet, OTPRequest, ParentStudentLink, StudentWalletOTPRequest, DailySpending, SpendingLock, StudentNotification, DailyAllowance, CumulativeSpendingTracker, User
from .serializers_wallet import StudentWalletSerializer
from django.db.models import Sum
from django.utils import timezone
from decimal import Decimal
import logging
import random

logger = logging.getLogger(__name__)

class StudentWalletViewSet(viewsets.ModelViewSet):
    """
    Secure API endpoint for student wallet management.
    """
    serializer_class = StudentWalletSerializer
    permission_classes = [permissions.IsAuthenticated, WalletAccessPermission]
    throttle_classes = [WalletAccessThrottle]

    def get_queryset(self):
        return Wallet.objects.filter(user=self.request.user)

    def get_object(self):
        wallet, created = Wallet.objects.get_or_create(user=self.request.user)
        return wallet

    @action(detail=False, methods=['get'])
    def balance(self, request):
        wallet = self.get_object()
        return Response({
            'balance': wallet.balance,
            'special_balance': wallet.special_balance,
            'is_locked': wallet.is_locked,
            'last_transaction_at': wallet.last_transaction_at
        })

    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated, WalletAccessPermission, OTPVerificationPermission])
    def deposit(self, request):
        wallet = self.get_object()
        amount = Decimal(str(request.data.get('amount', 0)))
        otp = request.data.get('otp')
        cache_key = request.data.get('cache_key')
        
        if amount <= 0: return Response({'error': 'Invalid amount'}, 400)
        if not otp: return Response({'error': 'OTP is required'}, 400)
        if not cache_key: return Response({'error': 'Cache key is required'}, 400)
        
        # Verify OTP
        is_valid, msg = OTPSecurityService.validate_otp(request.user.id, otp, cache_key, 'wallet_operation')
        if not is_valid:
            return Response({'error': msg}, 400)
            
        new_balance = wallet.deposit_main(amount, _('Direct Deposit'))
        return Response({'message': 'Deposit successful', 'new_balance': new_balance})

    @action(detail=False, methods=['post'])
    def withdraw(self, request):
        """Consolidated withdrawal logic with strict limit and lock enforcement"""
        try:
            wallet = self.get_object()
            amount = Decimal(str(request.data.get('amount', 0)))
            description = request.data.get('description', _('Withdrawal'))

            if amount <= 0:
                return Response({'error': _('Invalid amount')}, status=status.HTTP_400_BAD_REQUEST)

            today = timezone.localdate()
            
            # 1. Check for Active Lock
            active_lock = SpendingLock.objects.filter(student=request.user, is_active=True).first()
            if active_lock or wallet.is_locked:
                return self._handle_pending_approval(request.user, amount, description, "LOCKED")

            # 2. Check Cumulative Limit
            cumulative_available = Decimal('0.00')
            try:
                tracker = CumulativeSpendingTracker.objects.get(student=request.user, month=today.month, year=today.year)
                cumulative_available = tracker.total_available
            except CumulativeSpendingTracker.DoesNotExist:
                # Fallback to daily spending record if tracker missing
                ds, _ = DailySpending.objects.get_or_create(student=request.user, date=today, defaults={'daily_limit': 0, 'remaining_amount': 0})
                cumulative_available = ds.remaining_amount

            if amount > cumulative_available:
                return self._handle_pending_approval(request.user, amount, description, "LIMIT_EXCEEDED")

            # 3. Process Valid Withdrawal
            if wallet.balance < amount:
                return Response({'error': _('Insufficient wallet balance')}, status=status.HTTP_400_BAD_REQUEST)

            with transaction.atomic():
                new_balance = wallet.withdraw_main(amount, description)
                
                # Update Daily spending tracker
                ds, _ = DailySpending.objects.get_or_create(student=request.user, date=today, defaults={'daily_limit': 0, 'remaining_amount': 0})
                ds.amount_spent += amount
                ds.remaining_amount -= amount
                ds.save()

                # Update Cumulative tracker
                tracker, _ = CumulativeSpendingTracker.objects.get_or_create(student=request.user, month=today.month, year=today.year)
                tracker.total_spent += amount
                tracker.total_available -= amount
                tracker.save()

            return Response({
                'message': _('Withdrawal successful'),
                'new_balance': new_balance,
                'today_spent': float(amount)
            })

        except Exception as e:
            logger.error(f"Withdrawal error: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def _handle_pending_approval(self, student, amount, description, reason):
        """Helper to create OTP request and notify parent"""
        try:
            parent_link = ParentStudentLink.objects.get(student=student)
            parent = parent_link.parent
            
            otp_req, created = OTPRequest.objects.get_or_create(
            student=student, 
            parent=parent, 
            is_used=False,
            expires_at__gt=timezone.now(),
            defaults={
            'otp_code': str(random.randint(100000, 999999)),
            'amount_requested': amount,
            'expires_at': timezone.now() + timezone.timedelta(minutes=30)
            }
            )            
            # Notify parent via ParentAlert (for dashboard visibility)
            from parent_module.models import ParentAlert
            ParentAlert.objects.get_or_create(
                parent=parent, student=student, alert_type='UNLOCK_REQUEST',
                message=_(f'{student.username} needs ₹{amount} for "{description}". OTP: {otp_req.otp_code}'),
                status='UNREAD'
            )
            
            return Response({
                'status': 'pending_approval',
                'message': _('Approval required. OTP sent to parent.'),
                'otp_request_id': otp_req.id,
                'requires_parent_otp': True,
                'reason': reason
            }, status=status.HTTP_402_PAYMENT_REQUIRED)
        except ParentStudentLink.DoesNotExist:
            return Response({'error': _('No parent linked to this student.')}, status=status.HTTP_403_FORBIDDEN)

    @action(detail=False, methods=['post'])
    def verify_parent_otp(self, request):
        """Verify OTP and process the BLOCKED withdrawal"""
        otp_code = request.data.get('otp_code')
        otp_request_id = request.data.get('otp_request_id')
        
        try:
            otp_request = OTPRequest.objects.get(id=otp_request_id, student=request.user, is_used=False)
            
            if otp_request.is_expired():
                return Response({'error': _('OTP has expired')}, status=status.HTTP_400_BAD_REQUEST)
            if otp_request.otp_code != otp_code:
                return Response({'error': _('Invalid OTP')}, status=status.HTTP_400_BAD_REQUEST)
            
            # --- SUCCESS: COMPLETE TRANSACTION ---
            with transaction.atomic():
                otp_request.mark_as_used()
                wallet = self.get_object()
                amount = otp_request.amount_requested
                
                # Deduct money
                new_balance = wallet.withdraw_main(amount, _('Approved by Parent via OTP'))
                
                # Update spending trackers (Only now!)
                today = timezone.localdate()
                ds, _ = DailySpending.objects.get_or_create(student=request.user, date=today)
                ds.amount_spent += amount
                ds.remaining_amount -= amount
                ds.save()

                tracker, _ = CumulativeSpendingTracker.objects.get_or_create(student=request.user, month=today.month, year=today.year)
                tracker.total_spent += amount
                tracker.total_available -= amount
                tracker.save()

            return Response({
                'message': _('Withdrawal successful! Parent approval verified.'),
                'new_balance': new_balance,
                'amount_withdrawn': float(amount)
            })
            
        except OTPRequest.DoesNotExist:
            return Response({'error': _('Invalid or expired request')}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def special_withdraw(self, request):
        wallet = self.get_object()
        amount = Decimal(str(request.data.get('amount', 0)))
        if amount <= 0: return Response({'error': 'Invalid amount'}, 400)
        if wallet.special_balance < amount: return Response({'error': 'Insufficient special funds'}, 400)
        new_balance = wallet.withdraw_special(amount, _('Special Withdrawal'))
        return Response({'message': 'Special withdrawal successful', 'new_special_balance': new_balance})

class GenerateStudentWalletOTPView(APIView):
    permission_classes = [permissions.IsAuthenticated, OTPGenerationPermission]
    def post(self, request):
        amount = request.data.get('amount')
        operation_type = request.data.get('operation_type', 'wallet_operation')
        
        # Use user's email if available for OTP delivery
        email = getattr(request.user, 'email', None)
        
        otp_res = OTPSecurityService.create_otp_request(
            user_id=request.user.id,
            purpose=operation_type,
            email=email
        )
        return Response(otp_res)

class VerifyStudentWalletOTPView(APIView):
    permission_classes = [permissions.IsAuthenticated, OTPVerificationPermission]
    def post(self, request):
        otp = request.data.get('otp_code')
        cache_key = request.data.get('cache_key')
        operation_type = request.data.get('operation_type', 'wallet_operation')
        
        is_valid, msg = OTPSecurityService.validate_otp(
            user_id=request.user.id,
            otp_code=otp,
            cache_key=cache_key,
            purpose=operation_type
        )
        if is_valid:
            return Response({'message': msg})
        return Response({'error': msg}, status=400)
