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

import os
import jinja2

from main import MySettings

from camelot.view.action_steps.print_preview import PrintHtml, PrintJinjaTemplate, PrintPreview

def chunks(l, n):
    """ Yield successive n-sized chunks from l. Used to split address lists into page-sized chunks."""
    
    for i in xrange(0, len(l), n):
        yield l[i:i+n]
        
class PrintQtWebJinjaTemplate (PrintHtml):
    from PyQt4.QtWebKit import QWebView
    from camelot.view.action_steps import PrintPreview
    from camelot.core.templates import environment
    def __init__(self,
                 template, 
                 context={},
                 environment = environment):
        self.template = environment.get_template( template )
        self.html = self.template.render( context )
        self.context = context
        super( PrintQtWebJinjaTemplate, self).__init__( self.html )
    
    def get_html( self ):
        doc = QWebView() 
        doc.setHtml(self.template.render( self.context ))
        return doc

"""class RenewalNotice(Action):
    verbose_name = _('Print Renewal Notice')
    icon = Icon('tango/16x16/actions-document-print-preview.png')
    tooltip = _('Print Renewal Notice')
    
    def model_run(self, model_context):"""
        
        
class AddressList(ListContextAction):
    """Print a list of addresses from the selected records."""
    verbose_name = _('Print Address List')
    icon = Icon('tango/16x16/actions/document-print-preview.png')
    tooltip = _('Print Address List')
    
    def model_run(self, model_context):
        iterator = model_context.get_selection()
        addresses = []
        for a in iterator:
            # For each address, create a tuple of relevant fields to place in the context dict.
            name = "%s, %s" % (a.Last_Name, a.First_Name)
            address = a.Address
            city = a.City
            state = a.State
            zip = a.ZIP
            phone = a.Phone
            email = a.Email
            addresses.append((name, address, city, state, zip, phone, email))
        context = {'addresses': addresses}
            
        JINJA_ENVIRONMENT = jinja2.Environment(autoescape=True,
                                               loader=jinja2.FileSystemLoader(os.path.join(MySettings.ROOT_DIR, 
                                               'templates')))
        
        from camelot.view import action_steps
        yield action_steps.PrintJinjaTemplate(template = 'addresses.html',
                                                         context = context,
                                                         environment = JINJA_ENVIRONMENT)

class AddressLabels(ListContextAction):
    """Print a sheet of address labels from the selected records."""
    verbose_name= _('Print Address Labels')
    icon = Icon('tango/16x16/actions/document-print-preview.png')
    tooltip = _('Print Address Labels')

    def model_run(self, model_context):
        iterator = model_context.get_selection()
        addresses = []
        for a in iterator:
            line_1 = "%s %s" % (a.First_Name, a.Last_Name)
            line_2 = a.Address
            line_3 = "%s, %s %s" % (a.City, a.State, a.ZIP)
            # Does the postal walk code go here somewhere?
            addresses.append((line_1, line_2, line_3))
        
        # Each row contains 3 addresses.
        rows = list(chunks(addresses, 3))
        # Each page contains 10 rows, or 30 addresses.
        pages = list(chunks(rows, 10))
        # The final result: a list (page) of lists (rows) of 3-tuples (addresses).
        context = {'pages': pages}    
            
        jinja_environment = jinja2.Environment(autoescape=True,
                                               loader=jinja2.FileSystemLoader(os.path.join(MySettings.ROOT_DIR, 
                                               'templates')))    
                
        qt = PrintQtWebJinjaTemplate(template = 'labels.html',
                                     context = context,
                                     environment = jinja_environment)
        yield PrintPreview(qt)                                              
                                               
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
        # RenewSixMonths(),
        # RenewTwelveMonths(),
        ]
        
        # Actions encompassing the whole table or a selection of it - address labels, address lists.
        list_actions = [
        AddressLabels(),
        AddressList(),
        ]
    
    def __Unicode__ (self):
        return self.Address