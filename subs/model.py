from sqlalchemy.schema import Column
import sqlalchemy.types

from camelot.admin.entity_admin import EntityAdmin
from camelot.core.orm import Entity
import camelot.types

from sqlalchemy import Unicode, Date, Boolean, Integer

import datetime

from camelot.admin.action.list_action import ListContextAction
from camelot.core.utils import ugettext_lazy as _
from camelot.view.art import Icon

class AddressLabels(ListContextAction):
    """Print a sheet of address labels from the selected records."""
    verbose_name= _('Print Address Labels')
    icon = Icon('tango/16x16/actions/document-print-preview.png')
    tooltip = _('Print Address Labels')

    def model_run( self, model_context ):
        iterator = model_context.get_selection()
        addresses = []
        for address in iterator:
            line_1 = "%s %s" % (address.First_Name, address.Last_Name)
            line_2 = address.Address
            line_3 = "%s, %s %s" % (address.City, address.State, address.ZIP)
            # Does the postal walk code go here somewhere?
            addresses.append((line_1, line_2, line_3))
                
        context = {'addresses': addresses}
        # TODO: Count the tuples and if above the limit per page (30? 35?), split them.
            
        from camelot.view import action_steps
        yield action_steps.PrintJinjaTemplate( template = 'templates/labels.html',
                                               context = context )

class Subscription (Entity):
    __tablename__ = "subscription"
    
    First_Name = Column(Unicode(35))
    Last_Name = Column(Unicode(35))
    Address = Column(Unicode(70), nullable = False)
    City = Column(Unicode(35), nullable = False)
    # Remember, these are unicode objects. Can't set the default to 'GA'.
    State = Column(Unicode(4), nullable = False, default = u'GA')
    ZIP = Column(Unicode(9), nullable = False)    
    
    # "File_Code" refers to which service area the ZIP code falls under.
    # Calculated columns are tough in Camelot, so I will implement it in the renewal notice.
    """File_Code = Column(Unicode(9))
    if ZIP[0:2] == '304':
        if ZIP[3:4] in ('74', '75'):
            File_Code = 'VIDALIA'
        elif ZIP[3:4] == '36':
            File_Code = 'LYONS'
        else:
            File_Code = 'OUT304'
    else:
        File_Code = 'OUTCO'"""
        
    Walk_Sequence = Column(Integer())
    Phone = Column(Unicode(20))
    Email = Column(Unicode(35))
    Start_Date = Column(Date(), default = datetime.datetime.today())
    # Default value of the start date + 365.24 days. ("years=1" is not valid, leads to bugs on leap days.)
    End_Date = Column(Date(), default = (datetime.datetime.today() + datetime.timedelta(days=365.24)))
    # These show which of the publications this subscriber receives.
    Advance = Column(Boolean)
    Clipper = Column(Boolean)
    
    class Admin(EntityAdmin):
        verbose_name = 'Subscription'
        
        list_display = [
        'First_Name', 
        'Last_Name', 
        'Address', 
        'City',
        'State',
        'ZIP', 
        'Walk_Sequence', 
        'Phone', 
        'Email', 
        'Start_Date', 
        'End_Date', 
        'Advance', 
        'Clipper'
        ]
        
        # Actions for a single record - renewal notices.
        form_actions = [
        # RenewalNotice(),
        ]
        
        # Actions encompassing the whole table or a selection of it - address labels, address lists.
        list_actions = [
        AddressLabels(),
        # AddressList(),
        ]
    
    def __Unicode__ (self):
        return self.Address
            
    """class RenewalNotice(Action):
        verbose_name = _('Renewal Notice')
    
        def model_run(self, model_context):
            from camelot.view.action_steps import PrintHtml
            import datetime
            from jinja import Environment, FileSystemLoader
            from pkg_resources import resource_filename
            import subs
            from camelot.core.conf import settings 
            fileloader = FileSystemLoader(resource_filename(subs.__name__, 'templates'))
            e = Environment(loader=fileloader)
        
            context = {
            'customer':"%s %s\n%s\n%s, %s %s"  % (subscription.FirstName, subscription.LastName, subscription.Address, 
                                              subscription.City, subscription.State, subscription.ZIP),"""


 
