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
        plotlist = csv.reader(f, delimiter=',')
        for i, line in enumerate(plotlist):
                    first = line[0]
                    last = line[1]
                    address = line[2]
                    po_box = line[3]
                    rural_box = line[4]
                    city = line[5]
                    state = line[6]
                    zip = line[7]
                    phone = line[10]
                    email = 'NULL'
            
            # Handling dates.
                    if line[9] == '':
                            end_date = 'NULL'
                    else:
                        try:
                            end_date = datetime.datetime.strptime(line[9], "%y-%m-%d").date()
                        except ValueError:
                            end_date = 'NULL'
                    if line[8] == 'ex' or line[8] == '':
                        start_date = 'NULL'
                    else:
                        try:
                            start_date = end_date - datetime.timedelta(days=(mk_int(line[8]) / 12) * 365.24)
                        except (sqlite3.InterfaceError, TypeError, ValueError): # Possible errors: multiply by a string, multiply by a blank.
                            start_date = 'NULL'
                
                    sort_code = line[11]
                    walk_sequence = line[12]
                    city_code = line[13]
                    zone = line[14]
                    level = line[15]
                    # renewal_date = line[16]
                    advance = True
                    clipper = False
                    
            
                    record = (first, last, address, po_box, rural_box, city, state, zip, start_date, end_date, phone, email, sort_code, walk_sequence, city_code, zone, level, advance, clipper)
            
                    c.execute("INSERT INTO subscriptions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)", record)
            
conn.commit()
conn.close()
