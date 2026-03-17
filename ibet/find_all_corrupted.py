import os, sys, django
sys.path.insert(0, os.path.join('.', 'IBET'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings_testing_final')
django.setup()
from django.db import connection
cursor = connection.cursor()

# Check dailywage wallets
cursor.execute('SELECT id, balance FROM dailywage_module_dailywagewallet WHERE balance > 999999999999.99')
rows = cursor.fetchall()
print(f'Found {len(rows)} corrupted dailywage wallets:')
for row in rows:
    print(f'ID {row[0]}: {row[1]}')

# Check couple wallets
cursor.execute('SELECT id, balance FROM couple_module_couplewallet WHERE balance > 999999999999.99')
rows = cursor.fetchall()
print(f'Found {len(rows)} corrupted couple wallets:')
for row in rows:
    print(f'ID {row[0]}: {row[1]}')

# Check individual wallets
cursor.execute('SELECT id, balance FROM individual_module_individualwallet WHERE balance > 999999999999.99')
rows = cursor.fetchall()
print(f'Found {len(rows)} corrupted individual wallets:')
for row in rows:
    print(f'ID {row[0]}: {row[1]}')

# Check retiree wallets
cursor.execute('SELECT id, balance FROM retiree_module_retireewallet WHERE balance > 999999999999.99')
rows = cursor.fetchall()
print(f'Found {len(rows)} corrupted retiree wallets:')
for row in rows:
    print(f'ID {row[0]}: {row[1]}')

# Check student wallets
cursor.execute('SELECT id, balance FROM student_module_wallet WHERE balance > 999999999999.99')
rows = cursor.fetchall()
print(f'Found {len(rows)} corrupted student wallets:')
for row in rows:
    print(f'ID {row[0]}: {row[1]}')
