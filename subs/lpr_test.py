import os

printer = os.popen('lpr', 'w')
printer.write('This is a test.\n')
printer.close()

"""Full line max: 32 characters, 4 inches

Name max: 23
Address max: 23
City State Zip max: 20

Date: 8 characters always
Index: max 4 characters
City Code & Zone: 3 characters, spaces, then 1-4 characters"""

city_state_zip = "%s, %s %s" % (a.City, a.State, a.Zip)

line_1 = "%s + ((32 - (len(%s) + len(%s)))*" ") + %s\n" % (a.name, a.name, a.end_date, a.end_date)
line_2 = "%s + ((32 - (len(%s) + len(%s)))*" ") + %s\n" % (a.address, a.address, a.id, a.id)
line_3 = city_state_zip + (20 - len(city_state_zip))*" " + a.CityCode + ((10 - len(a.Zone)) * " ") + a.Zone + "\n"

printer = os.popen('lpr', 'w')
printer.write(line_1, line_2, line_3)
printer.close()