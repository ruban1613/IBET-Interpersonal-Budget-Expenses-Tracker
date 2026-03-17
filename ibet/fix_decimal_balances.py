from django.db import connection

def fix_decimal_balances():
    cursor = connection.cursor()

    # Fix all balances in all wallet tables
    tables = [
        'dailywage_module_dailywagewallet',
        'individual_module_individualwallet',
        'couple_module_couplewallet',
        'retiree_module_retireewallet'
    ]

    for table in tables:
        try:
            cursor.execute(f'UPDATE {table} SET balance = printf("%.2f", balance)')
            print(f'Updated {table}')
        except Exception as e:
            print(f'Error updating {table}: {e}')

    connection.commit()
    print('All balances fixed')

if __name__ == '__main__':
    fix_decimal_balances()
