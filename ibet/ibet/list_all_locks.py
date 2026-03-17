import os, sys, django
from decimal import Decimal
from django.utils import timezone

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings_testing_final')
sys.path.insert(0, os.path.dirname(__file__))
django.setup()

from student_module.models import User, Wallet, SpendingLock, DailySpending

def list_locks():
    print(f"Server Today: {timezone.now().date()}")
    
    locked_wallets = Wallet.objects.filter(is_locked=True)
    print(f"Locked Wallets: {locked_wallets.count()}")
    for w in locked_wallets:
        print(f" - Wallet: {w.user.username} (ID: {w.user.id})")
        
    active_locks = SpendingLock.objects.filter(is_active=True)
    print(f"Active Spending Locks: {active_locks.count()}")
    for lock in active_locks:
        print(f" - Student: {lock.student.username} (ID: {lock.student.id}), Type: {lock.lock_type}, Created At: {lock.created_at}")

if __name__ == '__main__':
    list_locks()
