import sqlite3

conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()

# Get all tables
print('=== All Tables ===')
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
for t in tables:
    print(f'  {t[0]}')

# Check student transactions
print('\n=== Student Transactions ===')
try:
    cursor.execute('SELECT * FROM student_module_transaction LIMIT 10')
    rows = cursor.fetchall()
    for row in rows:
        print(f'  {row}')
except Exception as e:
    print(f'Error: {e}')

# Get table info for student_module_wallet
print('\n=== Student Wallet Table Info ===')
cursor.execute('PRAGMA table_info(student_module_wallet)')
columns = cursor.fetchall()
for col in columns:
    print(f'  {col}')

conn.close()
