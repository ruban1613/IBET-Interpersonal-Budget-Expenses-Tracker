import os, sys, django
from decimal import Decimal
from django.utils import timezone

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings_testing_final')
sys.path.insert(0, os.path.dirname(__file__))
django.setup()

from student_module.models import User, Wallet, DailySpending, SpendingLock

def check_ruki():
    username = 'Ruki16'
    try:
        user = User.objects.get(username=username)
        print(f"User: {user.username} (ID: {user.id})")
        
        wallet = Wallet.objects.get(user=user)
        print(f"Wallet Locked: {wallet.is_locked}")
        
        today = timezone.now().date()
        
        ds = DailySpending.objects.filter(student=user, date=today).first()
        if ds:
            print(f"Daily Spending Today ({today}): Spent={ds.amount_spent}, Limit={ds.daily_limit}, Locked={ds.is_locked}")
        else:
            print(f"No Daily Spending record for today ({today}).")
            
        locks = SpendingLock.objects.filter(student=user, is_active=True)
        print(f"Active Locks: {locks.count()}")
        for l in locks:
            print(f" - Type: {l.lock_type}, Created: {l.created_at}")
            
    except User.DoesNotExist:
        print("User Ruki16 not found")

if __name__ == '__main__':
    check_ruki()
