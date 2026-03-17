import os, sys, django
from decimal import Decimal
from django.utils import timezone

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings_testing_final')
sys.path.insert(0, os.path.dirname(__file__))
django.setup()

from student_module.models import User, Wallet

def find_high_balance():
    print(f"Server Today: {timezone.now().date()}")
    
    wallets = Wallet.objects.filter(balance__gt=30000)
    print(f"Wallets with Balance > 30000: {wallets.count()}")
    for w in wallets:
        print(f" - User: {w.user.username} (ID: {w.user.id}), Balance: {w.balance}, Locked: {w.is_locked}")

if __name__ == '__main__':
    find_high_balance()
