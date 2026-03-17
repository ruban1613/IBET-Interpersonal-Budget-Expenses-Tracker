import os
import django
import sys
from decimal import Decimal

# Set up Django environment
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from student_module.models import User, Wallet
from individual_module.models import IndividualExpense

def test_expense_record(username, amount_val):
    try:
        user = User.objects.get(username=username)
        print(f"Testing expense for {user.username} (Persona: {user.persona})")
        print(f"Current Balance: {user.wallet.balance}")
        
        amount = Decimal(str(amount_val))
        category = 'FOOD'
        description = 'Test Expense'
        
        expense, alerts = IndividualExpense.record_expense_and_check_alerts(
            user, amount, category, description
        )
        
        print(f"SUCCESS! New Balance: {user.wallet.balance}")
        print(f"Expense created: ID {expense.id}, Amt {expense.amount}")
        
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    test_expense_record('kumar', 10.00)
    print("-" * 20)
    test_expense_record('keeru', 10.00)
