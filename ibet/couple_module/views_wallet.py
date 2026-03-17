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
from .serializers_wallet import CoupleWalletSerializer, CoupleWalletTransactionSerializer
from django.db.models import Sum, Q, Count
from django.utils import timezone
from decimal import Decimal, InvalidOperation


def validate_and_convert_amount(amount_data):
    """
    Validate and convert amount data to Decimal.
    Returns (amount, error_message) tuple.
    """
    if amount_data is None:
        return None, _("Amount is required")

    try:
        # Convert to Decimal safely
        amount = Decimal(str(amount_data).strip())
        if amount <= 0:
            return None, _("Amount must be greater than zero")
        return amount, None
    except (InvalidOperation, ValueError, TypeError):
        return None, _("Invalid amount format")


class CoupleWalletViewSet(viewsets.ModelViewSet):
    """
    Secure API endpoint for couple wallet management.
    """
    serializer_class = CoupleWalletSerializer
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [WalletAccessThrottle]

    def get_queryset(self):
        # Users can only access wallets where they are a partner
        return CoupleWallet.objects.filter(
            Q(partner1=self.request.user) | Q(partner2=self.request.user)
        )

    def get_object(self):
        try:
            return CoupleWallet.objects.get(
                Q(partner1=self.request.user) | Q(partner2=self.request.user)
            )
        except CoupleWallet.DoesNotExist:
            from couple_module.models import CoupleLink
            try:
                couple_link = CoupleLink.objects.get(
                    Q(user1=self.request.user) | Q(user2=self.request.user)
                )
                return CoupleWallet.objects.create(
                    partner1=couple_link.user1,
                    partner2=couple_link.user2,
                    balance=Decimal('0.00'),
                    emergency_fund=Decimal('0.00'),
                    joint_goals=Decimal('0.00'),
                    monthly_budget=Decimal('0.00')
                )
            except CoupleLink.DoesNotExist:
                raise CoupleWallet.DoesNotExist("No couple relationship found")

    def list(self, request, *args, **kwargs):
        """Override list to return single wallet object instead of array"""
        wallet = CoupleWallet.objects.filter(
            Q(partner1=request.user) | Q(partner2=request.user)
        ).first()
        
        if not wallet:
            from couple_module.models import CoupleLink
            try:
                couple_link = CoupleLink.objects.get(
                    models.Q(user1=request.user) | models.Q(user2=request.user)
                )
                wallet = CoupleWallet.objects.create(
                    partner1=couple_link.user1,
                    partner2=couple_link.user2,
                    balance=Decimal('0.00'),
                    emergency_fund=Decimal('0.00'),
                    joint_goals=Decimal('0.00'),
                    monthly_budget=Decimal('0.00')
                )
            except CoupleLink.DoesNotExist:
                # Return empty wallet data if no couple link exists
                wallet = None
        
        if wallet:
            serializer = self.get_serializer(wallet)
            return Response(serializer.data)
        else:
            return Response({'error': _('No couple relationship found.')}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['get'])
    def balance(self, request):
        """Get wallet balance securely"""
        # Try to get existing wallet or create new one
        wallet = CoupleWallet.objects.filter(
            Q(partner1=request.user) | Q(partner2=request.user)
        ).first()
        
        if not wallet:
            # Create wallet if it doesn't exist - find partners
            from couple_module.models import CoupleLink
            try:
                couple_link = CoupleLink.objects.get(
                    models.Q(user1=request.user) | models.Q(user2=request.user)
                )
                wallet = CoupleWallet.objects.create(
                    partner1=couple_link.user1,
                    partner2=couple_link.user2,
                    balance=Decimal('0.00'),
                    emergency_fund=Decimal('0.00'),
                    joint_goals=Decimal('0.00'),
                    monthly_budget=Decimal('0.00')
                )
            except CoupleLink.DoesNotExist:
                return Response({'error': _('No couple relationship found. Please link with a partner first.')}, status=status.HTTP_404_NOT_FOUND)

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

    @action(detail=False, methods=['get'])
    def welcome(self, request):
        """Welcome endpoint for couple wallet"""
        SecurityEventManager.log_event(
            SecurityEventManager.EVENT_TYPES['WALLET_ACCESS'],
            request.user.id,
            {'action': 'welcome', 'method': request.method, 'path': request.path}
        )

        return Response({
            'message': _('Welcome to the Couple Wallet API Service!')
        })

    @action(detail=False, methods=['post'])
    def deposit(self, request):
        """Secure deposit to couple wallet"""
        # Auto-create wallet if it doesn't exist
        wallet = CoupleWallet.objects.filter(
            Q(partner1=request.user) | Q(partner2=request.user)
        ).first()
        
        if not wallet:
            from couple_module.models import CoupleLink
            try:
                couple_link = CoupleLink.objects.get(
                    models.Q(user1=request.user) | models.Q(user2=request.user)
                )
                wallet = CoupleWallet.objects.create(
                    partner1=couple_link.user1,
                    partner2=couple_link.user2,
                    balance=Decimal('0.00'),
                    emergency_fund=Decimal('0.00'),
                    joint_goals=Decimal('0.00'),
                    monthly_budget=Decimal('0.00')
                )
            except CoupleLink.DoesNotExist:
                return Response({'error': _('No couple relationship found. Please link with a partner first.')}, status=status.HTTP_404_NOT_FOUND)
        
        try:
            amount_raw = request.data.get('amount', 0)
            try:
                amount = Decimal(amount_raw)
            except Exception:
                return Response({'error': _('Invalid amount format')}, status=status.HTTP_400_BAD_REQUEST)
            if amount <= 0:
                return Response({'error': _('Amount must be greater than zero')}, status=status.HTTP_400_BAD_REQUEST)
            description = request.data.get('description', _('Deposit'))

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
                SecurityEventManager.EVENT_TYPES['WALLET_DEPOSIT'],
                request.user.id,
                {'amount': amount, 'new_balance': new_balance, 'wallet_type': 'couple'}
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
            amount_raw = request.data.get('amount', 0)
            try:
                amount = Decimal(amount_raw)
            except Exception:
                return Response({'error': _('Invalid amount format')}, status=status.HTTP_400_BAD_REQUEST)
            if amount <= 0:
                return Response({'error': _('Amount must be greater than zero')}, status=status.HTTP_400_BAD_REQUEST)
            
            description = request.data.get('description', _('Withdrawal'))
            category = request.data.get('category', 'OTHER')

            # Check for suspicious activity
            if SecurityEventManager.detect_suspicious_activity(
                request.user.id, 'couple_wallet_withdrawal', threshold=3, time_window_minutes=15
            ):
                return Response(
                    {'error': _('Suspicious activity detected')},
                    status=status.HTTP_429_TOO_MANY_REQUESTS
                )

            new_balance = wallet.withdraw(amount, category, description, request.user)

            # Audit the operation
            AuditService.audit_wallet_operation(
                request.user.id,
                'couple_withdrawal',
                amount,
                {'description': description, 'category': category, 'wallet_type': 'couple'}
            )

            SecurityEventManager.log_event(
                SecurityEventManager.EVENT_TYPES['WALLET_WITHDRAWAL'],
                request.user.id,
                {'amount': amount, 'new_balance': new_balance, 'wallet_type': 'couple'}
            )

            return Response({
                'message': _('Withdrawal successful'),
                'new_balance': new_balance,
                'withdrawn_by': request.user.username
            })

        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def set_budget(self, request):
        """Set monthly budget for the couple wallet"""
        try:
            wallet = self.get_object()
            budget_raw = request.data.get('monthly_budget')
            if budget_raw is None:
                return Response({'error': _('monthly_budget is required')}, status=status.HTTP_400_BAD_REQUEST)
            
            wallet.monthly_budget = Decimal(str(budget_raw))
            wallet.save()
            
            return Response({
                'message': _('Monthly budget updated successfully'),
                'monthly_budget': float(wallet.monthly_budget)
            })
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def monthly_summary(self, request):
        """Get enhanced monthly transaction summary for dashboard charts"""
        try:
            wallet = self.get_object()
            from django.utils.timezone import localdate
            today_date = localdate()
            
            # Start of month in local time
            current_month_start_date = today_date.replace(day=1)
            
            # Use __date lookup for transactions to ensure local date matching
            transactions = CoupleWalletTransaction.objects.filter(
                wallet=wallet,
                created_at__date__gte=current_month_start_date,
                created_at__date__lte=today_date
            )
            
            summary = transactions.aggregate(
                total_deposits=Sum('amount', filter=Q(transaction_type='DEPOSIT')),
                total_withdrawals=Sum('amount', filter=Q(transaction_type='WITHDRAWAL')),
                total_transfers=Sum('amount', filter=Q(transaction_type__in=['EMERGENCY_TRANSFER', 'GOAL_TRANSFER'])),
                transaction_count=Count('id')
            )

            # 2. Category Breakdown (Pie Chart) with Partner Attribution
            # Include WITHDRAWAL and GOAL_TRANSFER
            category_qs = transactions.filter(
                transaction_type__in=['WITHDRAWAL', 'GOAL_TRANSFER']
            ).values('category', 'withdrawn_by__username', 'transaction_type').annotate(
                total=Sum('amount')
            ).order_by('-total')
            
            category_data = []
            for item in category_qs:
                cat_label = item['category']
                if item['transaction_type'] == 'GOAL_TRANSFER':
                    cat_label = 'SAVINGS GOAL'
                
                category_data.append({
                    'category': cat_label,
                    'withdrawn_by': item['withdrawn_by__username'] or _('System'),
                    'total': float(item['total'] or 0)
                })

            # 3. Spending Trend (Continuous Daily Breakdown for current month)
            # Include all outflows (Withdrawals + Transfers to goals)
            daily_spending_qs = transactions.filter(
                transaction_type__in=['WITHDRAWAL', 'GOAL_TRANSFER', 'EMERGENCY_TRANSFER']
            ).values('created_at__date').annotate(
                total=Sum('amount')
            ).order_by('created_at__date')
            
            # Map by date object for reliability
            data_map = {item['created_at__date']: float(item['total'] or 0) for item in daily_spending_qs}
            
            spending_trend = []
            import calendar
            
            # Fill every day of the month from 1st to today (using local date)
            for day in range(1, today_date.day + 1):
                current_date = today_date.replace(day=day)
                spending_trend.append({
                    'day': str(day),
                    'full_date': str(current_date),
                    'total': data_map.get(current_date, 0.0)
                })

            # 4. Contribution Ratio
            p1_contrib = transactions.filter(transaction_type='DEPOSIT', deposited_by=wallet.partner1).aggregate(total=Sum('amount'))['total'] or Decimal(0)
            p2_contrib = transactions.filter(transaction_type='DEPOSIT', deposited_by=wallet.partner2).aggregate(total=Sum('amount'))['total'] or Decimal(0)
            
            total_contrib = float(p1_contrib + p2_contrib)
            p1_ratio = (float(p1_contrib) / total_contrib * 100) if total_contrib > 0 else 50
            p2_ratio = (float(p2_contrib) / total_contrib * 100) if total_contrib > 0 else 50

            # 5. Financial Health Score
            total_transfers = float(summary['total_transfers'] or 0)
            total_deposits = float(summary['total_deposits'] or 0)
            total_withdrawals = float(summary['total_withdrawals'] or 0)
            
            # Use total accumulated savings for a more stable savings rate
            total_savings = float(wallet.emergency_fund + wallet.joint_goals)
            
            # Get lifetime deposits for this wallet to calculate overall rate
            lifetime_deposits = CoupleWalletTransaction.objects.filter(
                wallet=wallet, transaction_type='DEPOSIT'
            ).aggregate(total=Sum('amount'))['total'] or Decimal('1.00')
            
            savings_rate = (total_savings / float(lifetime_deposits)) * 100
            
            budget_val = float(wallet.monthly_budget or 0)
            budget_adherence = 100 - ((total_withdrawals / budget_val * 100) if budget_val > 0 else 0)
            health_score = min(max((savings_rate * 0.4) + (budget_adherence * 0.6), 0), 100)

            return Response({
                'month_name': today_date.strftime('%B %Y'),
                'total_deposits': total_deposits,
                'total_withdrawals': total_withdrawals,
                'total_transfers': total_transfers,
                'monthly_budget': budget_val,
                'category_breakdown': category_data,
                'spending_trend': spending_trend,
                'metrics': {
                    'savings_rate': round(savings_rate, 1),
                    'p1_ratio': round(p1_ratio, 1),
                    'p2_ratio': round(p2_ratio, 1),
                    'health_score': round(health_score, 0)
                }
            })

        except CoupleWallet.DoesNotExist:
            return Response({'error': _('Couple wallet not found')}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def personal(self, request):
        from .models_wallet import CouplePersonalWallet
        from couple_module.models import CoupleLink
        
        # 1. Get own wallet
        my_wallet = CouplePersonalWallet.objects.filter(user=request.user).first()
        
        # 2. Get partner's wallet if linked and visible
        partner_wallet_data = None
        couple_link = CoupleLink.objects.filter(
            models.Q(user1=request.user) | models.Q(user2=request.user)
        ).first()
        
        if couple_link:
            partner = couple_link.user2 if couple_link.user1 == request.user else couple_link.user1
            p_wallet = CouplePersonalWallet.objects.filter(user=partner).first()
            if p_wallet and p_wallet.is_visible_to_partner:
                partner_wallet_data = {
                    'username': partner.username,
                    'balance': float(p_wallet.balance)
                }

        if not my_wallet:
            return Response({'partner_wallet': partner_wallet_data})
            
        return Response({
            'balance': float(my_wallet.balance),
            'is_visible_to_partner': my_wallet.is_visible_to_partner,
            'partner_wallet': partner_wallet_data
        })

    @action(detail=False, methods=['post'], url_path='personal/create')
    def personal_create(self, request):
        from .models_wallet import CouplePersonalWallet
        from couple_module.models import CoupleLink
        couple_link = CoupleLink.objects.filter(models.Q(user1=request.user) | models.Q(user2=request.user)).first()
        wallet, created = CouplePersonalWallet.objects.get_or_create(user=request.user, defaults={'couple_link': couple_link})
        return Response({'message': 'Personal wallet created'})

    @action(detail=False, methods=['patch'], url_path='personal/visibility')
    def personal_visibility(self, request):
        from .models_wallet import CouplePersonalWallet
        wallet = CouplePersonalWallet.objects.filter(user=request.user).first()
        if wallet:
            wallet.is_visible_to_partner = request.data.get('is_visible', False)
            wallet.save()
            return Response({'message': 'Visibility updated'})
        return Response({'error': 'No personal wallet'}, status=400)

    @action(detail=False, methods=['post'], url_path='personal/deposit')
    def personal_deposit(self, request):
        from .models_wallet import CouplePersonalWallet
        amount = Decimal(str(request.data.get('amount', 0)))
        if amount <= 0: return Response({'error': 'Invalid amount'}, status=400)
        
        wallet, _ = CouplePersonalWallet.objects.get_or_create(user=request.user)
        wallet.balance += amount
        wallet.save()
        
        # Log in general transactions but marked as PERSONAL
        CoupleWalletTransaction.objects.create(
            wallet=self.get_object(),
            amount=amount,
            transaction_type='DEPOSIT',
            category='PERSONAL',
            description="Personal Wallet Deposit",
            deposited_by=request.user,
            balance_after=0 # Private balance doesn't affect joint balance_after
        )
        return Response({'message': 'Deposit successful', 'new_balance': float(wallet.balance)})

    @action(detail=False, methods=['post'], url_path='personal/withdraw')
    def personal_withdraw(self, request):
        from .models_wallet import CouplePersonalWallet
        amount = Decimal(str(request.data.get('amount', 0)))
        if amount <= 0: return Response({'error': 'Invalid amount'}, status=400)
        
        wallet = CouplePersonalWallet.objects.filter(user=request.user).first()
        if not wallet or wallet.balance < amount:
            return Response({'error': 'Insufficient private balance'}, status=400)
            
        wallet.balance -= amount
        wallet.save()
        
        CoupleWalletTransaction.objects.create(
            wallet=self.get_object(),
            amount=amount,
            transaction_type='WITHDRAWAL',
            category='PERSONAL',
            description="Personal Wallet Withdrawal",
            withdrawn_by=request.user,
            balance_after=0
        )
        return Response({'message': 'Withdrawal successful', 'new_balance': float(wallet.balance)})

    @action(detail=False, methods=['get'], url_path='personal/transactions')
    def personal_transactions(self, request):
        txs = CoupleWalletTransaction.objects.filter(
            Q(deposited_by=request.user) | Q(withdrawn_by=request.user),
            category='PERSONAL'
        ).order_by('-created_at')
        
        return Response([{
            'id': t.id,
            'amount': float(t.amount),
            'type': t.transaction_type,
            'description': t.description,
            'date': t.created_at
        } for t in txs])

    @action(detail=False, methods=['get'])
    def goals(self, request):
        from .models_wallet import JointGoal
        goals = JointGoal.objects.filter(couple__user1=request.user) | JointGoal.objects.filter(couple__user2=request.user)
        return Response([{
            'id': g.id,
            'name': g.name,
            'target_amount': g.target_amount,
            'current_amount': g.current_amount,
            'deadline': g.deadline,
            'progress_percentage': g.progress_percentage
        } for g in goals.distinct()])

    @action(detail=False, methods=['post'])
    def goals_create(self, request):
        from .models_wallet import JointGoal
        from couple_module.models import CoupleLink
        couple_link = CoupleLink.objects.filter(models.Q(user1=request.user) | models.Q(user2=request.user)).first()
        if not couple_link: return Response({'error': 'No couple link'}, status=400)
        goal = JointGoal.objects.create(
            couple=couple_link,
            name=request.data.get('name'),
            target_amount=Decimal(request.data.get('target_amount', 0)),
            deadline=request.data.get('deadline')
        )
        return Response({'message': 'Goal created'})

    @action(detail=False, methods=['post'])
    def goals_contribute(self, request):
        from .models_wallet import JointGoal, CoupleWalletTransaction
        goal_id = request.data.get('goal_id')
        amount = Decimal(request.data.get('amount', 0))
        wallet = self.get_object()
        
        if wallet.balance < amount:
            return Response({'error': 'Insufficient funds in joint wallet'}, status=400)
            
        try:
            goal = JointGoal.objects.get(id=goal_id)
            
            # Deduct from spending balance, add to goals total
            wallet.balance -= amount
            wallet.joint_goals += amount
            wallet.save()
            
            # Update specific goal
            goal.current_amount += amount
            goal.save()

            # Record transaction for history
            CoupleWalletTransaction.objects.create(
                wallet=wallet,
                amount=amount,
                transaction_type='GOAL_TRANSFER',
                description=f"Contributed to goal: {goal.name}",
                balance_after=wallet.balance
            )

            return Response({
                'message': 'Contributed to goal successfully',
                'new_goal_amount': float(goal.current_amount),
                'new_joint_balance': float(wallet.balance)
            })
        except JointGoal.DoesNotExist:
            return Response({'error': 'Goal not found'}, status=404)

    @action(detail=False, methods=['patch'], url_path='goals/update')
    def update_goal(self, request):
        from .models_wallet import JointGoal
        goal_id = request.data.get('goal_id')
        goal = JointGoal.objects.get(id=goal_id)
        
        if 'name' in request.data: goal.name = request.data['name']
        if 'target_amount' in request.data: goal.target_amount = Decimal(str(request.data['target_amount']))
        if 'deadline' in request.data: goal.deadline = request.data['deadline']
        
        goal.save()
        return Response({'message': 'Goal updated successfully'})

    @action(detail=False, methods=['get'])
    def settlement(self, request):
        wallet = self.get_object()
        from .models_wallet import CoupleWalletTransaction
        # Get only shared transactions (exclude PERSONAL)
        txs = CoupleWalletTransaction.objects.filter(wallet=wallet).exclude(category='PERSONAL').order_by('-created_at')
        
        p1_contrib = txs.filter(transaction_type='DEPOSIT', deposited_by=wallet.partner1).aggregate(Sum('amount'))['amount__sum'] or Decimal(0)
        p2_contrib = txs.filter(transaction_type='DEPOSIT', deposited_by=wallet.partner2).aggregate(Sum('amount'))['amount__sum'] or Decimal(0)
        total_shared = txs.filter(transaction_type='WITHDRAWAL').aggregate(Sum('amount'))['amount__sum'] or Decimal(0)
        
        ideal_share = total_shared / Decimal(2)
        p1_net = p1_contrib
        p2_net = p2_contrib
        
        diff = p1_net - p2_net
        amount_owed = abs(diff) / Decimal(2)
        owes_to = None
        if diff > 0:
            owes_to = wallet.partner1.username
        elif diff < 0:
            owes_to = wallet.partner2.username
            
        # Serialize history for the settlement view
        history = [{
            'id': t.id,
            'amount': float(t.amount),
            'type': t.transaction_type,
            'category': t.category,
            'description': t.description,
            'user': t.deposited_by.username if t.deposited_by else (t.withdrawn_by.username if t.withdrawn_by else 'System'),
            'date': t.created_at
        } for t in txs]

        return Response({
            'partner1_contributed': p1_contrib,
            'partner2_contributed': p2_contrib,
            'total_shared_expenses': total_shared,
            'ideal_share': ideal_share,
            'imbalance': diff,
            'owes_to': owes_to,
            'amount_owed': amount_owed,
            'history': history
        })


class CoupleWalletTransactionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    View transaction history for couple wallets.
    """
    serializer_class = CoupleWalletTransactionSerializer
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [WalletAccessThrottle]

    def get_queryset(self):
        return CoupleWalletTransaction.objects.filter(
            Q(wallet__partner1=self.request.user) | Q(wallet__partner2=self.request.user)
        ).exclude(category='PERSONAL').order_by('-created_at')


class GenerateCoupleWalletOTPView(APIView):
    """
    Secure API endpoint for generating OTP for couple wallet operations.
    """
    permission_classes = [permissions.IsAuthenticated, OTPGenerationPermission]
    throttle_classes = [OTPGenerationThrottle, SensitiveOperationsThrottle]

    def post(self, request, *args, **kwargs):
        # Make operation_type optional with default value for flexibility
        operation_type = request.data.get('operation_type', 'wallet_operation')
        amount_data = request.data.get('amount')
        description = request.data.get('description', '')

        # Validate amount if provided
        amount = None
        if amount_data is not None:
            amount, error = validate_and_convert_amount(amount_data)
            if error:
                return Response({'error': _(error)}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Get couple wallet
            wallet = CoupleWallet.objects.get(
                Q(partner1=request.user) | Q(partner2=request.user)
            )
        except CoupleWallet.DoesNotExist:
            return Response({'error': _('Couple wallet not found')}, status=status.HTTP_404_NOT_FOUND)

        # Generate secure OTP
        otp_request_data = OTPSecurityService.create_otp_request(
            request.user.id,
            'couple_wallet_operation',
            email=request.user.email
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
            'message': _('OTP generated and sent successfully for couple wallet operation'),
            'otp_request_id': otp_request.id,
            'operation_type': operation_type,
            'expires_at': expires_at
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
            is_valid, error_message = OTPSecurityService.validate_otp(
                request.user.id,
                otp_code,
                otp_request.cache_key,
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
