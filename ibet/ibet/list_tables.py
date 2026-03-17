import sqlite3

conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()
cursor.execute('SELECT name FROM sqlite_master WHERE type="table"')
rows = cursor.fetchall()
print('Tables:')
for row in rows:
    print(row[0])
conn.close()
