import os
import csv
from time import strptime

csv_sheet = "exported.csv"


with open('exported.csv', 'rb') as f:
    reader = csv.reader(f)
    for row in reader:


def populate():
    with open('exported.csv', 'rb') as f:
        reader = csv.reader(f)
        for row in reader:
            first = row[0]
            last = row[1]
            address = row[2] + " " + row[3] + " " + row[4] # Address, PO Box, Rural Box number.
            city = row[5]
            state = row[6]
            zip = row[7]
            # row[8] = subscription type
            end_date = strptime(row[9], "%y-%m-%e")

        add_material(name, count, location)

    

    # Print out the contents of the database... not just what you've added at this point.
    print "\nTexts:"
    for t in Text.objects.all():
        print t
    print "\nExperiments:"
    for e in Experiment.objects.all():
        print e
    print "\nMaterials:"
    for m in Material.objects.all():
        print m
    print "\nRooms:"
    for r in Room.objects.all():
        print r
    print "\nTags:"
    for t in Tag.objects.all():
        print t


# Functions to add different kinds of objects.
def add_material(name, count, location):
    m = Material.objects.get_or_create(name=name, count=count, location=location)[0]
    return m


# Start execution here!
if __name__ == '__main__':
    print "Starting inventory population script..."
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'baros.settings')
    from inventory.models import Material, Experiment, Text, Room, Tag

    populate()