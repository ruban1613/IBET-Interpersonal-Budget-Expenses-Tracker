from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from django.utils.translation import gettext_lazy as _
from core.throttling import OTPGenerationThrottle, OTPVerificationThrottle, WalletAccessThrottle, SensitiveOperationsThrottle
from .models import (
    Budget, Category, Transaction, User, UserPersona, Reminder, ChatMessage, 
    DailyLimit, OTPRequest, Wallet, ParentStudentRequest, ParentStudentLink, MonthlyAllowance, 
    DailySpending, SpendingLock, StudentNotification, MonthlySpendingSummary,
    DailyAllowance, CumulativeSpendingTracker, PendingSpendingRequest, AllowanceContribution
)
from django.db.models import Sum, Q
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
from .serializers import (
    BudgetSerializer, CategorySerializer, TransactionSerializer, UserSerializer, UserPersonaSerializer,
    ReminderSerializer, ChatMessageSerializer, DailyLimitSerializer, OTPRequestSerializer,
    ParentStudentRequestSerializer, MonthlyAllowanceSerializer, DailySpendingSerializer, 
    SpendingLockSerializer, StudentNotificationSerializer, MonthlySpendingSummarySerializer
)

import logging
logger = logging.getLogger(__name__)

class CategoryViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows categories to be viewed or edited.
    """
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Category.objects.filter(user=self.request.user).order_by('name')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class OTPRequestViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows OTP requests to be viewed or edited.
    """
    serializer_class = OTPRequestSerializer
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [OTPGenerationThrottle]

    def get_queryset(self):
        return OTPRequest.objects.filter(student=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(student=self.request.user)


class VerifyOTPView(APIView):
    """
    API endpoint for student to verify OTP and receive extra funds from parent.
    """
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [OTPVerificationThrottle, SensitiveOperationsThrottle]

    def post(self, request, *args, **kwargs):
        from parent_module.models import ParentOTPRequest
        from parent_module.serializers import VerifyOTPSerializer
        from .models import Wallet, WalletTransaction, Transaction

        serializer = VerifyOTPSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            otp_code = serializer.validated_data['otp_code']
            student_id = serializer.validated_data['student_id']

            # Find the OTP request
            try:
                otp_request = ParentOTPRequest.objects.get(
                    student_id=student_id,
                    otp_code=otp_code,
                    status='PENDING'
                )
            except ParentOTPRequest.DoesNotExist:
                return Response(
                    {'error': _('Invalid OTP or OTP request not found.')},
                    status=status.HTTP_400_BAD_REQUEST)

            # Check if OTP is expired
            if otp_request.is_expired():
                otp_request.mark_as_expired()
                return Response(
                    {'error': _('OTP has expired.')},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Verify that the requesting user is the correct student
            if otp_request.student_id != request.user.id:
                return Response(
                    {'error': _('You are not authorized to use this OTP.')},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Add funds to student's pocket money (special wallet)
            try:
                wallet = Wallet.objects.get(user=request.user)
            except Wallet.DoesNotExist:
                wallet = Wallet.objects.create(user=request.user)
            
            wallet.special_balance += otp_request.amount_requested
            wallet.save()

            # Mark OTP as used
            otp_request.mark_as_used()

            # Create general transaction record
            Transaction.objects.create(
                user=request.user,
                amount=otp_request.amount_requested,
                transaction_type='INC',
                description=_(f'Pocket Money from parent: {otp_request.reason}'),
                category=None,
                transaction_date=timezone.localdate()
            )

            # Create specific wallet transaction record
            WalletTransaction.objects.create(
                wallet=wallet,
                wallet_type=WalletTransaction.WalletType.SPECIAL,
                transaction_type=WalletTransaction.TransactionType.DEPOSIT,
                amount=otp_request.amount_requested,
                balance_after=wallet.special_balance,
                description=_(f'Pocket Money from parent: {otp_request.reason}')
            )

            return Response({
                'message': _('Successfully received pocket money from parent.'),
                'new_special_balance': wallet.special_balance,
                'reason': otp_request.reason
            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BudgetViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows budgets to be viewed or edited.
    It automatically filters budgets to only show the ones for the logged-in user.
    """
    serializer_class = BudgetSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Budget.objects.filter(user=self.request.user).order_by('-start_date')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['get'])
    def summary(self, request, pk=None):
        """
        Returns a summary of the budget, including total spent and remaining amount.
        """
        budget = self.get_object()
        total_spent = Transaction.objects.filter(
            user=request.user,
            category=budget.category,
            transaction_date__range=[budget.start_date, budget.end_date],
            transaction_type='EXP'
        ).aggregate(total=Sum('amount'))['total'] or 0.00

        remaining = budget.amount - total_spent

        return Response({
            'budget_amount': budget.amount,
            'total_spent': total_spent,
            'remaining': remaining,
            'category': budget.category.name,
        })


class TransactionViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows transactions to be viewed or edited.
    """
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['transaction_type', 'category']

    def get_queryset(self):
        return Transaction.objects.filter(user=self.request.user).order_by('-transaction_date')

    def perform_create(self, serializer):
        transaction = serializer.save(user=self.request.user)
        
        # Automatically deduct from wallet for expenses
        if transaction.transaction_type == 'EXP':
            try:
                wallet = Wallet.objects.get(user=self.request.user)
                wallet.balance -= transaction.amount
                wallet.last_transaction_at = timezone.now()
                wallet.save()
            except Wallet.DoesNotExist:
                # Create wallet if it doesn't exist (optional)
                Wallet.objects.create(
                    user=self.request.user,
                    balance=-transaction.amount,
                    last_transaction_at=timezone.now()
                )
        
        # Check spending limits for students
        if hasattr(self.request.user, 'persona') and self.request.user.persona == 'STUDENT':
            # Signals handle the spending tracker updates automatically
            today = timezone.localdate()
            
            # Get or create daily spending record
            daily_spending, created = DailySpending.objects.get_or_create(
                student=self.request.user,
                date=today,
                defaults={'daily_limit': 0, 'remaining_amount': 0}
            )
            
            # Get monthly allowance
            try:
                allowance = MonthlyAllowance.objects.get(student=self.request.user, is_active=True)
                daily_limit = allowance.get_daily_allowance()
                
                # Check 80% daily limit
                if daily_limit > 0:
                    spent_percent = (daily_spending.amount_spent / daily_limit) * 100
                    if spent_percent >= 80 and spent_percent < 100:
                        # Check if alert already sent today
                        today_alerts = StudentNotification.objects.filter(
                            student=self.request.user,
                            notification_type='DAILY_80%',
                            created_at__date=today
                        )
                        if not today_alerts.exists():
                            StudentNotification.objects.create(
                                student=self.request.user,
                                notification_type='DAILY_80%',
                                title=_('Daily Limit Warning'),
                                message=_(f'You have used {spent_percent:.0f}% of your daily allowance.')
                            )
                
                # Check if daily limit exceeded
                if daily_spending.remaining_amount < 0:
                    daily_spending.is_locked = True
                    daily_spending.lock_reason = 'Daily limit exceeded'
                    daily_spending.save()
                    
                    # Also lock the wallet object
                    try:
                        wallet = Wallet.objects.get(user=self.request.user)
                        wallet.is_locked = True
                        wallet.save()
                    except Wallet.DoesNotExist:
                        pass
                    
                    # Create spending lock
                    SpendingLock.objects.create(
                        student=self.request.user,
                        lock_type='DAILY_LIMIT',
                        amount_locked=abs(daily_spending.remaining_amount)
                    )
                    
                    # Create notification
                    StudentNotification.objects.create(
                        student=self.request.user,
                        notification_type='WALLET_LOCKED',
                        title=_('Daily Limit Exceeded'),
                        message=_('Your spending has been locked due to exceeding the daily limit. Contact your parent to unlock.')
                    )
                    
                    # Notify parent
                    try:
                        link = ParentStudentLink.objects.filter(
                            student=self.request.user
                        ).first()
                        if link:
                            from parent_module.models import ParentAlert
                            ParentAlert.objects.create(
                                parent=link.parent,
                                student=self.request.user,
                                alert_type='WALLET_LOCKED',
                                message=_(f'{self.request.user.username} has exceeded their daily limit and spending is now locked.')
                            )
                    except:
                        pass
                            
            except MonthlyAllowance.DoesNotExist:
                pass


class SelectPersonaView(APIView):
    """
    An endpoint for the logged-in user to select their persona.
    Accepts a PATCH request with the 'persona' field, e.g. {"persona": "STUDENT"}
    """
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, *args, **kwargs):
        user = request.user
        
        # New persona requested
        new_persona = request.data.get('persona')
        
        # If user already has a persona, only allow switching between student types
        if user.persona:
            allowed_student_personas = ['STUDENT', 'STUDENT_ACADEMIC']
            if user.persona in allowed_student_personas and new_persona in allowed_student_personas:
                # This is an allowed switch (Academic <-> Wallet)
                pass
            else:
                return Response(
                    {'error': _('Your core role is already set and cannot be changed.')},
                    status=status.HTTP_400_BAD_REQUEST)

        serializer = UserPersonaSerializer(data=request.data)
        if serializer.is_valid():
            user.persona = serializer.validated_data['persona']
            user.save(update_fields=['persona'])
            return Response(UserSerializer(user).data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ReminderViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows reminders to be viewed or edited.
    """
    serializer_class = ReminderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Reminder.objects.filter(user=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ChatMessageViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows chat messages to be viewed or edited.
    """
    serializer_class = ChatMessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ChatMessage.objects.filter(
            Q(sender=self.request.user) | Q(receiver=self.request.user)
        ).order_by('-timestamp')

    def perform_create(self, serializer):
        serializer.save(sender=self.request.user)


class DailyLimitViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows daily limits to be viewed or edited.
    """
    serializer_class = DailyLimitSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return DailyLimit.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ParentStudentRequestViewSet(viewsets.ModelViewSet):
    """
    API endpoint for parent-student connection requests.
    """
    serializer_class = ParentStudentRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'persona') and user.persona == 'PARENT':
            return ParentStudentRequest.objects.filter(parent=user).order_by('-created_at')
        return ParentStudentRequest.objects.filter(student=user).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(student=self.request.user)

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        req = self.get_object()
        if request.user != req.parent:
            return Response({'error': _('Not authorized.')}, status=status.HTTP_403_FORBIDDEN)
        
        req.status = 'APPROVED'
        req.processed_at = timezone.now()
        req.save()
        
        # Create the actual link
        ParentStudentLink.objects.get_or_create(parent=req.parent, student=req.student)
        
        StudentNotification.objects.create(
            student=req.student,
            notification_type='PARENT_APPROVAL',
            title=_('Connection Approved'),
            message=_(f'Your request to connect with {req.parent.username} has been approved.')
        )
        
        return Response({'status': 'approved'})

    @action(detail=True, methods=['post'])
    def unlink(self, request, pk=None):
        req = self.get_object()
        if request.user != req.parent and request.user != req.student:
            return Response({'error': _('Not authorized.')}, status=status.HTTP_403_FORBIDDEN)
        
        ParentStudentLink.objects.filter(parent=req.parent, student=req.student).delete()
        req.status = 'REJECTED'
        req.save()
        
        return Response({'status': 'unlinked'})


class MonthlyAllowanceViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing monthly allowance.
    """
    serializer_class = MonthlyAllowanceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'persona') and user.persona == 'PARENT':
            return MonthlyAllowance.objects.filter(parent=user).order_by('-created_at')
        return MonthlyAllowance.objects.filter(student=user)

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        from decimal import Decimal, InvalidOperation
        from datetime import timedelta
        
        student_id = request.data.get('student')
        parent = request.user
        today = timezone.localdate()
        
        try:
            student = User.objects.get(id=student_id)
        except User.DoesNotExist:
            return Response({'error': _('Student not found')}, status=status.HTTP_404_NOT_FOUND)

        try:
            monthly_amount_val = request.data.get('monthly_amount', '0') or '0'
            monthly_deposit = Decimal(str(monthly_amount_val))
        except (InvalidOperation, ValueError):
            return Response({'error': _('Invalid monthly amount format')}, status=status.HTTP_400_BAD_REQUEST)

        try:
            days_in_month = int(request.data.get('days_in_month', 30) or 30)
            if days_in_month <= 0: days_in_month = 30
        except (ValueError, TypeError):
            days_in_month = 30

        new_daily_limit_requested = request.data.get('daily_allowance')
        otp_code = request.data.get('otp_code')

        allowance, allowance_created = MonthlyAllowance.objects.get_or_create(
            student=student,
            defaults={
                'parent': parent,
                'monthly_amount': Decimal('0.00'),
                'days_in_month': days_in_month,
                'start_date': today,
                'is_active': True
            }
        )
        # Ensure correct parent is set even if record existed
        if not allowance_created:
            allowance.parent = parent
            allowance.save()
        
        current_daily_limit = allowance.get_daily_allowance()
        limit_is_changing = False
        target_daily_limit = current_daily_limit

        if new_daily_limit_requested is not None and str(new_daily_limit_requested).strip() != '':
            try:
                target_daily_limit = Decimal(str(new_daily_limit_requested))
                if abs(target_daily_limit - current_daily_limit) > 0.01:
                    limit_is_changing = True
            except (InvalidOperation, ValueError):
                return Response({'error': _('Invalid daily allowance format')}, status=status.HTTP_400_BAD_REQUEST)

        if limit_is_changing:
            if not otp_code:
                return Response({
                    'requires_otp': True,
                    'message': _('Changing the daily limit requires parent OTP.')
                }, status=status.HTTP_202_ACCEPTED)
            
            from parent_module.models import ParentOTPRequest
            pending_req = ParentOTPRequest.objects.filter(
                parent=parent, student=student, otp_code=otp_code, 
                operation_type='allowance_change', is_used=False
            ).first()
            
            if not pending_req:
                return Response({'error': _('Invalid or expired OTP code.')}, status=status.HTTP_400_BAD_REQUEST)
            
            pending_req.mark_as_used()

        parent_wallet, ign = Wallet.objects.select_for_update().get_or_create(user=parent, defaults={'balance': Decimal('0.00')})
        student_wallet, ign = Wallet.objects.select_for_update().get_or_create(user=student, defaults={'balance': Decimal('0.00')})

        if monthly_deposit > 0:
            if parent_wallet.balance < monthly_deposit:
                return Response({'error': _('Insufficient funds in parent wallet.')}, status=status.HTTP_400_BAD_REQUEST)
            
            parent_wallet.balance -= monthly_deposit
            student_wallet.balance += monthly_deposit
            parent_wallet.save()
            student_wallet.save()
            
            AllowanceContribution.objects.create(parent=parent, student=student, amount=monthly_deposit, day=today.day, month=today.month, year=today.year)
            Transaction.objects.create(user=student, amount=monthly_deposit, transaction_type='INC', description=_(f'Allowance from {parent.username}'), transaction_date=today)
            Transaction.objects.create(user=parent, amount=monthly_deposit, transaction_type='EXP', description=_(f'Allowance to {student.username}'), transaction_date=today)

        # 1. Update MonthlyAllowance
        if new_daily_limit_requested and Decimal(str(new_daily_limit_requested)) > 0:
            target_daily_limit = Decimal(str(new_daily_limit_requested))
            # Store the manual override
            allowance.daily_limit_override = target_daily_limit
            # If they provided a specific daily limit, the effective monthly_amount is just the deposit
            if monthly_deposit > 0:
                allowance.monthly_amount = monthly_deposit
        elif monthly_deposit > 0:
            allowance.monthly_amount = monthly_deposit
            # Clear manual override if only deposit is provided
            allowance.daily_limit_override = None
            target_daily_limit = allowance.get_daily_allowance()
        else:
            target_daily_limit = allowance.get_daily_allowance()
            
        allowance.days_in_month = days_in_month
        allowance.save()

        # Update Monthly spending summary
        ms, ms_created = MonthlySpendingSummary.objects.get_or_create(
            student=student, 
            month=today.month, 
            year=today.year,
            defaults={
                'total_allowance': allowance.monthly_amount,
                'remaining_amount': allowance.monthly_amount,
                'total_spent': Decimal('0.00'),
                'days_elapsed': 1
            }
        )
        ms.total_allowance = allowance.monthly_amount
        ms.remaining_amount = ms.total_allowance - ms.total_spent
        ms.save()

        # Update Cumulative tracker
        tracker, tracker_created = CumulativeSpendingTracker.objects.get_or_create(
            student=student,
            month=today.month,
            year=today.year,
            defaults={
                'total_allocated': allowance.monthly_amount,
                'total_available': allowance.monthly_amount,
                'total_spent': Decimal('0.00'),
                'days_available': 1
            }
        )
        tracker.total_allocated = allowance.monthly_amount
        tracker.total_available = tracker.total_allocated - tracker.total_spent
        tracker.save()

        ds, ds_created = DailySpending.objects.get_or_create(
            student=student, 
            date=today,
            defaults={
                'daily_limit': target_daily_limit,
                'remaining_amount': target_daily_limit,
                'amount_spent': Decimal('0.00')
            }
        )
        ds.daily_limit = target_daily_limit
        ds.remaining_amount = target_daily_limit - ds.amount_spent
        ds.is_locked = False
        ds.save()
        
        SpendingLock.objects.filter(student=student, is_active=True).update(is_active=False, unlocked_at=timezone.now())
        student_wallet.is_locked = False
        student_wallet.save()
        
        for i in range(days_in_month):
            d = today + timedelta(days=i)
            DailyAllowance.objects.update_or_create(
                student=student, date=d,
                defaults={
                    'daily_amount': target_daily_limit,
                    'remaining_amount': target_daily_limit if d > today else (target_daily_limit - ds.amount_spent),
                    'amount_spent': Decimal('0.00') if d > today else ds.amount_spent,
                    'is_available': True, 'is_locked': False
                }
            )

        return Response(MonthlyAllowanceSerializer(allowance).data)


class DailySpendingViewSet(viewsets.ModelViewSet):
    serializer_class = DailySpendingSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        return DailySpending.objects.filter(student=self.request.user).order_by('-date')


class SpendingLockViewSet(viewsets.ModelViewSet):
    serializer_class = SpendingLockSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'persona') and user.persona == 'PARENT':
            linked_students = ParentStudentLink.objects.filter(parent=user).values_list('student', flat=True)
            return SpendingLock.objects.filter(student__in=linked_students, is_active=True).order_by('-created_at')
        return SpendingLock.objects.filter(student=user, is_active=True).order_by('-created_at')

    @action(detail=True, methods=['post'])
    def request_unlock(self, request, pk=None):
        lock = self.get_object()
        from parent_module.models import ParentAlert
        link = ParentStudentLink.objects.filter(student=lock.student).first()
        if link:
            ParentAlert.objects.create(parent=link.parent, student=lock.student, alert_type='UNLOCK_REQUEST', message=_(f'{lock.student.username} requests spending unlock.'))
        return Response({'message': _('Unlock request sent to parent.')})

    @action(detail=True, methods=['post'])
    def generate_unlock_otp(self, request, pk=None):
        lock = self.get_object()
        if not hasattr(request.user, 'persona') or request.user.persona != 'PARENT':
            return Response({'error': _('Only parents can generate unlock OTP.')}, status=403)
        import random
        otp = str(random.randint(100000, 999999))
        lock.unlock_otp = otp
        lock.unlock_expires_at = timezone.now() + timedelta(minutes=10)
        lock.save()
        StudentNotification.objects.create(student=lock.student, notification_type='WALLET_UNLOCKED', title=_('Unlock OTP'), message=_(f'Parent sent OTP: {otp}'))
        return Response({'otp_code': otp})

    @action(detail=True, methods=['post'])
    def verify_unlock_otp(self, request, pk=None):
        lock = self.get_object()
        otp = request.data.get('otp_code')
        if lock.unlock_otp != otp or (lock.unlock_expires_at and timezone.now() > lock.unlock_expires_at):
            return Response({'error': _('Invalid or expired OTP.')}, status=400)
        lock.is_active = False
        lock.unlocked_at = timezone.now()
        lock.save()
        DailySpending.objects.filter(student=lock.student, date=timezone.now().date()).update(is_locked=False)
        return Response({'message': _('Unlocked successfully.')})


class StudentNotificationViewSet(viewsets.ModelViewSet):
    serializer_class = StudentNotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        return StudentNotification.objects.filter(student=self.request.user).order_by('-created_at')
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        return Response({'status': 'read'})


class MonthlySpendingSummaryViewSet(viewsets.ModelViewSet):
    serializer_class = MonthlySpendingSummarySerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        return MonthlySpendingSummary.objects.filter(student=self.request.user).order_by('-year', '-month')


class StudentDashboardView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            from decimal import Decimal
            from datetime import date
            from calendar import monthrange
            user = request.user
            if not hasattr(user, 'persona') or user.persona != 'STUDENT':
                return Response({'error': _('Only students can access this.')}, status=403)

            today = timezone.localdate()
            
            # Auto-unlock expired locks
            expired_locks = SpendingLock.objects.filter(student=user, is_active=True, lock_type='DAILY_LIMIT', created_at__date__lt=today)
            if expired_locks.exists():
                expired_locks.update(is_active=False, unlocked_at=timezone.now())
                DailySpending.objects.filter(student=user, date__lt=today, is_locked=True).update(is_locked=False)
                wallet_obj = Wallet.objects.filter(user=user).first()
                if wallet_obj:
                    wallet_obj.is_locked = False
                    wallet_obj.save()

            # --- CRITICAL FIX: Unlock wallet if no ACTIVE spending locks exist ---
            # This handles "stuck" locks where is_locked is True but no SpendingLock record exists
            has_active_locks = SpendingLock.objects.filter(student=user, is_active=True).exists()
            if not has_active_locks:
                wallet_obj = Wallet.objects.filter(user=user).first()
                if wallet_obj and wallet_obj.is_locked:
                    wallet_obj.is_locked = False
                    wallet_obj.save()
                    # Also ensure today's record isn't locked if no active lock exists
                    DailySpending.objects.filter(student=user, date=today, is_locked=True).update(is_locked=False)

            allowance = MonthlyAllowance.objects.filter(student=user, is_active=True).first()
            wallet, created = Wallet.objects.get_or_create(user=user, defaults={'balance': Decimal('0.00')})
            
            if allowance:
                ds, created = DailySpending.objects.get_or_create(
                    student=user, 
                    date=today, 
                    defaults={
                        'daily_limit': allowance.get_daily_allowance(), 
                        'remaining_amount': allowance.get_daily_allowance(),
                        'amount_spent': Decimal('0.00')
                    }
                )
                daily_limit = ds.daily_limit
                
                # Robustly handle Monthly Summary and Tracker
                try:
                    MonthlySpendingSummary.objects.get_or_create(
                        student=user, 
                        month=today.month, 
                        year=today.year, 
                        defaults={
                            'total_allowance': allowance.monthly_amount, 
                            'remaining_amount': allowance.monthly_amount,
                            'total_spent': Decimal('0.00'),
                            'days_elapsed': 1
                        }
                    )
                    CumulativeSpendingTracker.objects.get_or_create(
                        student=user, 
                        month=today.month, 
                        year=today.year, 
                        defaults={
                            'total_allocated': allowance.monthly_amount, 
                            'total_available': allowance.monthly_amount,
                            'total_spent': Decimal('0.00'),
                            'days_available': 30
                        }
                    )
                except Exception as e:
                    logger.error(f"Error creating dashboard trackers: {e}")
            else:
                daily_limit = Decimal('0.00')

            today_spent = Transaction.objects.filter(user=user, transaction_type='EXP', transaction_date=today).exclude(description__icontains='[Pocket Money]').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
            monthly_spent = Transaction.objects.filter(user=user, transaction_type='EXP', transaction_date__month=today.month, transaction_date__year=today.year).exclude(description__icontains='[Pocket Money]').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

            daily_breakdown = []
            month_allowances = DailyAllowance.objects.filter(student=user, date__month=today.month, date__year=today.year).order_by('date')
            for da in month_allowances:
                daily_breakdown.append({'date': da.date.strftime('%Y-%m-%d'), 'day': da.date.day, 'spent': float(da.amount_spent), 'limit': float(da.daily_amount)})

            active_locks_qs = SpendingLock.objects.filter(student=user, is_active=True)
            active_locks_count = active_locks_qs.count()
            active_lock_id = active_locks_qs.first().id if active_locks_count > 0 else None
            
            from datetime import datetime, time, timedelta
            tomorrow = datetime.combine(today + timedelta(days=1), time.min)
            now_dt = timezone.now()
            
            if timezone.is_naive(now_dt):
                seconds_until_reset = int((tomorrow - now_dt).total_seconds())
            else:
                # Make tomorrow aware to match now_dt
                tomorrow_aware = timezone.make_aware(tomorrow, timezone.get_current_timezone())
                seconds_until_reset = int((tomorrow_aware - now_dt).total_seconds())
            
            hours, remainder = divmod(seconds_until_reset, 3600)
            minutes, _ = divmod(remainder, 60)
            reset_time_str = f"{hours}h {minutes}m"

            return Response({
                'user_name': user.username,
                'user_persona': user.persona,
                'server_time': timezone.now().strftime('%I:%M %p'),
                'server_date': today.strftime('%d/%m/%Y'),
                'resets_in': reset_time_str,
                'wallet_balance': wallet.balance,
                'special_wallet_balance': wallet.special_balance,
                'monthly_allowance': float(allowance.monthly_amount) if allowance else 0,
                'daily_limit': float(daily_limit),
                'today_spent': float(today_spent),
                'today_remaining': float(max(Decimal('0.00'), daily_limit - today_spent)),
                'is_locked': active_locks_count > 0,
                'active_locks': active_locks_count,
                'active_lock_id': active_lock_id,
                'monthly_spent': float(monthly_spent),
                'monthly_remaining': float(max(Decimal('0.00'), (allowance.monthly_amount if allowance else 0) - monthly_spent)),
                'daily_breakdown': daily_breakdown,
                'has_allowance': allowance is not None
            })
        except Exception as e:
            import traceback
            return Response({'error': 'Dashboard Logic Error', 'details': str(e), 'traceback': traceback.format_exc()}, status=500)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    @action(detail=False, methods=['post'])
    def set_transaction_pin(self, request):
        if not hasattr(request.user, 'persona') or request.user.persona != 'PARENT':
            return Response({'error': _('Only parents can set PIN.')}, status=403)
        pin = request.data.get('transaction_pin')
        if not pin or len(str(pin)) < 4:
            return Response({'error': _('PIN must be 4 digits.')}, status=400)
        request.user.set_transaction_pin(pin)
        return Response({'message': _('PIN set successfully.')})
