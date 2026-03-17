import os, sys, django
from decimal import Decimal
from django.utils import timezone

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings_testing_final')
sys.path.insert(0, os.path.dirname(__file__))
django.setup()

from student_module.models import User, Wallet, SpendingLock, DailySpending, DailyAllowance

def check_keeru():
    username = 'keeru'
    try:
        user = User.objects.get(username=username)
        print(f"User: {user.username} (ID: {user.id})")
        
        wallet = Wallet.objects.get(user=user)
        print(f"Wallet Locked: {wallet.is_locked}")
        print(f"Main Balance: {wallet.balance}")
        print(f"Special Balance: {wallet.special_balance}")
        
        today = timezone.now().date()
        print(f"Server Today: {today}")
        
        active_locks = SpendingLock.objects.filter(student=user, is_active=True)
        print(f"Active Locks: {active_locks.count()}")
        for lock in active_locks:
            print(f" - Lock Type: {lock.lock_type}, Created At: {lock.created_at}")
            
        daily_spending = DailySpending.objects.filter(student=user, date=today).first()
        if daily_spending:
            print(f"Daily Spending Today: Spent={daily_spending.amount_spent}, Limit={daily_spending.daily_limit}, Locked={daily_spending.is_locked}")
        else:
            print("No Daily Spending record for today.")
            
    except User.DoesNotExist:
        print("User keeru not found")

if __name__ == '__main__':
    check_keeru()
