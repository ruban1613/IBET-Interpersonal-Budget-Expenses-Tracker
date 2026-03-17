"""
Secure wallet views for Individual Module.
Provides secure wallet operations with OTP protection and monitoring.
"""
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils.translation import gettext_lazy as _
from core.throttling import OTPGenerationThrottle, OTPVerificationThrottle, WalletAccessThrottle, SensitiveOperationsThrottle
from core.security import OTPSecurityService, SecurityUtils
from core.security_monitoring_fixed import SecurityEventManager, AuditService
from core.permissions import OTPGenerationPermission, OTPVerificationPermission
from .models_wallet import IndividualWallet, IndividualWalletTransaction, IndividualWalletOTPRequest
from .models import IndividualExpense, InvestmentSuggestion
from .serializers_wallet import (
    IndividualWalletSerializer, IndividualWalletTransactionSerializer,
    IndividualWalletTransferSerializer, IndividualWalletSavingsWithdrawalSerializer,
    IndividualWalletBudgetSerializer, IndividualWalletSavingsGoalSerializer
)
from django.db.models import Sum
from django.utils import timezone
from decimal import Decimal


class IndividualWalletViewSet(viewsets.ModelViewSet):
    """
    Secure API endpoint for individual wallet management.
    """
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [WalletAccessThrottle]
    serializer_class = IndividualWalletSerializer

    def get_queryset(self):
        return IndividualWallet.objects.filter(user=self.request.user)

    def get_object(self):
        try:
            return IndividualWallet.objects.get(user=self.request.user)
        except IndividualWallet.DoesNotExist:
            raise IndividualWallet.DoesNotExist("Individual wallet not found")

    @action(detail=False, methods=['get'])
    def statement(self, request):
        """Get filtered transaction statement"""
        from django.utils.timezone import localdate
        user = request.user
        year = request.query_params.get('year')
        month = request.query_params.get('month')
        day = request.query_params.get('day')
        
        # Default to current month if no filters provided
        today = localdate()
        if not year: year = today.year
        if not month: month = today.month

        queryset = IndividualWalletTransaction.objects.filter(
            wallet__user=user
        )

        if year:
            queryset = queryset.filter(created_at__year=year)
        if month:
            queryset = queryset.filter(created_at__month=month)
        if day:
            queryset = queryset.filter(created_at__day=day)

        transactions = queryset.order_by('-created_at')
        
        serializer = IndividualWalletTransactionSerializer(transactions, many=True)
        return Response({
            'period': f"{month}/{year}",
            'count': transactions.count(),
            'transactions': serializer.data
        })

    def list(self, request, *args, **kwargs):
        """Override list to return single wallet object instead of array"""
        wallet, created = IndividualWallet.objects.get_or_create(
            user=request.user,
            defaults={
                'balance': Decimal('0.00'),
                'total_deposits': Decimal('0.00'),
                'monthly_budget': Decimal('0.00'),
                'savings_goal': Decimal('0.00'),
                'current_savings': Decimal('0.00'),
                'alert_threshold': Decimal('0.00')
            }
        )
        serializer = self.get_serializer(wallet)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def balance(self, request):
        """Get wallet balance securely"""
        wallet, created = IndividualWallet.objects.get_or_create(
            user=request.user,
            defaults={
                'balance': Decimal('0.00'),
                'total_deposits': Decimal('0.00'),
                'monthly_budget': Decimal('0.00'),
                'savings_goal': Decimal('0.00'),
                'current_savings': Decimal('0.00'),
                'alert_threshold': Decimal('0.00')
            }
        )

        SecurityEventManager.log_event(
            SecurityEventManager.EVENT_TYPES['WALLET_ACCESS'],
            request.user.id,
            {'action': 'balance_check'}
        )

        return Response({
            'balance': wallet.balance,
            'total_deposits': wallet.total_deposits,
            'monthly_budget': wallet.monthly_budget,
            'savings_goal': wallet.savings_goal,
            'current_savings': wallet.current_savings,
            'available_balance': wallet.available_balance,
            'is_locked': wallet.is_locked,
            'last_transaction_at': wallet.last_transaction_at
        })

    @action(detail=False, methods=['get'])
    def welcome(self, request):
        """Welcome endpoint for individual wallet"""
        SecurityEventManager.log_event(
            SecurityEventManager.EVENT_TYPES['WALLET_ACCESS'],
            request.user.id,
            {'action': 'welcome', 'method': request.method, 'path': request.path}
        )

        return Response({
            'message': _('Welcome to the Individual Wallet API Service!')
        })

    @action(detail=False, methods=['post'])
    def deposit(self, request):
        """Secure deposit to wallet"""
        try:
            wallet, created = IndividualWallet.objects.get_or_create(
                user=request.user,
                defaults={
                    'balance': Decimal('0.00'),
                    'total_deposits': Decimal('0.00'),
                    'monthly_budget': Decimal('0.00'),
                    'savings_goal': Decimal('0.00'),
                    'current_savings': Decimal('0.00'),
                    'alert_threshold': Decimal('0.00')
                }
            )

            amount_raw = request.data.get('amount', 0)
            try:
                amount = Decimal(amount_raw)
            except Exception:
                return Response({'error': _('Invalid amount format')}, status=status.HTTP_400_BAD_REQUEST)
            description = request.data.get('description', _('Deposit'))

            if amount <= 0:
                return Response({'error': _('Invalid amount')}, status=status.HTTP_400_BAD_REQUEST)

            # Check for suspicious activity
            if SecurityEventManager.detect_suspicious_activity(
                request.user.id, 'wallet_deposit', threshold=5, time_window_minutes=30
            ):
                return Response(
                    {'error': _('Suspicious activity detected')},
                    status=status.HTTP_429_TOO_MANY_REQUESTS
                )

            new_balance = wallet.deposit(amount, description)

            # Audit the operation
            AuditService.audit_wallet_operation(
                request.user.id,
                'deposit',
                amount,
                {'description': description}
            )

            SecurityEventManager.log_event(
                SecurityEventManager.EVENT_TYPES['FUND_TRANSFER'],
                request.user.id,
                {'amount': amount, 'new_balance': new_balance, 'transfer_type': 'credit'}
            )

            return Response({
                'message': _('Deposit successful'),
                'new_balance': new_balance
            })

        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def withdraw(self, request):
        """Secure withdrawal from wallet"""
        try:
            wallet, created = IndividualWallet.objects.get_or_create(
                user=request.user,
                defaults={
                    'balance': Decimal('0.00'),
                    'total_deposits': Decimal('0.00'),
                    'monthly_budget': Decimal('0.00'),
                    'savings_goal': Decimal('0.00'),
                    'current_savings': Decimal('0.00'),
                    'alert_threshold': Decimal('0.00')
                }
            )

            amount_raw = request.data.get('amount', 0)
            try:
                amount = Decimal(amount_raw)
            except Exception:
                return Response({'error': _('Invalid amount format')}, status=status.HTTP_400_BAD_REQUEST)
            description = request.data.get('description', _('Withdrawal'))

            if amount <= 0:
                return Response({'error': _('Invalid amount')}, status=status.HTTP_400_BAD_REQUEST)

            # Check for suspicious activity
            if SecurityEventManager.detect_suspicious_activity(
                request.user.id, 'wallet_withdrawal', threshold=3, time_window_minutes=15
            ):
                return Response(
                    {'error': _('Suspicious activity detected')},
                    status=status.HTTP_429_TOO_MANY_REQUESTS
                )

            new_balance = wallet.withdraw(amount, description)

            # Audit the operation
            AuditService.audit_wallet_operation(
                request.user.id,
                'withdrawal',
                amount,
                {'description': description}
            )

            SecurityEventManager.log_event(
                SecurityEventManager.EVENT_TYPES['FUND_TRANSFER'],
                request.user.id,
                {'amount': amount, 'new_balance': new_balance, 'transfer_type': 'debit'}
            )

            return Response({
                'message': _('Withdrawal successful'),
                'new_balance': new_balance
            })

        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def transfer_to_goal(self, request):
        """Transfer money to savings goal - requires OTP"""
        try:
            wallet, created = IndividualWallet.objects.get_or_create(
                user=request.user,
                defaults={
                    'balance': Decimal('0.00'),
                    'total_deposits': Decimal('0.00'),
                    'monthly_budget': Decimal('0.00'),
                    'savings_goal': Decimal('0.00'),
                    'current_savings': Decimal('0.00'),
                    'alert_threshold': Decimal('0.00')
                }
            )

            serializer = IndividualWalletTransferSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            amount = serializer.validated_data['amount']
            goal_name = serializer.validated_data['goal_name']
            
            # OTP Check
            otp_code = request.data.get('otp_code')
            otp_request_id = request.data.get('otp_request_id')

            if not otp_code or not otp_request_id:
                return Response({'error': _('OTP code and request ID are required for transfer')}, status=status.HTTP_400_BAD_REQUEST)

            try:
                otp_request = IndividualWalletOTPRequest.objects.get(
                    id=otp_request_id,
                    user=request.user,
                    is_used=False
                )
                
                # Use security service for validation
                is_valid, error_message = OTPSecurityService.validate_otp(
                    request.user.id,
                    otp_code,
                    otp_request.cache_key,
                    'individual_wallet_operation'
                )

                if not is_valid:
                    return Response({'error': error_message}, status=status.HTTP_400_BAD_REQUEST)

                otp_request.mark_as_used()
            except IndividualWalletOTPRequest.DoesNotExist:
                return Response({'error': _('Invalid OTP request')}, status=status.HTTP_400_BAD_REQUEST)

            # Check for suspicious activity
            if SecurityEventManager.detect_suspicious_activity(
                request.user.id, 'individual_goal_transfer', threshold=3, time_window_minutes=15
            ):
                return Response(
                    {'error': _('Suspicious activity detected')},
                    status=status.HTTP_429_TOO_MANY_REQUESTS
                )

            new_balance = wallet.transfer_to_goal(amount, goal_name)

            # Audit and log
            AuditService.audit_wallet_operation(request.user.id, 'savings_transfer', amount, {'goal_name': goal_name})
            SecurityEventManager.log_event(SecurityEventManager.EVENT_TYPES['FUND_TRANSFER'], request.user.id, {'amount': amount, 'goal_name': goal_name, 'new_balance': new_balance})

            return Response({
                'message': _('Transfer to savings successful'),
                'new_balance': new_balance,
                'current_savings': wallet.current_savings
            })

        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def withdraw_from_savings(self, request):
        """Withdraw money from savings wallet - requires OTP"""
        try:
            wallet, created = IndividualWallet.objects.get_or_create(
                user=request.user,
                defaults={
                    'balance': Decimal('0.00'),
                    'total_deposits': Decimal('0.00'),
                    'monthly_budget': Decimal('0.00'),
                    'savings_goal': Decimal('0.00'),
                    'current_savings': Decimal('0.00'),
                    'alert_threshold': Decimal('0.00')
                }
            )

            serializer = IndividualWalletSavingsWithdrawalSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            amount = serializer.validated_data['amount']
            description = serializer.validated_data.get('description', _('Savings Withdrawal'))
            
            # OTP Check
            otp_code = request.data.get('otp_code')
            otp_request_id = request.data.get('otp_request_id')

            if not otp_code or not otp_request_id:
                return Response({'error': _('OTP code and request ID are required for savings withdrawal')}, status=status.HTTP_400_BAD_REQUEST)

            try:
                otp_request = IndividualWalletOTPRequest.objects.get(
                    id=otp_request_id,
                    user=request.user,
                    is_used=False
                )
                
                is_valid, error_message = OTPSecurityService.validate_otp(
                    request.user.id,
                    otp_code,
                    otp_request.cache_key,
                    'individual_wallet_operation'
                )

                if not is_valid:
                    return Response({'error': error_message}, status=status.HTTP_400_BAD_REQUEST)

                otp_request.mark_as_used()
            except IndividualWalletOTPRequest.DoesNotExist:
                return Response({'error': _('Invalid OTP request')}, status=status.HTTP_400_BAD_REQUEST)

            new_savings_balance = wallet.withdraw_from_savings(amount, description)

            # Audit and log
            AuditService.audit_wallet_operation(request.user.id, 'savings_withdrawal', amount, {'description': description})
            SecurityEventManager.log_event(SecurityEventManager.EVENT_TYPES['FUND_TRANSFER'], request.user.id, {'amount': amount, 'new_savings_balance': new_savings_balance})

            return Response({
                'message': _('Withdrawal from savings successful'),
                'new_balance': wallet.balance,
                'current_savings': new_savings_balance
            })

        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def today_spending(self, request):
        """Get today's total spending and items"""
        from django.utils.timezone import localdate
        today = localdate()
        expenses = IndividualExpense.objects.filter(user=request.user, expense_date=today)
        total_spent = expenses.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        return Response({
            'date': today,
            'total_spent': total_spent,
            'expenses': [
                {'id': exp.id, 'amount': exp.amount, 'category': exp.category, 'description': exp.description}
                for exp in expenses
            ]
        })

    @action(detail=False, methods=['get'])
    def monthly_summary(self, request):
        """Get monthly spending summary by category for dynamic charts"""
        today = timezone.now()
        start_of_month = today.replace(day=1)
        
        expenses = IndividualExpense.objects.filter(
            user=request.user, 
            expense_date__gte=start_of_month
        ).order_by('expense_date', 'created_at')
        
        category_summary = expenses.values('category').annotate(
            total=Sum('amount')
        ).order_by('-total')
        
        total_monthly_spent = expenses.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        # Individual expenses for granular pie chart visualization
        individual_expenses = []
        for exp in expenses:
            individual_expenses.append({
                'id': exp.id,
                'category': exp.category,
                'amount': float(exp.amount),
                'description': exp.description or exp.category,
                'date': exp.expense_date.strftime('%d %b')
            })

        # Investment suggestions if saving is good
        wallet = self.get_object()
        
        suggestions = []
        if wallet.current_savings > 1000:
            suggestions = InvestmentSuggestion.objects.filter(is_active=True)
        
        import calendar
        month_name = calendar.month_name[today.month]
        
        return Response({
            'month': f"{month_name} {today.year}",
            'total_spent': total_monthly_spent,
            'category_breakdown': list(category_summary),
            'individual_expenses': individual_expenses,
            'investment_suggestions': [
                {
                    'id': s.id,
                    'title': s.title,
                    'plan_type': s.plan_type,
                    'description': s.description,
                    'benefits': s.benefits,
                    'minimum_investment': s.minimum_investment,
                    'current_scenario_analysis': s.current_scenario_analysis
                } for s in suggestions
            ]
        })

    @action(detail=False, methods=['get'])
    def daily_spending_summary(self, request):
        """Get granular individual transactions for the current month for charts"""
        from django.utils.timezone import localdate
        today = localdate()
        year = today.year
        month = today.month
        
        # Get all individual transactions up to today
        expenses = IndividualExpense.objects.filter(
            user=request.user,
            expense_date__year=year,
            expense_date__month=month,
            expense_date__day__lte=today.day
        ).order_by('expense_date', 'created_at')
        
        result = []
        for i, exp in enumerate(expenses):
            result.append({
                'index': i + 1,
                'day': exp.expense_date.day,
                'date': exp.expense_date.strftime('%d %b'),
                'amount': float(exp.amount),
                'category': exp.category,
                'description': exp.description or exp.category
            })
            
        return Response(result)

    @action(detail=False, methods=['get'])
    def yearly_spending_summary(self, request):
        """Get monthly spending for the last 12 months for charts"""
        from django.utils.timezone import localdate
        today = localdate()
        
        result = []
        import calendar
        
        # Calculate last 12 months manually
        curr_month = today.month
        curr_year = today.year
        
        months_to_fetch = []
        for i in range(12):
            months_to_fetch.append((curr_year, curr_month))
            curr_month -= 1
            if curr_month == 0:
                curr_month = 12
                curr_year -= 1
        
        # Reverse to get chronological order
        months_to_fetch.reverse()
        
        for year, month in months_to_fetch:
            total = IndividualExpense.objects.filter(
                user=request.user,
                expense_date__year=year,
                expense_date__month=month
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
            
            result.append({
                'month': calendar.month_name[month][:3],
                'full_month': calendar.month_name[month],
                'year': year,
                'amount': float(total)
            })
            
        return Response(result)

    @action(detail=False, methods=['post'])
    def set_budget(self, request):
        """Set monthly budget for individual wallet"""
        wallet, created = IndividualWallet.objects.get_or_create(
            user=request.user,
            defaults={
                'balance': Decimal('0.00'),
                'total_deposits': Decimal('0.00'),
                'monthly_budget': Decimal('0.00'),
                'savings_goal': Decimal('0.00'),
                'current_savings': Decimal('0.00')
            }
        )

        serializer = IndividualWalletBudgetSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        wallet.monthly_budget = serializer.validated_data['monthly_budget']
        wallet.save()

        AuditService.audit_wallet_operation(request.user.id, 'set_budget', wallet.monthly_budget)
        
        return Response({
            'message': _('Monthly budget updated successfully'),
            'monthly_budget': wallet.monthly_budget
        })

    @action(detail=False, methods=['post'])
    def set_savings_goal(self, request):
        """Set savings goal for individual wallet"""
        wallet, created = IndividualWallet.objects.get_or_create(
            user=request.user,
            defaults={
                'balance': Decimal('0.00'),
                'total_deposits': Decimal('0.00'),
                'monthly_budget': Decimal('0.00'),
                'savings_goal': Decimal('0.00'),
                'current_savings': Decimal('0.00')
            }
        )

        serializer = IndividualWalletSavingsGoalSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        wallet.savings_goal = serializer.validated_data['savings_goal']
        wallet.save()

        AuditService.audit_wallet_operation(request.user.id, 'set_savings_goal', wallet.savings_goal)

        return Response({
            'message': _('Savings goal updated successfully'),
            'savings_goal': wallet.savings_goal
        })


class IndividualWalletTransactionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    View transaction history for individual wallets.
    """
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [WalletAccessThrottle]
    serializer_class = IndividualWalletTransactionSerializer

    def get_queryset(self):
        return IndividualWalletTransaction.objects.filter(wallet__user=self.request.user)


class GenerateIndividualWalletOTPView(APIView):
    """
    Secure API endpoint for generating OTP for individual wallet operations.
    """
    permission_classes = [permissions.IsAuthenticated, OTPGenerationPermission]
    throttle_classes = [OTPGenerationThrottle, SensitiveOperationsThrottle]

    def post(self, request, *args, **kwargs):
        # Make operation_type optional with default value for flexibility
        operation_type = request.data.get('operation_type', 'wallet_operation')
        amount = request.data.get('amount')
        description = request.data.get('description', '')

        # Generate secure OTP
        otp_request_data = OTPSecurityService.create_otp_request(
            request.user.id,
            'individual_wallet_operation'
        )

        # Set expiration time (10 minutes from now)
        expires_at = timezone.now() + timezone.timedelta(minutes=10)

        # Create OTP request
        otp_request = IndividualWalletOTPRequest.objects.create(
            user=request.user,
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
                'description': description
            }
        )

        SecurityEventManager.log_event(
            SecurityEventManager.EVENT_TYPES['OTP_GENERATED'],
            request.user.id,
            {
                'operation_type': operation_type,
                'amount': amount,
                'expires_at': expires_at.isoformat()
            }
        )

        response_data = {
            'message': _('OTP generated successfully for wallet operation'),
            'otp_request_id': otp_request.id,
            'operation_type': operation_type,
            'expires_at': expires_at,
            'note': _('The OTP has been securely generated and must be shared with the user directly.')
        }

        # Include OTP code in debug mode for testing
        from django.conf import settings
        if settings.DEBUG and 'otp_code' in otp_request_data:
            response_data['otp_code'] = otp_request_data['otp_code']

        return Response(response_data, status=status.HTTP_201_CREATED)


class VerifyIndividualWalletOTPView(APIView):
    """
    Secure API endpoint for verifying OTP for individual wallet operations.
    """
    permission_classes = [permissions.IsAuthenticated, OTPVerificationPermission]
    throttle_classes = [OTPVerificationThrottle, SensitiveOperationsThrottle]

    def post(self, request, *args, **kwargs):
        otp_code = request.data.get('otp_code')
        otp_request_id = request.data.get('otp_request_id')

        if not otp_code or not otp_request_id:
            return Response({'error': _('OTP code and request ID are required')}, status=status.HTTP_400_BAD_REQUEST)

        try:
            otp_request = IndividualWalletOTPRequest.objects.get(
                id=otp_request_id,
                user=request.user,
                is_used=False
            )

            if otp_request.is_expired():
                otp_request.delete()
                SecurityEventManager.log_event(
                    SecurityEventManager.EVENT_TYPES['OTP_FAILED'],
                    request.user.id,
                    {'reason': 'OTP expired'}
                )
                return Response({'error': _('OTP has expired')}, status=status.HTTP_400_BAD_REQUEST)

            # Validate OTP using security service
            cache_key = otp_request.cache_key
            is_valid, error_message = OTPSecurityService.validate_otp(
                request.user.id,
                otp_code,
                cache_key,
                'individual_wallet_operation'
            )

            if not is_valid:
                SecurityEventManager.log_event(
                    SecurityEventManager.EVENT_TYPES['OTP_FAILED'],
                    request.user.id,
                    {'reason': error_message}
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
                    'amount': otp_request.amount
                }
            )

            SecurityEventManager.log_event(
                SecurityEventManager.EVENT_TYPES['OTP_VERIFIED'],
                request.user.id,
                {
                    'operation_type': otp_request.operation_type,
                    'amount': otp_request.amount,
                    'success': True
                }
            )

            return Response({
                'message': _('OTP verified successfully'),
                'operation_type': otp_request.operation_type,
                'amount': otp_request.amount,
                'description': otp_request.description
            })

        except IndividualWalletOTPRequest.DoesNotExist:
            SecurityEventManager.log_event(
                SecurityEventManager.EVENT_TYPES['OTP_FAILED'],
                request.user.id,
                {'reason': 'Invalid OTP request'}
            )
            return Response({'error': _('Invalid OTP request')}, status=status.HTTP_400_BAD_REQUEST)
