class ContactsInDateRange(object):
    
    class Admin(EntityAdmin):
        verbose_name = _('Contacts in Date Range')
        list_display = table.Table( [ table.ColumnGroup( _('Name and Visitors'), ['first_name', 'last_name', 'visitors'] ),
                                      table.ColumnGroup( _('Official'), ['birthdate', 'social_security_number', 'passport_number'] ) ]
                                    )
# end column group

class DateRangeDiaog(object):

    class Admin(ObjectAdmin):
        form_close_action = setup_views(param)

def setup_views():
    from sqlalchemy.sql import select, func, and_
    from sqlalchemy.orm import mapper
 
    from subs.model import Vidalia, Lyons, OutCo, Out304
        
    s = select([Person.party_id,
                Person.first_name.label('first_name'),
                Person.last_name.label('last_name'),
                Person.birthdate.label('birthdate'),
                Person.social_security_number.label('social_security_number'),
                Person.passport_number.label('passport_number'),
                func.sum( VisitorReport.visitors ).label('visitors'),],
                whereclause = and_( c.End_Date > input_start,
                                    c.End_Date < input_end),
                group_by = [ Person.party_id, 
                             Person.first_name, 
                             Person.last_name,
                             Person.birthdate,
                             Person.social_security_number,
                             Person.passport_number, ] )
                            
    s=s.alias('contacts_in_date_range')
    
    mapper( VisitorsPerDirector, s, always_refresh=True )