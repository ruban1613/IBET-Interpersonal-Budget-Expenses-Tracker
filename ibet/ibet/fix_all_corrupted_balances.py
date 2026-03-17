import sqlite3

conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()

# Fix corrupted balances - set them to reasonable values
fixes = [
    ('dailywage_module_dailywagewallet', 6, 1000),  # Already fixed
    ('individual_module_individualwallet', 4, 1000),  # Fix corrupted balance
]

for table, wallet_id, new_balance in fixes:
    cursor.execute(f'UPDATE {table} SET balance = ? WHERE id = ?', (new_balance, wallet_id))
    print(f'Fixed {table} ID {wallet_id}: balance set to {new_balance}')

conn.commit()
print('All corrupted balances fixed')

# Verify fixes
for table, wallet_id, new_balance in fixes:
    cursor.execute(f'SELECT id, balance FROM {table} WHERE id = ?', (wallet_id,))
    row = cursor.fetchone()
    print(f'Verified {table} ID {wallet_id}: balance = {row[1]}')

conn.close()
