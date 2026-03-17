import os
import django
import sys
from decimal import Decimal

# Set up Django environment
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from student_module.models import User, Wallet, WalletTransaction, Transaction
from individual_module.models import IndividualExpense

def get_student_statement(uid):
    u = User.objects.filter(uid=uid).first()
    if not u:
        print(f"Student with UID {uid} not found.")
        return

    print(f"Statement for {u.username} (UID: {u.uid})")
    
    print("\n--- Wallet Transactions ---")
    wallet_txs = WalletTransaction.objects.filter(wallet__user=u).order_by('-created_at')
    for t in wallet_txs:
        print(f"{t.created_at.strftime('%Y-%m-%d')} | {t.transaction_type:10} | ₹{t.amount:8} | {t.description}")

    print("\n--- General Transactions (Allowances/Transfers) ---")
    gen_txs = Transaction.objects.filter(user=u).order_by('-transaction_date')
    for t in gen_txs:
        print(f"{t.transaction_date} | {t.transaction_type:10} | ₹{t.amount:8} | {t.description}")

    print("\n--- Individual Expenses (EXP) ---")
    expenses = IndividualExpense.objects.filter(user=u).order_by('-expense_date')
    for e in expenses:
        print(f"{e.expense_date} | EXPENSE    | ₹{e.amount:8} | [{e.category}] {e.description}")

if __name__ == "__main__":
    get_student_statement('IBET-957132')
