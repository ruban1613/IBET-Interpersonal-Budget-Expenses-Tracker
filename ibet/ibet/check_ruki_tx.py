import os, sys, django
from django.utils import timezone

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings_testing_final')
sys.path.insert(0, os.path.dirname(__file__))
django.setup()

from student_module.models import User, Transaction

def check_tx():
    user = User.objects.get(username='Ruki16')
    txs = Transaction.objects.filter(user=user).order_by('-id')[:10]
    print(f"Transactions for {user.username}:")
    for tx in txs:
        print(f"ID: {tx.id}, Date: {tx.transaction_date}, Type: {tx.transaction_type}, Amount: {tx.amount}, Desc: {tx.description}")

if __name__ == '__main__':
    check_tx()
