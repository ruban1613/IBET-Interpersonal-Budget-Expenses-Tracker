import os, sys, django
sys.path.insert(0, os.path.join('.', 'IBET'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings_testing_final')
django.setup()
from django.db import connection
cursor = connection.cursor()

tables = [
    'dailywage_module_dailywagewallet',
    'couple_module_couplewallet',
    'individual_module_individualwallet',
    'retiree_module_retireewallet',
    'student_module_wallet'
]

print("Checking for corrupted balances (negative or extremely large)...")

for table in tables:
    try:
        cursor.execute(f'SELECT id, balance FROM {table} WHERE balance > 99999999.99 OR balance < 0')
        rows = cursor.fetchall()
        if rows:
            print(f'{table}: {len(rows)} corrupted balances')
            for row in rows:
                print(f'  ID {row[0]}: {row[1]}')
        else:
            print(f'{table}: No corrupted balances found')
    except Exception as e:
        print(f'{table}: Error checking - {e}')

print("Check complete.")
