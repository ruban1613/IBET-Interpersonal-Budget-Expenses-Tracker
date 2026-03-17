from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Sum, Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from datetime import datetime, timedelta
from decimal import Decimal
from .models import (
    IncomeSource, EmergencyFund, IndividualDashboard,
    ExpenseAlert, FinancialGoal, InvestmentSuggestion, IndividualExpense
)
from .serializers import (
    IncomeSourceSerializer, EmergencyFundSerializer, IndividualDashboardSerializer,
    ExpenseAlertSerializer, FinancialGoalSerializer, InvestmentSuggestionSerializer,
    IndividualOverviewSerializer, WalletSerializer, TransactionSerializer
)
from .models_wallet import IndividualWallet, IndividualWalletTransaction


class IncomeSourceViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows income sources to be viewed or edited.
    """
    serializer_class = IncomeSourceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return IncomeSource.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class EmergencyFundViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows emergency funds to be viewed or edited.
    """
    serializer_class = EmergencyFundSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return EmergencyFund.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class IndividualDashboardViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows individual dashboards to be viewed or edited.
    """
    serializer_class = IndividualDashboardSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return IndividualDashboard.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ExpenseAlertViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows expense alerts to be viewed or edited.
    """
    serializer_class = ExpenseAlertSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ExpenseAlert.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['patch'])
    def mark_as_read(self, request, pk=None):
        """Mark an alert as read."""
        alert = self.get_object()
        alert.mark_as_read()
        return Response({'status': _('Alert marked as read')})

    @action(detail=False, methods=['patch'])
    def mark_all_read(self, request):
        """Mark all alerts as read."""
        alerts = self.get_queryset().filter(is_read=False)
        alerts.update(is_read=True, read_at=timezone.now())
        return Response({'status': _(f'{alerts.count()} alerts marked as read')})


class FinancialGoalViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows financial goals to be viewed or edited.
    """
    serializer_class = FinancialGoalSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return FinancialGoal.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['patch'])
    def update_progress(self, request, pk=None):
        """Update the current amount for a financial goal."""
        goal = self.get_object()
        current_amount = request.data.get('current_amount')

        if current_amount is not None:
            goal.current_amount = current_amount
            goal.save()
            return Response({'status': _('Goal progress updated')})

        return Response({'error': _('current_amount is required')}, status=status.HTTP_400_BAD_REQUEST)


class InvestmentSuggestionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that provides investment suggestions for individual users.
    """
    serializer_class = InvestmentSuggestionSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = InvestmentSuggestion.objects.filter(is_active=True)

    @action(detail=False, methods=['get'])
    def seed_data(self, request):
        """Seed some initial investment suggestion data"""
        suggestions = [
            {
                'title': 'Gold Investment Plan',
                'plan_type': 'GOLD',
                'description': 'Invest in digital gold or physical gold for long term stability.',
                'benefits': 'Hedge against inflation, high liquidity, diversification.',
                'risk_level': 'Low to Medium',
                'minimum_investment': 500.00,
                'current_scenario_analysis': 'Gold is currently performing well due to market volatility. It is a safe haven for investors.'
            },
            {
                'title': 'Term Life Insurance',
                'plan_type': 'INSURANCE',
                'description': 'Secure your family\'s future with a term life insurance policy.',
                'benefits': 'Family security, tax benefits, peace of mind.',
                'risk_level': 'Very Low',
                'minimum_investment': 1000.00,
                'current_scenario_analysis': 'With rising health costs, having a comprehensive insurance plan is crucial for financial planning.'
            },
            {
                'title': 'High Yield Fixed Deposit',
                'plan_type': 'FD',
                'description': 'Invest in bank FDs for guaranteed returns.',
                'benefits': 'Guaranteed returns, flexible tenure, safety of capital.',
                'risk_level': 'Very Low',
                'minimum_investment': 5000.00,
                'current_scenario_analysis': 'Interest rates are currently stable, making FDs a good option for conservative investors.'
            },
            {
                'title': 'Systematic Recurring Deposit',
                'plan_type': 'RD',
                'description': 'Save a fixed amount every month with RD.',
                'benefits': 'Disciplined saving, guaranteed returns, regular investment habit.',
                'risk_level': 'Very Low',
                'minimum_investment': 500.00,
                'current_scenario_analysis': 'RDs are ideal for building a corpus over time from monthly savings.'
            }
        ]

        created_count = 0
        for sugg in suggestions:
            obj, created = InvestmentSuggestion.objects.get_or_create(
                title=sugg['title'],
                defaults=sugg
            )
            if created:
                created_count += 1

        return Response({'status': _(f'Successfully seeded {created_count} investment suggestions.')})


class IndividualOverviewView(APIView):
    """
    API endpoint for individual financial overview.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user

        # Get wallet balance
        try:
            wallet = IndividualWallet.objects.get(user=user)
            wallet_balance = wallet.balance
        except IndividualWallet.DoesNotExist:
            wallet_balance = 0.00

        # Calculate monthly income
        current_month = timezone.now().replace(day=1)
        next_month = (current_month + timedelta(days=32)).replace(day=1)

        monthly_income = IncomeSource.objects.filter(
            user=user,
            is_active=True
        ).aggregate(total=Sum('amount'))['total'] or 0.00

        # Calculate monthly expenses
        monthly_expenses = IndividualExpense.objects.filter(
            user=user,
            expense_date__gte=current_month,
            expense_date__lt=next_month
        ).aggregate(total=Sum('amount'))['total'] or 0.00

        # Emergency fund progress
        try:
            emergency_fund = EmergencyFund.objects.get(user=user)
            emergency_fund_progress = emergency_fund.progress_percentage
        except EmergencyFund.DoesNotExist:
            emergency_fund_progress = 0.00

        # Active goals count
        active_goals_count = FinancialGoal.objects.filter(
            user=user,
            status='ACTIVE'
        ).count()

        # Unread alerts count
        unread_alerts_count = ExpenseAlert.objects.filter(
            user=user,
            is_read=False
        ).count()

        # Recent transactions (last 10)
        recent_expenses = IndividualExpense.objects.filter(
            user=user
        ).order_by('-expense_date')[:10]

        # Create the response data
        response_data = {
            'wallet_balance': wallet_balance,
            'monthly_income': monthly_income,
            'monthly_expenses': monthly_expenses,
            'emergency_fund_progress': emergency_fund_progress,
            'active_goals_count': active_goals_count,
            'unread_alerts_count': unread_alerts_count,
            'recent_transactions': TransactionSerializer(recent_expenses, many=True).data
        }

        return Response(response_data)


class WalletManagementView(APIView):
    """
    API endpoint for wallet management operations.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        """Get wallet information."""
        try:
            wallet = IndividualWallet.objects.get(request.user)
            return Response({
                'id': wallet.id,
                'balance': wallet.balance,
                'created_at': wallet.created_at,
                'updated_at': wallet.updated_at
            })
        except IndividualWallet.DoesNotExist:
            return Response(
                {'error': _('Wallet not found')},
                status=status.HTTP_404_NOT_FOUND
            )

    def post(self, request, *args, **kwargs):
        """Add money to wallet."""
        amount = request.data.get('amount')
        description = request.data.get('description', 'Wallet deposit')

        if not amount or Decimal(amount) <= 0:
            return Response(
                {'error': _('Valid amount is required')},
                status=status.HTTP_400_BAD_REQUEST
            )

        wallet, created = IndividualWallet.objects.get_or_create(
            user=request.user,
            defaults={'balance': Decimal('0.00')}
        )

        wallet.balance += Decimal(amount)
        wallet.save()

        # Create transaction record
        IndividualWalletTransaction.objects.create(
            wallet=wallet,
            amount=Decimal(amount),
            transaction_type='DEPOSIT',
            description=description
        )

        return Response({
            'message': _(f'Successfully added {amount} to wallet'),
            'new_balance': wallet.balance
        }, status=status.HTTP_201_CREATED)


class ExpenseTrackingView(APIView):
    """
    API endpoint for expense tracking and budget monitoring.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        """Get expense summary for current month."""
        user = request.user
        current_month = timezone.now().replace(day=1)
        next_month = (current_month + timedelta(days=32)).replace(day=1)

        # Get monthly expenses by category
        expenses_by_category = IndividualExpense.objects.filter(
            user=user,
            expense_date__gte=current_month,
            expense_date__lt=next_month
        ).values('category').annotate(
            total=Sum('amount')
        ).order_by('-total')

        # Get total monthly expenses
        total_expenses = IndividualExpense.objects.filter(
            user=user,
            expense_date__gte=current_month,
            expense_date__lt=next_month
        ).aggregate(total=Sum('amount'))['total'] or 0.00

        # Get monthly income
        monthly_income = IncomeSource.objects.filter(
            user=user,
            is_active=True
        ).aggregate(total=Sum('amount'))['total'] or 0.00

        # Calculate remaining budget
        remaining_budget = monthly_income - Decimal(str(total_expenses))

        return Response({
            'current_month': current_month.strftime('%Y-%m'),
            'monthly_income': monthly_income,
            'total_expenses': total_expenses,
            'remaining_budget': remaining_budget,
            'expenses_by_category': list(expenses_by_category)
        })

    def post(self, request, *args, **kwargs):
        """Add a new expense."""
        amount_val = request.data.get('amount')
        description = request.data.get('description', '')
        category = request.data.get('category')

        if not amount_val or not category:
            return Response(
                {'error': _('amount and category are required')},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            amount = Decimal(str(amount_val))
            expense, alerts = IndividualExpense.record_expense_and_check_alerts(
                request.user, amount, category, description
            )

            # Get the updated wallet balance for the response
            wallet = IndividualWallet.objects.get(user=request.user)

            return Response({
                'message': _(f'Expense of {amount} recorded successfully'),
                'new_balance': wallet.balance,
                'alerts_count': len(alerts)
            }, status=status.HTTP_201_CREATED)

        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
