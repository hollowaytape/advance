"""
    Advance Subscription Program: organizes subscription records and generates print reports.
    Copyright (C) 2014, 2015 Max Silbiger.

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import sqlite3

conn = sqlite3.connect('subscriptions.db')

c = conn.cursor()
c.execute('''ALTER TABLE authentication_mechanism ADD COLUMN representation character varying;''')

conn.commit()
conn.close()