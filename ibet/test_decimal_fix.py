import os
import django
from decimal import Decimal, InvalidOperation

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from dailywage_module.models_wallet import DailyWageWallet
from django.contrib.auth import get_user_model

User = get_user_model()

def test_decimal_conversion():
    """Test decimal conversion from database"""
    try:
        user = User.objects.get(username='edge_test_dailywage')
        print('User found')

        # Try to get wallet using raw SQL to bypass Django's converter
        from django.db import connection
        cursor = connection.cursor()

        cursor.execute("""
            SELECT id, balance FROM dailywage_module_dailywagewallet
            WHERE user_id = %s
        """, [user.id])

        row = cursor.fetchone()
        print(f'Raw SQL result: ID={row[0]}, Balance={repr(row[1])}')

        # Try manual conversion
        try:
            balance_decimal = Decimal(str(row[1]))
            print(f'Manual conversion successful: {balance_decimal}')
        except InvalidOperation as e:
            print(f'Manual conversion failed: {e}')

        # Try Django ORM with error handling
        try:
            wallets = DailyWageWallet.objects.filter(user=user)
            print(f'Django ORM query successful, count: {wallets.count()}')
            for w in wallets:
                print(f'Wallet: ID={w.id}, Balance={w.balance}')
        except Exception as e:
            print(f'Django ORM failed: {e}')

    except Exception as e:
        print(f'Error: {e}')

if __name__ == '__main__':
    test_decimal_conversion()
