import sqlite3

conn = sqlite3.connect('subscriptions.db')

c = conn.cursor()
c.execute('''ALTER TABLE authentication_mechanism ADD COLUMN representation character varying;''')

conn.commit()
conn.close()