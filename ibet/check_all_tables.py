from django.db import connection
cursor = connection.cursor()

# Check all tables that might contain balance fields
print('Checking all tables with balance fields for corruption...')

# Get all table names
cursor.execute('SELECT name FROM sqlite_master WHERE type="table"')
tables = cursor.fetchall()

wallet_tables = [table[0] for table in tables if 'wallet' in table[0] or 'balance' in table[0]]
print('Found wallet/balance tables:', wallet_tables)

# Check each table for balance columns and corrupted values
for table in wallet_tables:
    print('\n=== Checking', table.upper(), '===')
    try:
        # Check if table has balance column
        cursor.execute('PRAGMA table_info(' + table + ')')
        columns = cursor.fetchall()
        balance_columns = [col[1] for col in columns if 'balance' in col[1].lower()]

        if balance_columns:
            print('Balance columns found:', balance_columns)
            for col in balance_columns:
                # Check for corrupted values
                cursor.execute('SELECT COUNT(*) FROM ' + table + ' WHERE ' + col + ' = 999999999999.99')
                count = cursor.fetchone()[0]
                if count > 0:
                    print('Found', count, 'corrupted records in', col)
                    # Show the corrupted records
                    cursor.execute('SELECT id, ' + col + ' FROM ' + table + ' WHERE ' + col + ' = 999999999999.99')
                    corrupted_rows = cursor.fetchall()
                    for row in corrupted_rows:
                        print('  ID', row[0], ':', col, '=', row[1])
                else:
                    print('No corrupted values in', col)
        else:
            print('No balance columns found')
    except Exception as e:
        print('Error checking', table, ':', e)

print('\nComprehensive check completed.')
