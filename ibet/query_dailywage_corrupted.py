import sqlite3

conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()
cursor.execute('SELECT id, balance, weekly_target, alert_threshold FROM dailywage_module_dailywagewallet')
rows = cursor.fetchall()
print('All DailyWageWallet records:')
for row in rows:
    print('ID:', row[0], 'Balance:', row[1], 'Weekly Target:', row[2], 'Alert Threshold:', row[3])
conn.close()
