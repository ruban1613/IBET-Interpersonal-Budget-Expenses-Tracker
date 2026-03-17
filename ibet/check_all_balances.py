import sqlite3

conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()

# Check all wallet tables for corrupted balances
tables = [
    'dailywage_module_dailywagewallet',
    'individual_module_individualwallet',
    'couple_module_couplewallet',
    'retiree_module_retireewallet'
]

for table in tables:
    try:
        cursor.execute(f'SELECT id, balance FROM {table}')
        rows = cursor.fetchall()
        print(f'\n{table}:')
        for row in rows:
            balance = row[1]
            if balance is not None:
                try:
                    # Try to convert to float to check if it's valid
                    float(balance)
                    print(f'  ID: {row[0]}, Balance: {balance}')
                except (ValueError, TypeError):
                    print(f'  ID: {row[0]}, Balance: {repr(balance)} (CORRUPTED)')
            else:
                print(f'  ID: {row[0]}, Balance: None')
    except sqlite3.OperationalError as e:
        print(f'Error querying {table}: {e}')

conn.close()
>>>>>>> 55200c0a8f7e0485a48f0d7a7743dfe177e6f868
=======
import os, sys, django
sys.path.insert(0, os.path.join('.', 'IBET'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings_testing_final')
django.setup()
from django.db import connection
cursor = connection.cursor()

# Check all wallet tables for corrupted balances
tables = [
    'dailywage_module_dailywagewallet',
    'individual_module_individualwallet',
    'couple_module_couplewallet',
    'retiree_module_retireewallet',
    'student_module_wallet'
]

for table in tables:
    try:
        cursor.execute(f'SELECT id, balance FROM {table}')
        rows = cursor.fetchall()
        print(f'\n{table}:')
        corrupted_count = 0
        for row in rows:
            balance = row[1]
            if balance is not None:
                try:
                    # Try to convert to float to check if it's valid
                    float(balance)
                    print(f'  ID: {row[0]}, Balance: {balance}')
                except (ValueError, TypeError):
                    print(f'  ID: {row[0]}, Balance: {repr(balance)} (CORRUPTED)')
                    corrupted_count += 1
            else:
                print(f'  ID: {row[0]}, Balance: None')
        if corrupted_count > 0:
            print(f'  Found {corrupted_count} corrupted balances in {table}')
    except Exception as e:
        print(f'Error querying {table}: {e}')
=======
import sqlite3

conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()

# Check all wallet tables for corrupted balances
tables = [
    'dailywage_module_dailywagewallet',
    'individual_module_individualwallet',
    'couple_module_couplewallet',
    'retiree_module_retireewallet'
]

for table in tables:
    try:
        cursor.execute(f'SELECT id, balance FROM {table}')
        rows = cursor.fetchall()
        print(f'\n{table}:')
        for row in rows:
            balance = row[1]
            if balance is not None:
                try:
                    # Try to convert to float to check if it's valid
                    float(balance)
                    print(f'  ID: {row[0]}, Balance: {balance}')
                except (ValueError, TypeError):
                    print(f'  ID: {row[0]}, Balance: {repr(balance)} (CORRUPTED)')
            else:
                print(f'  ID: {row[0]}, Balance: None')
    except sqlite3.OperationalError as e:
        print(f'Error querying {table}: {e}')

conn.close()
>>>>>>> 55200c0a8f7e0485a48f0d7a7743dfe177e6f868
