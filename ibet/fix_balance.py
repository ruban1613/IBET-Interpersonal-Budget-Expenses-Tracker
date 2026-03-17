import sqlite3

conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()

# Fix the corrupted balance
cursor.execute('UPDATE dailywage_module_dailywagewallet SET balance = 1000 WHERE id = 6')

conn.commit()
print('Fixed corrupted balance for wallet ID 6')

# Verify the fix
cursor.execute('SELECT id, balance FROM dailywage_module_dailywagewallet WHERE id = 6')
row = cursor.fetchone()
print(f'Updated balance: ID: {row[0]}, Balance: {row[1]}')

conn.close()
