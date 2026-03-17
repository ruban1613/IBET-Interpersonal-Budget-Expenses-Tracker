import sqlite3

conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()

# Fix the remaining corrupted balances
fixes = [
    ('dailywage_module_dailywagewallet', 3, 1000.00),
    ('couple_module_couplewallet', 3, 1000.00),
]

print("Fixing corrupted balances...")
for table, wallet_id, new_balance in fixes:
    cursor.execute(f'UPDATE {table} SET balance = ? WHERE id = ?', (new_balance, wallet_id))
    print(f'Fixed {table} ID {wallet_id}: balance set to {new_balance}')

conn.commit()
print('All corrupted balances fixed')

# Verify fixes
print("\nVerifying fixes...")
for table, wallet_id, new_balance in fixes:
    cursor.execute(f'SELECT id, balance FROM {table} WHERE id = ?', (wallet_id,))
    row = cursor.fetchone()
    if row:
        print(f'Verified {table} ID {wallet_id}: balance = {row[1]}')
    else:
        print(f'Error: Could not find {table} ID {wallet_id}')

conn.close()
print("Fix complete.")
