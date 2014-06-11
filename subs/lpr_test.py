# TODO: Check the ()s.

import os

"""Full line max: 32 characters, 4 inches

Name max: 23
Address max: 23
City State Zip max: 20

Date: 8 characters always
Index: max 4 characters
City Code & Zone: 3 characters, spaces, then 1-4 characters"""


class Test(object):
    def __init__(self, Name, Address, City, State, Zip, End_Date, id, City_Code, Zone):
        self.Name = Name
        self.Address = Address
        self.City = City
        self.State = State
        self.Zip = str(Zip)
        self.End_Date = End_Date
        self.id = str(id)
        self.City_Code = City_Code
        self.Zone = str(Zone)

a = Test(Name = 'MAX SILBIGER', Address = '3323 SULKY CIR SE', City = 'MARIETTA', State = 'GA', Zip = '30067',
         End_Date = '05-04-2014', id = 21, City_Code = 'VC6', Zone = '8')
         
name_date = a.Name + str(a.End_Date)
address_id = a.Address + str(a.id)
         
city_state_zip = "%s, %s %s" % (a.City, a.State, a.Zip)
city_code_zone = a.City_Code + str(a.Zone)
        
# line_1 = Name, spaces so that the line adds up to 32char, End_Date
line_1 = a.Name + ((32 - (len(name_date)))*" ") + a.End_Date + "\n"

# line_2 = Address, spaces to ensure the line adds up to 32char, ID
line_2 = a.Address + ((32 - len(address_id))*" ") + a.id + "\n"

# line_3 = City, State, Zip, spaces, City_Code, spaces, Zone
line_3a = city_state_zip + ((20 - (len(city_state_zip)))*" ")
line_3b = ((10 - len(city_code_zone))*" ") + a.City_Code + "  " + a.Zone + "\n"
line_3 = line_3a + line_3b

print line_1, len(line_1)
print line_2
print line_3

printer = os.popen('lpr', 'w')
printer.write(line_1 + line_2 + line_3)
printer.close()