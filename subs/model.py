from sqlalchemy.schema import Column
import sqlalchemy.types

from camelot.admin.entity_admin import EntityAdmin
from camelot.core.orm import Entity
import camelot.types

from sqlalchemy import Unicode, Date, Boolean, Integer

import datetime

from camelot.admin.action import Action
from camelot.admin.action.list_action import ListContextAction
from camelot.core.utils import ugettext_lazy as _
from camelot.view.art import Icon

import os
import jinja2

from main import MySettings

from camelot.view.action_steps.print_preview import PrintHtml, PrintJinjaTemplate, PrintPreview
from PyQt4.QtWebKit import QWebView, QWebPage

def chunks(l, n):
    """ Yield successive n-sized chunks from l. Used to split address lists into page-sized chunks."""

    for i in xrange(0, len(l), n):
        yield l[i:i+n]
        
class GetJinjaHtml (PrintHtml):
    from camelot.view.action_steps import PrintPreview
    from camelot.core.templates import environment
    def __init__(self,
                 template, 
                 context={},
                 environment = environment):
        self.template = environment.get_template( template )
        self.html = self.template.render( context )
        self.context = context
        super( GetJinjaHtml, self).__init__( self.html )
    
    def get_html( self ):
        doc = QWebView() 
        doc.setHtml(self.template.render( self.context ))
        return doc
        
class WebKitPrintPreview(PrintPreview):
    """create webview in gui thread to make use of QPixmaps"""
    def __init__(self,  html):
        # create a non-widget object that can be passed to init and moved to another thread
        self.dummy =  QWebPage() 
        super(WebKitPrintPreview, self).__init__(document=self.dummy )
        self.html = html
        
    def gui_run(self,  gui_context):
        self.document =  QWebView()
        self.document.setHtml(self.html )        
        self.document.settings().PrintElementBackgrounds=True

        super(WebKitPrintPreview, self).gui_run(gui_context)

# Eventually I'd like to collapse SixMonths and TwelveMonths into one class that takes a "t" arg.
class RenewSixMonths(Action):
    verbose_name = _('Renew 6 Months')
    icon = Icon('tango/16x16/actions-document-print-preview.png')
    tooltip = verbose_name
    
    def model_run(self, model_context):
        sub = model_context.get_object()
        renewal_days = 0.5 * 365.24 # Six months.
        sub.EndDate += datetime.timedelta(days=renewal_days)
        
class RenewTwelveMonths(Action):
    verbose_name = _('Renew 1 Year')
    icon = Icon('tango/16x16/actions-document-print-preview.png')
    tooltip = verbose_name
    
    def model_run(self, model_context):
        sub = model_context.get_object()
        renewal_days = 365.24 # One year.
        sub.EndDate += datetime.timedelta(days=renewal_days)

class RenewalNotice(Action):
    verbose_name = _('Print Renewal Notice')
    icon = Icon('tango/16x16/actions-document-print-preview.png')
    tooltip = _('Print Renewal Notice')
    
    def model_run(self, model_context):
        sub = model_context.get_object()
        context = {}
        
        context['name'] = "%s %s" % (sub.First_Name, sub.Last_Name)
        context['address'] = "%s %s %s" % (a.Address, a.PO_Box, a.Rural_Box)
        context['city'] = sub.City
        context['state'] = sub.State
        context['zip'] = sub.ZIP
        context['expiration_date'] = sub.End_Date
        # File Code determines the price, and is based on the ZIP code.
        # 30475 & 30475 are Vidalia, 30436 is Lyons, 304** is Out304, else is OutCo.
        if sub.ZIP[0:2] == '304':
            if sub.ZIP[3:4] in ('74', '75'):
                context['file_code'] = 'VIDALIA'
            elif sub.ZIP[3:4] == '36':
                context['file_code'] = 'LYONS'
            else:
                context['file_code'] = 'OUT304'
        else:
            context['file_code'] = 'OUTCO'
        
        # Eventually I'll want to pull these prices from an editable table instead of hard-coding them.
        if context['file_code'] == 'OUTCO':
            context['price_six'] = 27.50
            context['price_twelve'] = 45.00
        else:
            context['price_six'] = 19.50
            context['price_twelve'] = 30.00
            
        jinja_environment = jinja2.Environment(autoescape=True,
                                               loader=jinja2.FileSystemLoader(os.path.join(MySettings.ROOT_DIR, 
                                               'templates')))
                                               
        qt = GetJinjaHtml(template = 'renewal_notice.html',
                          context = context,
                          environment = jinja_environment)
        html = qt.get_html()
        yield PrintPreview(html) 
        
class AddressList(ListContextAction):
    """Print a list of addresses from the selected records."""
    verbose_name = _('Print Address List')
    icon = Icon('tango/16x16/actions/format-justify-full.png')
    tooltip = _('Print Address List')
    
    def model_run(self, model_context):
        iterator = model_context.get_selection()
        addresses = []
        for a in iterator:
            # For each address, create a tuple of relevant fields to place in the context dict.
            name = "%s %s" % (a.First_Name, a.Last_Name)
            address = "%s %s %s" % (a.Address, a.PO_Box, a.Rural_Box)
            city = a.City
            state = a.State
            zip = a.ZIP
            phone = a.Phone
            email = a.Email
            
            addresses.append((name, address, city, state, zip, phone, email))
        context = {'addresses': addresses}
            
        jinja_environment = jinja2.Environment(autoescape=True,
                                               loader=jinja2.FileSystemLoader(os.path.join(MySettings.ROOT_DIR, 
                                               'templates')))
        
        qt = GetJinjaHtml(template = 'addresses.html',
                          context = context,
                          environment = jinja_environment)
        html = qt.get_html()
        yield PrintPreview(html)                   

class AddressLabels(ListContextAction):
    """Print a sheet of address labels from the selected records."""
    verbose_name= _('Print Address Labels')
    icon = Icon('tango/16x16/actions/document-print.png')
    tooltip = _('Print Address Labels')

    def model_run(self, model_context):
        iterator = model_context.get_selection()
        addresses = []
        for a in iterator:
            line_1 = "%s %s" % (a.First_Name, a.Last_Name)
            line_2 = "%s %s %s" % (a.Address, a.PO_Box, a.Rural_Box)
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
                

        # Render the jinja template + context as HTML.
        # Pass it to WebKitPrintPreview as the html argument.
        qt = GetJinjaHtml(template = 'labels.html',
                          context = context,
                          environment = jinja_environment)
        html = qt.get_html()
        yield PrintPreview(html)                                          

class PO_Box (Entity):
    __tablename__ = "po_boxes"
    
    Number = Column(Unicode(9))
    City_Code = Column(Unicode(3))
    Select_Code = Column(Unicode(2))
    Walk_Sequence = Column(Integer())
    Tag = Column(Boolean())
    
    class Admin(EntityAdmin):
        verbose_name = 'PO Box'
        
        list_display = [
        'Number',
        'City_Code',
        'Select_Code',
        'Walk_Sequence',
        'Tag',
        ]
        
class Subscription (Entity):
    __tablename__ = "subscriptions"
    
    First_Name = Column(Unicode(35))
    Last_Name = Column(Unicode(35))
    Address = Column(Unicode(70))
    # PO_Box either stores Line 2 of the address (apt #, etc) or specifies that it's a PO Box, with the number in Rural_Box.
    PO_Box = Column(Unicode(30))
    Rural_Box = Column(Unicode(30))
    City = Column(Unicode(35), nullable=False, default=u'VIDALIA')
    # Remember, these are unicode objects. Can't set the default to 'GA'.
    State = Column(Unicode(4), nullable=False, default = u'GA')
    ZIP = Column(Unicode(9))  
    
    Phone = Column(Unicode(20))
    Email = Column(Unicode(35))
    
    Start_Date = Column(Date(), default = datetime.datetime.today())
    # Default value of the start date + 365.24 days. ("years=1" is not valid, leads to bugs on leap days.)
    End_Date = Column(Date(), default = (datetime.datetime.today() + datetime.timedelta(days=365.24)))
    
    Sort_Code = Column(Integer())
    Walk_Sequence = Column(Unicode(5))
    City_Code = Column(Unicode(5))
    Zone = Column(Unicode(5))
    Level = Column(Unicode(5))
    
    Advance = Column(Boolean(), default=True)
    Clipper = Column(Boolean(), default=False)
    
    
    
    class Admin(EntityAdmin):
        verbose_name = 'Subscription'
        
        list_display = [
        'First_Name', 
        'Last_Name', 
        'Address', 
        'PO_Box',
        'Rural_Box',
        'City',
        'State',
        'ZIP', 
        'Phone', 
        'Email',  
        'Start_Date',
        'End_Date', 
        'Sort_Code',
        'Walk_Sequence', 
        'City_Code',
        'Zone',
        'Level'
        ]
        force_columns_width = [20, 20, 40, 10, 10, 15, 5, 10, 15, 15, 20, 20, 10, 10, 10, 10, 10]
        
        # Actions for a single record - renewal notices.
        form_actions = [
        RenewalNotice(),
        RenewSixMonths(),
        RenewTwelveMonths(),
        ]
        
        # Actions encompassing the whole table or a selection of it - address labels, address lists.
        list_actions = [
        AddressLabels(),
        AddressList(),
        ]
    
    def __Unicode__ (self):
        return self.Address