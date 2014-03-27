import os
import csv
import sqlite3
import datetime

conn = sqlite3.connect('subscriptions.db')
c = conn.cursor()

# CSVs containing addresses + subscription information.
address_tables = ('Vidalia.csv', 'Lyons.csv', 'Out304.csv', 'Outco.csv')
# Containing PO Box No., City Code, Select Code, Walk Seq, Tag.
po_tables = ('LPOBoxes.csv', 'VPOBoxes.csv')
# Containing Address, Sort Code, and City RTE.
code_tables = ('Soperton.csv', 'VC12345.csv')
# Containing Addresses, Walk Seq, and City Code.
lc12 = 'LC12.csv'

def mk_int(s):
    s = s.strip()
    return int(s) if s else 0

for table in address_tables:
    with open(table, 'rb') as f:
        reader = csv.reader(f)
        reader.next()
        for row in reader:
            first = row[0]
            last = row[1]
            address = row[2]
            po_box = row[3]
            rural_box = row[4]
            city = row[5]
            state = row[6]
            zip = row[7]
            phone = row[10]
            email = NULL
            try:
                end_date = datetime.datetime.strptime(row[9], "%y-%m-%d")
            except ValueError:
                end_date = 'NULL'
            try:
                # This can't currently handle a '' value, the provenance of which is unknown...
                start_date = end_date - datetime.timedelta(days=(mk_int(row[8]) / 12) * 365.24)
            except (sqlite3.InterfaceError, TypeError, ValueError): # Possible errors: multiply by a string, multiply by a blank.
                start_date = datetime.datetime.today()
                
            start_date = datetime.datetime.today()
            sort_code = row[11]
            walk_sequence = row[12]
            city_code = row[13]
            zone = row[14]
            level = row[15]
            # renewal_date = row[16]
            advance = True
            clipper = False
            
            record = (first, last, address, po_box, rural_box, city, state, zip, start_date, end_date, phone, email, sort_code, walk_sequence, city_code, zone, level, advance, clipper)
            
            c.execute("INSERT INTO subscriptions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL)", record)
conn.commit()
conn.close()
