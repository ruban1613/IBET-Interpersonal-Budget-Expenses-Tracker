import os, sys, django
sys.path.insert(0, os.path.join('.', 'IBET'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings_testing_final')
django.setup()
from django.db import connection
cursor = connection.cursor()

cursor.execute('SELECT name FROM sqlite_master WHERE type="table" AND name LIKE "%wallet%"')
rows = cursor.fetchall()
print('Wallet tables:')
for row in rows:
    print(row[0])
