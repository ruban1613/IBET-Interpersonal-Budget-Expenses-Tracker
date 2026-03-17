"""
Enhanced Individual Module Views
Includes API endpoints for dual wallet system, expense tracking, and smart alerts.
"""
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from decimal import Decimal
import random
import string

from .models import (
    IndividualSavingsWallet,
    SavingsTransaction,
    IndividualExpense,
    SpendingAlert,
    SpendingAnomalyDetector
)
from .models_wallet import IndividualWallet, IndividualWalletTransaction, IndividualWalletOTPRequest


def generate_otp():
    """Generate a 6-digit OTP"""
    return ''.join(random.choices(string.digits, k=6))


def get_or_create_main_wallet(user):
    """Get or create main wallet for user"""
    wallet, created = IndividualWallet.objects.get_or_create(
        user=user,
        defaults={
            'balance': Decimal('0.00'),
            'monthly_budget': Decimal('0.00'),
            'savings_goal': Decimal('0.00'),
            'current_savings': Decimal('0.00'),
            'alert_threshold': Decimal('0.00')
        }
    )
    return wallet


def get_or_create_savings_wallet(user):
    """Get or create savings wallet for user"""
    wallet, created = IndividualSavingsWallet.objects.get_or_create(
        user=user,
        defaults={
            'balance': Decimal('0.00'),
            'total_deposits': Decimal('0.00'),
            'total_withdrawals': Decimal('0.00')
        }
    )
    return wallet


@login_required
@require_http_methods(["GET"])
def get_individual_dashboard(request):
    """Get individual user's dashboard data"""
    user = request.user
    
    # Get main wallet
    main_wallet = get_or_create_main_wallet(user)
    
    # Get savings wallet
    savings_wallet = get_or_create_savings_wallet(user)
    
    # Get recent expenses
    recent_expenses = IndividualExpense.objects.filter(user=user)[:10]
    
    # Get spending stats
    stats = SpendingAnomalyDetector.get_average_spending(user)
    
    # Get unread alerts
    unread_alerts = SpendingAlert.objects.filter(user=user, is_read=False)
    
    return JsonResponse({
        'main_wallet': {
            'balance': str(main_wallet.balance),
            'monthly_budget': str(main_wallet.monthly_budget),
            'savings_goal': str(main_wallet.savings_goal),
            'current_savings': str(main_wallet.current_savings)
        },
        'savings_wallet': {
            'balance': str(savings_wallet.balance),
            'total_deposits': str(savings_wallet.total_deposits),
            'total_withdrawals': str(savings_wallet.total_withdrawals)
        },
        'expenses': [
            {
                'id': exp.id,
                'amount': str(exp.amount),
                'category': exp.category,
                'description': exp.description,
                'expense_date': exp.expense_date.isoformat(),
                'created_at': exp.created_at.isoformat()
            }
            for exp in recent_expenses
        ],
        'stats': {
            'average_spending': str(stats['average']),
            'total_spent': str(stats['total']),
            'transaction_count': stats['count']
        },
        'unread_alerts_count': unread_alerts.count()
    })


@login_required
@require_http_methods(["POST"])
@csrf_exempt
def deposit_to_main_wallet(request):
    """
    Deposit money to main wallet - requires OTP verification.
    """
    user = request.user
    
    try:
        import json
        data = json.loads(request.body)
        amount = Decimal(str(data.get('amount', 0)))
        description = data.get('description', 'Deposit')
        otp_code = data.get('otp', '')
        otp_request_id = data.get('otp_request_id')
        
        if amount <= 0:
            return JsonResponse({'error': 'Invalid amount'}, status=400)
        
        # Verify OTP if provided
        if otp_code and otp_request_id:
            try:
                otp_request = IndividualWalletOTPRequest.objects.get(
                    id=otp_request_id,
                    user=user,
                    is_used=False
                )
                if otp_request.is_expired():
                    return JsonResponse({'error': 'OTP expired'}, status=400)
                if otp_request.otp_code != otp_code:
                    return JsonResponse({'error': 'Invalid OTP'}, status=400)
                
                # Mark OTP as used
                otp_request.mark_as_used()
                otp_verified = True
            except IndividualWalletOTPRequest.DoesNotExist:
                return JsonResponse({'error': 'Invalid OTP request'}, status=400)
        else:
            # No OTP provided - generate one for deposit
            otp = generate_otp()
            expires_at = timezone.now() + timezone.timedelta(minutes=10)
            
            otp_request = IndividualWalletOTPRequest.objects.create(
                user=user,
                operation_type='DEPOSIT',
                amount=amount,
                description=description,
                otp_code=otp,
                expires_at=expires_at
            )
            
            return JsonResponse({
                'requires_otp': True,
                'otp_request_id': otp_request.id,
                'otp_code': otp,  # In production, send via email only
                'message': 'OTP sent to your email'
            })
        
        # Deposit money
        wallet = get_or_create_main_wallet(user)
        wallet.deposit(amount, description)
        
        return JsonResponse({
            'success': True,
            'new_balance': str(wallet.balance),
            'message': f'Deposited ₹{amount} successfully'
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
@csrf_exempt
def withdraw_from_main_wallet(request):
    """
    Withdraw money from main wallet - no OTP required.
    """
    user = request.user
    
    try:
        import json
        data = json.loads(request.body)
        amount = Decimal(str(data.get('amount', 0)))
        description = data.get('description', 'Withdrawal')
        
        if amount <= 0:
            return JsonResponse({'error': 'Invalid amount'}, status=400)
        
        wallet = get_or_create_main_wallet(user)
        
        if wallet.balance < amount:
            return JsonResponse({'error': 'Insufficient balance'}, status=400)
        
        wallet.withdraw(amount, description)
        
        return JsonResponse({
            'success': True,
            'new_balance': str(wallet.balance),
            'message': f'Withdrawn ₹{amount} successfully'
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
@csrf_exempt
def transfer_to_savings(request):
    """
    Transfer money to savings wallet - requires OTP verification.
    """
    user = request.user
    
    try:
        import json
        data = json.loads(request.body)
        amount = Decimal(str(data.get('amount', 0)))
        otp_code = data.get('otp', '')
        otp_request_id = data.get('otp_request_id')
        
        if amount <= 0:
            return JsonResponse({'error': 'Invalid amount'}, status=400)
        
        # Verify OTP if provided
        if otp_code and otp_request_id:
            try:
                otp_request = IndividualWalletOTPRequest.objects.get(
                    id=otp_request_id,
                    user=user,
                    is_used=False,
                    operation_type='TRANSFER_TO_SAVINGS'
                )
                if otp_request.is_expired():
                    return JsonResponse({'error': 'OTP expired'}, status=400)
                if otp_request.otp_code != otp_code:
                    return JsonResponse({'error': 'Invalid OTP'}, status=400)
                
                otp_request.mark_as_used()
            except IndividualWalletOTPRequest.DoesNotExist:
                return JsonResponse({'error': 'Invalid OTP request'}, status=400)
        else:
            # Generate OTP for savings transfer
            otp = generate_otp()
            expires_at = timezone.now() + timezone.timedelta(minutes=10)
            
            otp_request = IndividualWalletOTPRequest.objects.create(
                user=user,
                operation_type='TRANSFER_TO_SAVINGS',
                amount=amount,
                description='Transfer to Savings',
                otp_code=otp,
                expires_at=expires_at
            )
            
            return JsonResponse({
                'requires_otp': True,
                'otp_request_id': otp_request.id,
                'otp_code': otp,
                'message': 'OTP sent to your email'
            })
        
        # Check main wallet balance
        main_wallet = get_or_create_main_wallet(user)
        if main_wallet.balance < amount:
            return JsonResponse({'error': 'Insufficient balance in main wallet'}, status=400)
        
        # Transfer to savings
        main_wallet.withdraw(amount, 'Transfer to Savings')
        savings_wallet = get_or_create_savings_wallet(user)
        savings_wallet.deposit(amount, 'Transfer from Main Wallet')
        
        return JsonResponse({
            'success': True,
            'main_wallet_balance': str(main_wallet.balance),
            'savings_wallet_balance': str(savings_wallet.balance),
            'message': f'Transferred ₹{amount} to savings successfully'
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
@csrf_exempt
def record_expense(request):
    """
    Record an expense and check for alerts/anomalies.
    """
    user = request.user
    
    try:
        import json
        data = json.loads(request.body)
        amount = Decimal(str(data.get('amount', 0)))
        category = data.get('category', 'OTHER')
        description = data.get('description', '')
        
        if amount <= 0:
            return JsonResponse({'error': 'Invalid amount'}, status=400)
        
        # Record expense and get alerts
        expense, alerts = IndividualExpense.record_expense_and_check_alerts(
            user=user,
            amount=amount,
            category=category,
            description=description
        )
        
        return JsonResponse({
            'success': True,
            'expense_id': expense.id,
            'alerts_created': len(alerts),
            'alerts': [
                {
                    'id': alert.id,
                    'type': alert.alert_type,
                    'title': alert.title,
                    'message': alert.message
                }
                for alert in alerts
            ]
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def get_spending_alerts(request):
    """Get all spending alerts for the user"""
    user = request.user
    
    alerts = SpendingAlert.objects.filter(user=user)
    
    return JsonResponse({
        'alerts': [
            {
                'id': alert.id,
                'type': alert.alert_type,
                'title': alert.title,
                'message': alert.message,
                'percentage': str(alert.percentage) if alert.percentage else None,
                'is_read': alert.is_read,
                'created_at': alert.created_at.isoformat()
            }
            for alert in alerts
        ]
    })


@login_required
@require_http_methods(["POST"])
@csrf_exempt
def mark_alert_read(request, alert_id):
    """Mark a spending alert as read"""
    user = request.user
    
    try:
        alert = SpendingAlert.objects.get(id=alert_id, user=user)
        alert.mark_as_read()
        return JsonResponse({'success': True})
    except SpendingAlert.DoesNotExist:
        return JsonResponse({'error': 'Alert not found'}, status=404)


@login_required
@require_http_methods(["GET"])
def get_expense_categories(request):
    """Get list of expense categories"""
    categories = [
        {'value': 'FOOD', 'label': 'Food & Dining', 'icon': '🍔'},
        {'value': 'TRANSPORT', 'label': 'Transportation', 'icon': '🚗'},
        {'value': 'UTILITIES', 'label': 'Utilities', 'icon': '💡'},
        {'value': 'ENTERTAINMENT', 'label': 'Entertainment', 'icon': '🎬'},
        {'value': 'SHOPPING', 'label': 'Shopping', 'icon': '🛒'},
        {'value': 'HEALTH', 'label': 'Healthcare', 'icon': '🏥'},
        {'value': 'EDUCATION', 'label': 'Education', 'icon': '📚'},
        {'value': 'BILLS', 'label': 'Bills & Payments', 'icon': '📄'},
        {'value': 'OTHER', 'label': 'Other', 'icon': '📦'}
    ]
    
    return JsonResponse({'categories': categories})


@login_required
@require_http_methods(["GET"])
def get_spending_stats(request):
    """Get spending statistics for the user"""
    user = request.user
    
    stats = SpendingAnomalyDetector.get_average_spending(user)
    expenses = IndividualExpense.objects.filter(user=user)
    
    # Category breakdown
    category_totals = expenses.values('category').annotate(
        total=Sum('amount')
    ).order_by('-total')
    
    return JsonResponse({
        'average_spending': str(stats['average']),
        'total_spent': str(stats['total']),
        'transaction_count': stats['count'],
        'category_breakdown': [
            {'category': item['category'], 'total': str(item['total'])}
            for item in category_totals
        ]
    })


@login_required
@require_http_methods(["POST"])
@csrf_exempt
def generate_deposit_otp(request):
    """Generate OTP for deposit"""
    user = request.user
    
    try:
        import json
        data = json.loads(request.body)
        amount = Decimal(str(data.get('amount', 0)))
        
        if amount <= 0:
            return JsonResponse({'error': 'Invalid amount'}, status=400)
        
        otp = generate_otp()
        expires_at = timezone.now() + timezone.timedelta(minutes=10)
        
        otp_request = IndividualWalletOTPRequest.objects.create(
            user=user,
            operation_type='DEPOSIT',
            amount=amount,
            description='Wallet Deposit',
            otp_code=otp,
            expires_at=expires_at
        )
        
        return JsonResponse({
            'otp_request_id': otp_request.id,
            'otp_code': otp,  # In production, send via email only
            'expires_at': expires_at.isoformat()
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
@csrf_exempt
def generate_savings_otp(request):
    """Generate OTP for savings transfer"""
    user = request.user
    
    try:
        import json
        data = json.loads(request.body)
        amount = Decimal(str(data.get('amount', 0)))
        
        if amount <= 0:
            return JsonResponse({'error': 'Invalid amount'}, status=400)
        
        otp = generate_otp()
        expires_at = timezone.now() + timezone.timedelta(minutes=10)
        
        otp_request = IndividualWalletOTPRequest.objects.create(
            user=user,
            operation_type='TRANSFER_TO_SAVINGS',
            amount=amount,
            description='Transfer to Savings',
            otp_code=otp,
            expires_at=expires_at
        )
        
        return JsonResponse({
            'otp_request_id': otp_request.id,
            'otp_code': otp,
            'expires_at': expires_at.isoformat()
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
@csrf_exempt
def set_monthly_budget(request):
    """Set monthly budget for spending tracking"""
    user = request.user
    
    try:
        import json
        data = json.loads(request.body)
        monthly_budget = Decimal(str(data.get('monthly_budget', 0)))
        
        if monthly_budget < 0:
            return JsonResponse({'error': 'Invalid budget amount'}, status=400)
        
        wallet = get_or_create_main_wallet(user)
        wallet.monthly_budget = monthly_budget
        wallet.save()
        
        return JsonResponse({
            'success': True,
            'monthly_budget': str(wallet.monthly_budget),
            'message': f'Monthly budget set to ₹{monthly_budget}'
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
@csrf_exempt
def set_savings_goal(request):
    """Set savings goal"""
    user = request.user
    
    try:
        import json
        data = json.loads(request.body)
        savings_goal = Decimal(str(data.get('savings_goal', 0)))
        
        if savings_goal < 0:
            return JsonResponse({'error': 'Invalid savings goal'}, status=400)
        
        wallet = get_or_create_main_wallet(user)
        wallet.savings_goal = savings_goal
        wallet.save()
        
        return JsonResponse({
            'success': True,
            'savings_goal': str(wallet.savings_goal),
            'message': f'Savings goal set to ₹{savings_goal}'
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
