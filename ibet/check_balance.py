<<<<<<< HEAD
import os, sys, django
sys.path.insert(0, os.path.join('.', 'IBET'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings_testing_final')
django.setup()
from django.db import connection
cursor = connection.cursor()

cursor.execute('SELECT id, balance FROM dailywage_module_dailywagewallet;')
rows = cursor.fetchall()
print('ID | Balance')
print('-' * 20)
for row in rows:
    print(f'{row[0]} | {row[1]}')
=======
import sqlite3

conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()
cursor.execute('SELECT id, balance FROM dailywage_module_dailywagewallet')
rows = cursor.fetchall()
print('Daily wage wallet balances:')
for row in rows:
    print(f'ID: {row[0]}, Balance: {row[1]}')
conn.close()
>>>>>>> 55200c0a8f7e0485a48f0d7a7743dfe177e6f868
