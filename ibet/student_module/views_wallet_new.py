"""
New Student Wallet Views with Cumulative Daily Allowance System.

This implements:
- Monthly allowance divided equally across days
- Students can spend from available days
- Future days get locked if overspent
- At midnight, new day's allowance becomes available
- Parent OTP required for extra spending
"""

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from django.utils.translation import gettext_lazy as _
from django.db import transaction
from core.throttling import OTPGenerationThrottle, OTPVerificationThrottle, WalletAccessThrottle, SensitiveOperationsThrottle
from core.security import OTPSecurityService
from core.security_monitoring_fixed import SecurityEventManager, AuditService
from core.permissions import OTPGenerationPermission, OTPVerificationPermission, WalletAccessPermission
from .models import (
    Wallet, 
    OTPRequest, 
    ParentStudentLink, 
    StudentWalletOTPRequest,
    DailyAllowance,
    CumulativeSpendingTracker,
    PendingSpendingRequest,
    StudentNotification,
    MonthlyAllowance,
    SpendingLock,
    DailySpending,
    Transaction
)
from parent_module.models import ParentAlert
from .serializers_wallet import StudentWalletSerializer
from django.db.models import Sum
from django.utils import timezone
from datetime import date, timedelta
from decimal import Decimal
import random
import logging

logger = logging.getLogger(__name__)


def initialize_daily_allowances(student, monthly_amount, days_in_month, start_date):
    """
    Initialize daily allowances for a student based on monthly allowance.
    Creates DailyAllowance records for each day of the month.
    """
    daily_amount = monthly_amount / days_in_month
    allowances = []
    
    for day_offset in range(days_in_month):
        day_date = start_date + timedelta(days=day_offset)
        
        # Check if already exists
        allowance, created = DailyAllowance.objects.get_or_create(
            student=student,
            date=day_date,
            defaults={
                'daily_amount': daily_amount,
                'amount_spent': Decimal('0.00'),
                'remaining_amount': daily_amount,
                'is_available': True,
                'is_locked': False
            }
        )
        allowances.append(allowance)
    
    # Update cumulative tracker
    CumulativeSpendingTracker.objects.update_or_create(
        student=student,
        month=start_date.month,
        year=start_date.year,
        defaults={
            'total_allocated': monthly_amount,
            'total_spent': Decimal('0.00'),
            'total_available': monthly_amount,
            'days_available': days_in_month,
            'current_day_date': start_date
        }
    )
    
    return allowances


def get_today_available_amount(student, check_date=None):
    """
    Get ONLY today's available amount - this is what student can spend without OTP.
    Student can only spend one day's allowance per day without parent approval.
    """
    if check_date is None:
        check_date = date.today()
    
    # Get ONLY today's allowance
    try:
        today_allowance = DailyAllowance.objects.get(
            student=student,
            date=check_date,
            is_available=True,
            is_locked=False
        )
        return today_allowance.remaining_amount
    except DailyAllowance.DoesNotExist:
        return Decimal('0.00')


def get_all_available_amount(student, check_date=None):
    """
    Get total available amount across ALL available days (for display purposes).
    This is NOT what student can spend without OTP - they can only spend today's amount.
    """
    if check_date is None:
        check_date = date.today()
    
    # Get ALL available (unlocked) daily allowances
    available_allowances = DailyAllowance.objects.filter(
        student=student,
        is_available=True,
        is_locked=False
    )
    
    total_available = sum(
        allowance.remaining_amount for allowance in available_allowances
    )
    
    return total_available


def process_withdrawal(student, amount):
    """
    Process a withdrawal from available daily allowances.
    Returns (success, message, amount_withdrawn, locked_days_count)
    """
    today = timezone.localdate()
    
    # Get ALL available daily allowances sorted by date - cumulative system allows spending from all!
    available_allowances = DailyAllowance.objects.filter(
        student=student,
        is_available=True,
        is_locked=False
    ).order_by('date')
    
    remaining_to_spend = amount
    total_withdrawn = Decimal('0.00')
    locked_days = []
    
    for allowance in available_allowances:
        if remaining_to_spend <= 0:
            break
            
        # Calculate how much we can spend from this day
        available_today = allowance.remaining_amount
        
        if available_today >= remaining_to_spend:
            # We can fulfill from this day's allowance
            allowance.amount_spent += remaining_to_spend
            allowance.remaining_amount -= remaining_to_spend
            total_withdrawn += remaining_to_spend
            remaining_to_spend = 0
            
            # Check if this day is now fully spent
            if allowance.remaining_amount <= 0:
                allowance.is_available = False
                allowance.is_locked = True
                allowance.lock_reason = 'Daily limit exceeded'
                locked_days.append(allowance.date)
            
            allowance.save()
        else:
            # Use all of this day's allowance and continue to next day
            allowance.amount_spent += available_today
            allowance.remaining_amount = Decimal('0.00')
            allowance.is_available = False
            allowance.is_locked = True
            allowance.lock_reason = 'Daily limit exceeded'
            total_withdrawn += available_today
            remaining_to_spend -= available_today
            locked_days.append(allowance.date)
            allowance.save()
    
    # Update cumulative tracker
    try:
        tracker = CumulativeSpendingTracker.objects.get(
            student=student,
            month=today.month,
            year=today.year
        )
        tracker.total_spent += total_withdrawn
        tracker.total_available -= total_withdrawn
        tracker.days_available = DailyAllowance.objects.filter(
            student=student,
            is_available=True,
            is_locked=False
        ).count()
        tracker.save()
    except CumulativeSpendingTracker.DoesNotExist:
        pass

    # Update DailySpending (old system for dashboard compatibility)
    try:
        daily, created = DailySpending.objects.get_or_create(
            student=student, 
            date=today,
            defaults={'daily_limit': 0, 'remaining_amount': 0}
        )
        daily.amount_spent += total_withdrawn
        daily.remaining_amount -= total_withdrawn
        if daily.remaining_amount <= 0:
            daily.is_locked = True
            daily.lock_reason = 'Daily limit exceeded'
        daily.save()
    except Exception as e:
        print(f"Error updating DailySpending from withdrawal: {e}")
    
    if remaining_to_spend > 0:
        return False, "Insufficient available funds", total_withdrawn, locked_days
    
    return True, "Withdrawal successful", total_withdrawn, locked_days


def activate_today_allowance(student):
    """
    Activate today's allowance if it's not already active.
    Called at midnight or when checking availability.
    """
    today = timezone.localdate()
    
    # Check if today's allowance exists and is not available
    try:
        today_allowance = DailyAllowance.objects.get(
            student=student,
            date=today
        )
        
        if not today_allowance.is_available and not today_allowance.is_locked:
            # Yesterday's allowance might have been locked, check yesterday
            yesterday = today - timedelta(days=1)
            try:
                yesterday_allowance = DailyAllowance.objects.get(
                    student=student,
                    date=yesterday
                )
                # If yesterday is fully spent, unlock today's
                if yesterday_allowance.remaining_amount <= 0:
                    today_allowance.is_available = True
                    today_allowance.save()
            except DailyAllowance.DoesNotExist:
                pass
                
    except DailyAllowance.DoesNotExist:
        # No allowance for today, check if we need to create it
        # This would typically be handled by the monthly allowance setup
        pass


class StudentWalletViewSet(viewsets.ModelViewSet):
    """
    Secure API endpoint for student wallet management with cumulative daily allowance.
    """
    serializer_class = StudentWalletSerializer
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [WalletAccessThrottle]

    def get_queryset(self):
        return Wallet.objects.filter(user=self.request.user)

    def get_object(self):
        wallet, created = Wallet.objects.get_or_create(user=self.request.user)
        return wallet

    def list(self, request, *args, **kwargs):
        """Override list to return single wallet object instead of array"""
        wallet = self.get_object()
        serializer = self.get_serializer(wallet)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def balance(self, request):
        """Get wallet balance securely"""
        wallet = self.get_object()
        return Response({
            'balance': wallet.balance,
            'special_balance': wallet.special_balance,
            'is_locked': wallet.is_locked,
            'last_transaction_at': wallet.last_transaction_at
        })

    @action(detail=False, methods=['post'])
    def withdraw(self, request):
        """
        Secure withdrawal from student wallet.
        Checks against today's limit and handles dual-locking.
        """
        try:
            wallet = self.get_object()
            amount = Decimal(str(request.data.get('amount', 0)))
            description = request.data.get('description', '')
            student = request.user
            today = timezone.localdate()

            # 1. Fetch source of truth for Daily Limit
            allowance = MonthlyAllowance.objects.filter(student=student, is_active=True).first()
            if not allowance:
                return Response({'error': _('No active monthly allowance found.')}, status=status.HTTP_400_BAD_REQUEST)
            
            base_daily_limit = allowance.get_daily_allowance()

            # 2. Get current daily trackers
            da, created = DailyAllowance.objects.get_or_create(
                student=student, date=today, 
                defaults={'daily_amount': base_daily_limit, 'remaining_amount': base_daily_limit}
            )
            
            # 3. STRICT CHECK: Total spent vs Base Limit
            # If they already spent >= limit, they are LOCKED for further spending without OTP
            if wallet.is_locked or da.amount_spent >= base_daily_limit or (da.amount_spent + amount) > base_daily_limit:
                # Ensure a formal SpendingLock record exists for the UI
                SpendingLock.objects.get_or_create(
                    student=student,
                    lock_type='DAILY_LIMIT',
                    is_active=True,
                    defaults={'amount_locked': abs(da.remaining_amount)}
                )
                
                # Force hard lock on wallet object
                if not wallet.is_locked:
                    wallet.is_locked = True
                    wallet.save()
                
                # Need Parent Approval
                parent_link = ParentStudentLink.objects.filter(student=student).first()
                if not parent_link:
                    return Response({'error': _('Limit exceeded and no parent linked.')}, status=status.HTTP_403_FORBIDDEN)

                # Lock the account record if not already
                if not wallet.is_locked:
                    wallet.is_locked = True
                    wallet.save()
                
                # Create/Get OTP Request
                pending_request, created = PendingSpendingRequest.objects.get_or_create(
                    student=student, status='PENDING', expires_at__gt=timezone.now(),
                    defaults={
                        'parent': parent_link.parent,
                        'amount_requested': amount,
                        'otp_code': str(random.randint(100000, 999999)),
                        'expires_at': timezone.now() + timedelta(minutes=30),
                        'request_message': description or _('Extra spending request')
                    }
                )

                # Notify parent
                ParentAlert.objects.get_or_create(
                    parent=parent_link.parent, student=student, alert_type='SPENDING_REQUEST',
                    message=_(f'{student.username} wants to spend ₹{amount}. OTP: {pending_request.otp_code}'),
                    status='UNREAD'
                )

                return Response({
                    'status': 'pending_approval',
                    'message': _('Daily limit reached. Parent approval required.'),
                    'requires_parent_otp': True,
                    'otp_request_id': pending_request.id,
                    'requested_amount': float(amount)
                }, status=status.HTTP_202_ACCEPTED)

            # 4. Process Normal Withdrawal (Within Limit)
            if amount <= 0:
                return Response({'error': _('Invalid amount')}, status=status.HTTP_400_BAD_REQUEST)

            if wallet.balance < amount:
                return Response({'error': _('Insufficient wallet balance')}, status=status.HTTP_400_BAD_REQUEST)

            with transaction.atomic():
                wallet.balance -= amount
                wallet.last_transaction_at = timezone.now()
                
                da.amount_spent += amount
                da.remaining_amount = max(Decimal('0.00'), base_daily_limit - da.amount_spent)
                
                if da.remaining_amount <= 0:
                    wallet.is_locked = True
                    da.is_locked = True
                    SpendingLock.objects.get_or_create(student=student, lock_type='DAILY_LIMIT', is_active=True, defaults={'amount_locked': 0})
                
                wallet.save()
                da.save()

                # Sync old tracker for dashboard compatibility
                ds, created = DailySpending.objects.get_or_create(student=student, date=today, defaults={'daily_limit': base_daily_limit})
                ds.amount_spent = da.amount_spent
                ds.remaining_amount = da.remaining_amount
                ds.save()

                Transaction.objects.create(
                    user=student, amount=amount, transaction_type='EXP',
                    description=description or _('Daily Spending'), transaction_date=today
                )

            return Response({
                'message': _('Withdrawal successful'),
                'new_balance': float(wallet.balance),
                'today_spent': float(da.amount_spent),
                'today_remaining': float(da.remaining_amount)
            })

        except Exception as e:
            logger.error(f"Withdrawal Error: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def verify_parent_otp(self, request):
        """
        Verify parent OTP and process the extra withdrawal.
        """
        otp_code = request.data.get('otp_code')
        request_id = request.data.get('otp_request_id')
        
        if not otp_code or not request_id:
            return Response({'error': _('OTP code and Request ID are required')}, status=status.HTTP_400_BAD_REQUEST)

        try:
            pending_request = PendingSpendingRequest.objects.get(id=request_id, student=request.user)

            if pending_request.is_expired():
                pending_request.status = 'EXPIRED'
                pending_request.save()
                return Response({'error': _('This OTP has expired.')}, status=status.HTTP_400_BAD_REQUEST)

            if pending_request.status != 'PENDING':
                return Response({'error': _('This request has already been processed.')}, status=status.HTTP_400_BAD_REQUEST)

            if pending_request.otp_code != otp_code:
                return Response({'error': _('Invalid OTP code.')}, status=status.HTTP_400_BAD_REQUEST)

            student = request.user
            today = timezone.localdate()
            amount = pending_request.amount_requested
            wallet = self.get_object()

            if wallet.balance < amount:
                return Response({'error': _('Insufficient wallet balance')}, status=status.HTTP_400_BAD_REQUEST)

            # --- SUCCESS: PROCESS TRANSACTION NOW ---
            with transaction.atomic():
                # 1. Update Wallet
                wallet.balance -= amount
                # Stay locked because they are by definition over limit if they need OTP
                wallet.is_locked = True
                wallet.save()
                
                # 2. Update Daily Allowance Trackers
                da, created = DailyAllowance.objects.get_or_create(student=student, date=today)
                da.amount_spent += amount
                da.remaining_amount = Decimal('0.00') # Over limit = 0 remaining
                da.is_locked = True
                da.save()
                
                # Sync old tracker
                ds, created = DailySpending.objects.get_or_create(student=student, date=today, defaults={'daily_limit': 0})
                ds.amount_spent = da.amount_spent
                ds.remaining_amount = 0
                ds.is_locked = True
                ds.save()
                
                # 3. Mark request approved
                pending_request.status = 'APPROVED'
                pending_request.processed_at = timezone.now()
                pending_request.save()
                
                # 4. Create Transaction Record
                Transaction.objects.create(
                    user=student, amount=amount, transaction_type='EXP',
                    description=pending_request.request_message or _('Approved Extra Spending'),
                    transaction_date=today
                )

            return Response({
                'message': _('OTP Verified! ₹{0} withdrawal completed.').format(amount),
                'new_balance': float(wallet.balance),
                'today_spent': float(da.amount_spent)
            })

        except PendingSpendingRequest.DoesNotExist:
            return Response({'error': _('Spending request not found.')}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"OTP Verification Error: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def statement(self, request):
        """Get the student's own filtered transaction statement (Unified History)"""
        from .models import WalletTransaction, Transaction
        from individual_module.models import IndividualExpense
        from django.utils import timezone
        
        year = request.query_params.get('year')
        month = request.query_params.get('month')
        day = request.query_params.get('day')

        # 1. Get Wallet Transactions
        wallet_qs = WalletTransaction.objects.filter(wallet__user=request.user)
        if year: wallet_qs = wallet_qs.filter(created_at__year=year)
        if month: wallet_qs = wallet_qs.filter(created_at__month=month)
        if day: wallet_qs = wallet_qs.filter(created_at__day=day)

        # 2. Get Individual Expenses
        expense_qs = IndividualExpense.objects.filter(user=request.user)
        if year: expense_qs = expense_qs.filter(expense_date__year=year)
        if month: expense_qs = expense_qs.filter(expense_date__month=month)
        if day: expense_qs = expense_qs.filter(expense_date__day=day)

        # 3. Get General Transactions (Allowances, etc.)
        general_qs = Transaction.objects.filter(user=request.user)
        if year: general_qs = general_qs.filter(transaction_date__year=year)
        if month: general_qs = general_qs.filter(transaction_date__month=month)
        if day: general_qs = general_qs.filter(transaction_date__day=day)

        combined_data = []

        for tx in wallet_qs:
            combined_data.append({
                'id': f"w_{tx.id}",
                'amount': float(tx.amount),
                'transaction_type': tx.transaction_type,
                'description': tx.description,
                'date': tx.created_at
            })

        for exp in expense_qs:
            combined_data.append({
                'id': f"e_{exp.id}",
                'amount': float(exp.amount),
                'transaction_type': 'EXP',
                'description': f"[{exp.category}] {exp.description}",
                'date': timezone.make_aware(timezone.datetime.combine(exp.expense_date, timezone.datetime.min.time()))
            })

        for gen in general_qs:
            # Include EVERYTHING from general transactions for a complete report
            combined_data.append({
                'id': f"g_{gen.id}",
                'amount': float(gen.amount),
                'transaction_type': gen.transaction_type,
                'description': gen.description,
                'date': timezone.make_aware(timezone.datetime.combine(gen.transaction_date, timezone.datetime.min.time()))
            })

        combined_data.sort(key=lambda x: x['date'], reverse=True)

        return Response({
            'period': f"{month}/{year}",
            'count': len(combined_data),
            'results': combined_data
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

class GenerateStudentWalletOTPView(APIView):
    permission_classes = [permissions.IsAuthenticated, OTPGenerationPermission]
    def post(self, request):
        amount = request.data.get('amount')
        operation_type = request.data.get('operation_type', 'wallet_operation')
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
