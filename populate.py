import os
import csv
import sqlite3
from time import strptime
import datetime

conn = sqlite3.connect('subscriptions.db')
c = conn.cursor()

# CSVs containing addresses + subscription information.
address_tables = ('Lyons.csv', 'Out304.csv', 'Outco.csv', 'Vidalia.csv')
# Containing PO Box No., City Code, Select Code, Walk Seq, Tag.
po_tables = ('LPOBoxes.csv', 'VPOBoxes.csv')
# Containing Address, Sort Code, and City RTE.
code_tables = ('Soperton.csv', 'VC12345.csv')
# Containing Addresses, Walk Seq, and City Code.
lc12 = 'LC12.csv'

for table in address_tables:
    with open(table, 'rb') as f:
        reader = csv.reader(f)
        reader.next()
        for row in reader:
            id = 'null'
            first = row[0]
            last = row[1]
            address = row[2]
            po_box = row[3]
            rural_box = row[4]
            city = row[5]
            state = row[6]
            zip = row[7]
            # subscription_type = row[8]
            phone = row[10]
            email = ""
            start_date = datetime.datetime.today()
            try:
                end_date = strptime(row[9], "%y-%m-%d")
            except ValueError:
                end_date = None
            sort_code = row[11]
            walk_sequence = row[12]
            city_code = row[13]
            zone = row[14]
            level = row[15]
            # renewal_date = row[16]
            advance = True
            clipper = False
            
            record = (id, first, last, address, po_box, rural_box, city, state, zip, start_date, end_date, phone, email, sort_code, walk_sequence, city_code, zone, level, advance, clipper)
            
            c.execute("INSERT INTO subscriptions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", record)
conn.commit()
conn.close()
