import os
import django
import sys
from decimal import Decimal

# Set up Django environment
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from student_module.models import User, Wallet, Transaction

def fix_kumar_data():
    try:
        u = User.objects.get(username='kumar')
        w = u.wallet
        w.balance = Decimal('3000.00')
        w.save()
        
        t = Transaction.objects.filter(user=u, amount=Decimal('150000.00')).first()
        if t:
            t.amount = Decimal('15000.00')
            t.save()
            print(f"Corrected Transaction ID {t.id} to 15,000")
            
        print(f"Successfully corrected balance for {u.username} (UID: {u.uid}) to 3,000.00")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    fix_kumar_data()
