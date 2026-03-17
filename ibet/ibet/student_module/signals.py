from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.db.models import Sum
from decimal import Decimal
from .models import Transaction, DailySpending, DailyAllowance, CumulativeSpendingTracker

@receiver(post_save, sender=Transaction)
def update_spending_trackers(sender, instance, created, **kwargs):
    """
    Update DailySpending, DailyAllowance, MonthlySpendingSummary and CumulativeSpendingTracker 
    whenever a Transaction is created or updated.
    """
    if instance.transaction_type != 'EXP':
        return

    user = instance.user
    today = instance.transaction_date
    
    # 1. Update DailySpending (Old system)
    daily, _ = DailySpending.objects.get_or_create(
        student=user,
        date=today,
        defaults={'daily_limit': Decimal('0.00'), 'remaining_amount': Decimal('0.00')}
    )
    
    # Recalculate total spent for this day from all transactions
    # EXCLUDE Pocket Money transactions
    total_spent_today = Transaction.objects.filter(
        user=user,
        transaction_type='EXP',
        transaction_date=today
    ).exclude(description__icontains='[Pocket Money]').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    
    daily.amount_spent = total_spent_today
    # Note: remaining_amount depends on daily_limit which might be set elsewhere
    if daily.daily_limit > 0:
        daily.remaining_amount = daily.daily_limit - daily.amount_spent
    
    if daily.remaining_amount <= 0 and daily.daily_limit > 0:
        daily.is_locked = True
    else:
        daily.is_locked = False
    daily.save()

    # 2. Update DailyAllowance (New system)
    try:
        da = DailyAllowance.objects.get(student=user, date=today)
        da.amount_spent = total_spent_today
        da.remaining_amount = da.daily_amount - total_spent_today
        if da.remaining_amount <= 0:
            da.is_available = False
            da.is_locked = True
        else:
            da.is_available = True
            da.is_locked = False
        da.save()
    except DailyAllowance.DoesNotExist:
        pass

    # 3. Update MonthlySpendingSummary
    from .models import MonthlySpendingSummary
    try:
        summary, _ = MonthlySpendingSummary.objects.get_or_create(
            student=user,
            month=today.month,
            year=today.year,
            defaults={
                'total_allowance': Decimal('0.00'),
                'remaining_amount': Decimal('0.00'),
                'total_spent': Decimal('0.00')
            }
        )
        total_spent_month = Transaction.objects.filter(
            user=user,
            transaction_type='EXP',
            transaction_date__month=today.month,
            transaction_date__year=today.year
        ).exclude(description__icontains='[Pocket Money]').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        summary.total_spent = total_spent_month
        if summary.total_allowance > 0:
            summary.remaining_amount = summary.total_allowance - total_spent_month
        summary.save()
    except Exception as e:
        print(f"Error updating MonthlySpendingSummary in signal: {e}")

    # 4. Update CumulativeSpendingTracker
    try:
        tracker = CumulativeSpendingTracker.objects.get(
            student=user,
            month=today.month,
            year=today.year
        )
        tracker.total_spent = total_spent_month if 'total_spent_month' in locals() else (
            Transaction.objects.filter(
                user=user,
                transaction_type='EXP',
                transaction_date__month=today.month,
                transaction_date__year=today.year
            ).exclude(description__icontains='[Pocket Money]').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        )
        tracker.total_available = tracker.total_allocated - tracker.total_spent
        tracker.save()
    except CumulativeSpendingTracker.DoesNotExist:
        pass
