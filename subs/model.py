import os
import jinja2
import datetime
import calendar
import datetime

from sqlalchemy.schema import Column
import sqlalchemy.types

from camelot.admin.entity_admin import EntityAdmin
from camelot.core.orm import Entity
import camelot.types

from sqlalchemy import Unicode, Date, Boolean, Integer

from camelot.admin.action import Action, ActionStep
from camelot.admin.action.list_action import ListContextAction, DeleteSelection
from camelot.core.utils import ugettext_lazy as _
from camelot.core.conf import settings
from camelot.view.art import Icon

from camelot.view.model_thread import get_model_thread
from camelot.view.action_steps.orm import FlushSession, DeleteObject
from camelot.view.action_steps.print_preview import PrintHtml, PrintJinjaTemplate, PrintPreview
from PyQt4.QtWebKit import QWebPage, QWebView
from PyQt4.QtCore import QUrl, QFile, QObject

from camelot.view.filters import EditorFilter
from sqlalchemy.sql.operators import between_op

today = datetime.date.today()
days_in_current_month = calendar.monthrange(today.year, today.month)[1]

def chunks(l, n):
    """ Yield successive n-sized chunks from l. Used to split address lists into page-sized chunks."""
    for i in xrange(0, len(l), n):
        yield l[i:i+n]
        
class RenderJinjaHtml(PrintPreview):
    from camelot.core.templates import environment
    def __init__(self,
                 template, 
                 context={},
                 environment = environment):
        self.template = environment.get_template(template)
        self.html = self.template.render(context)
        self.context = context
    
    def gui_run(self, gui_context):
        self.document = QWebView()
        super(RenderJinjaHtml, self).__init__(document=self.document)
        # Qt needs a baseUrl with a trailing slash, so we can't just use CAMELOT_MEDIA_ROOT.
        baseUrl = QUrl.fromLocalFile(os.path.join(settings.ROOT_DIR, "images/"))
        self.document.setHtml(self.html, baseUrl)
        
        # Images do not render the first time. Maybe rendering it twice before returning it will solve this?
        del self.document
        self.document = QWebView()
        super(RenderJinjaHtml, self).__init__(document=self.document)
        self.document.setHtml(self.html, baseUrl)
        
        super(RenderJinjaHtml, self).gui_run(gui_context)
       
class RenewSixMonths(Action):
    verbose_name = _('Renew 6 Months')
    icon = Icon('tango/16x16/actions-document-print-preview.png')
    tooltip = verbose_name
    
    def model_run(self, model_context):
        sub = model_context.get_object()
        renewal_days = 0.5 * 365.24 # Six months.
        sub.End_Date += datetime.timedelta(days=renewal_days)
        yield FlushSession( model_context.session )
        
class RenewTwelveMonths(Action):
    verbose_name = _('Renew 1 Year')
    icon = Icon('tango/16x16/actions-document-print-preview.png')
    tooltip = verbose_name
    
    def model_run(self, model_context):
        sub = model_context.get_object()
        renewal_days = 365.24 # One year.
        sub.End_Date += datetime.timedelta(days=renewal_days)
        yield FlushSession( model_context.session )

class RenewalNotice(Action):
    verbose_name = _('Print Renewal Notices')
    icon = Icon('tango/16x16/actions/document-print-preview.png')
    tooltip = _('Print Renewal Notices')
    
    def model_run(self, model_context):
        # iterator = model_context.get_selection() # Would allow the selection of certain groups. Client wants the whole table selected.
        iterator = model_context.get_collection()
        addresses = []
        
        for a in iterator:
            context = {}
            context['record_number'] = a.id
            
            context['name'] = "%s %s" % (a.First_Name, a.Last_Name)
            if a.PO_Box is None and a.Rural_Box is None:
                context['address'] = a.Address
            elif a.Rural_Box is None:
                context['address'] = "%s %s" % (a.Address, a.PO_Box)
            elif a.Address is None:
                context['address'] = "%s %s" % (a.PO_Box, a.Rural_Box)
            else:
                context['address'] = "%s %s %s" % (a.Address, a.PO_Box, a.Rural_Box)
                
            context['city'] = a.City
            context['state'] = a.State
            context['zip'] = a.ZIP
            context['expiration_date'] = a.End_Date
            context['file_code'] = a.__tablename__.upper()

        
        # Eventually I'll want to pull these prices from an editable table instead of hard-coding them.
            if context['file_code'] == 'outco':
                context['price_six'] = "32.50"
                context['price_twelve'] = "50.00"
            else:
                context['price_six'] = "24.50"
                context['price_twelve'] = "35.00"
            addresses.append(context)
            
        context = {'addresses' : addresses}
            
        jinja_environment = jinja2.Environment(autoescape=True,
                                               loader=jinja2.FileSystemLoader(os.path.join(settings.ROOT_DIR, 
                                               'templates')))
                                               
        yield RenderJinjaHtml(template = 'renewal_notice.html',
                              context = context,
                              environment = jinja_environment)
        
class AddressList(Action):
    """Print a list of addresses from the selected records."""
    verbose_name = _('Print Address List')
    icon = Icon('tango/16x16/actions/format-justify-fill.png')
    tooltip = _('Print Address List')

    def model_run(self, model_context):
        iterator = model_context.get_collection()
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
            sort = a.Sort_Code
            walk = a.Walk_Sequence
            city_code = a.City_Code
            zone = a.Zone
            level = a.Level
            
            addresses.append((name, address, city, state, zip, phone, email, sort, walk, city_code, zone, level))
            
        pages = list(chunks(addresses, 32))
        context = {'pages': pages}
        jinja_environment = jinja2.Environment(autoescape=True,
                                               loader=jinja2.FileSystemLoader(os.path.join(settings.ROOT_DIR, 
                                               'templates')))
                                               
        yield RenderJinjaHtml(template = 'addresses.html',
                              context = context,
                              environment = jinja_environment)
        
class AddressLabels(Action):
    """Print a (laser) sheet of address labels from the selected records."""
    verbose_name= _('Print Labels (Laser)')
    icon = Icon('tango/16x16/actions/document-print.png')
    tooltip = _('Print Address Labels (Laser)')

    def model_run(self, model_context):
        iterator = model_context.get_collection()
        addresses = []
        count = 0
        
        # Check the table name through the iterator's first entry, to minimize db queries and determine biz rules.
        table = iterator.next().__tablename__
        
        if table == "outco":
            # In OutCO, we want to count the number of addresses in each zone.
            zone_counts = {}
            # There are zones from 0 to 8.
            for n in range(0, 9):
                zone_counts[n] = 0
        
        for a in iterator:
            try:
                # Last Names sometimes have "           SR" appended onto them which breaks the labels. Split them.
                line_1 = "%s %s" % (a.First_Name, " ".join(a.Last_Name.split()))
            except AttributeError:
                line_1 = "POSTAL PATRON"
                
            try:
                line_2 = "%s %s %s" % (a.Address, a.PO_Box, a.Rural_Box)
            except AttributeError:
                try:
                    line_2 = a.Address
                except AttributeError:
                    line_2 = "PO BOX %s" % a.Number
            
            if table == "vpo_boxes":
                if a.Tag == False:
                    continue
                line_3 = "VIDALIA, GA 30475"
            elif table == "vc12345":
                line_3 = "VIDALIA, GA 30474"
                
            elif table == "lpo_boxes":
                if a.Tag == False:
                    continue
                line_3 = "LYONS, GA 30436"
            elif table == "lc12":
                line_3 = "LYONS, GA 30436"
                
            elif table == "soperton":
                line_3 = "SOPERTON, GA 30457"
                
            else:
                line_3 = "%s, %s %s" % (a.City, a.State, a.ZIP)
            
            try:
                right_1 = a.End_Date
            except AttributeError:
                right_1 = ""
                
            right_2 = a.id
            
            try:
            # This case includes major files and PO Boxes.
                right_3 = "%s    %s" % (a.City_Code, a.Walk_Sequence)
            # LC12, VC12345, and Soperton have City RTE and Sort Code instead.
            except AttributeError: 
                right_3 = "%s    %s" % (a.City_RTE, a.Sort_Code)
                
            addresses.append((line_1, line_2, line_3, right_1, right_2, right_3))
            count += 1
            
            if table == "outco":
                zone_counts[int(a.Zone)] += 1
        
        # The count is displayed in the final label of the printout. So, add it to the list.
        if table == "outco":
            addresses.append(('Count: %s' % count, 'Zone 0: %s' % zone_counts[0], 'Zone 1: %s' % zone_counts[1], 
                              'Zone 2: %s' % zone_counts[2], 'Zone 3: %s' % zone_counts[3], 'Zone 4: %s' % zone_counts[4]))
        
            addresses.append(('Zone 5: %s' % zone_counts[5], 'Zone 6: %s' % zone_counts[6], 'Zone 7: %s' % zone_counts[7], 
                              'Zone 8: %s' % zone_counts[8], '', ''))                
        else:
            addresses.append(('Count:', '', '', count, '', ''))
        
        # Each row contains 3 addresses.
        rows = list(chunks(addresses, 3))
        # Each page contains 10 rows, or 30 addresses.
        pages = list(chunks(rows, 10))
        # The final result: a list (page) of lists (rows) of 3-tuples (addresses).
        context = {'pages': pages}
            
        jinja_environment = jinja2.Environment(autoescape=True,
                                               loader=jinja2.FileSystemLoader(os.path.join(settings.ROOT_DIR, 
                                               'templates')))    

        yield RenderJinjaHtml(template = 'labels.html',
                              context = context,
                              environment = jinja_environment)             

class AddressLabelsDotMatrix(Action):
    """Print a (laser) sheet of address labels from the selected records."""
    verbose_name= _('Print Labels (Dot-Matrix)')
    icon = Icon('tango/16x16/actions/document-print.png')
    tooltip = _('Print Address Labels (Dot-Matrix)')

    def model_run(self, model_context):
        iterator = model_context.get_collection()
        addresses = []
        count = 0
        
        for a in iterator:
            # Last Names sometimes have "           SR" appened onto them which breaks the labels. Split them.
            line_1 = "%s %s" % (a.First_Name, " ".join(a.Last_Name.split()))
            line_2 = "%s %s %s" % (a.Address, a.PO_Box, a.Rural_Box)
            line_3 = "%s, %s %s" % (a.City, a.State, a.ZIP)
            
            right_1 = a.End_Date
            right_2 = a.id
            right_3 = "%s   %s" % (a.City_Code, a.Walk_Sequence)
            addresses.append((line_1, line_2, line_3, right_1, right_2, right_3))
            count += 1
        
        # The count is displayed in the final label of the printout. So, add it to the list.
        addresses.append(('Count:', '', '', count, '', ''))
        
        # Each page contains 11 labels.
        pages = list(chunks(addresses, 11))
        # The final result: a list (pages) of rows (labels).
        context = {'pages': pages}    
            
        jinja_environment = jinja2.Environment(autoescape=True,
                                               loader=jinja2.FileSystemLoader(os.path.join(settings.ROOT_DIR, 
                                               'templates')))    

        yield RenderJinjaHtml(template = 'labels_dotmatrix.html',
                              context = context,
                              environment = jinja_environment)                                        
                           

class LC12 (Entity):
    __tablename__ = "lc12"
    
    Address = Column(Unicode(70))
    Walk_Sequence = Column(Integer())
    City_Code = Column(Integer())
    
    class Admin(EntityAdmin):
        verbose_name = 'LC12'
        verbose_name_plural = 'LC12'
        
        list_display = [
        'Address',
        'Walk_Sequence',
        'City_Code'
        ]
        
        list_actions = [
        DeleteSelection(),
        AddressLabels(),
        AddressLabelsDotMatrix(),
        ]
        
        
class Soperton (Entity):
    __tablename__ = "soperton"
    
    Address = Column(Unicode(70))
    Sort_Code = Column(Integer())
    City_RTE = Column(Integer())
    
    class Admin(EntityAdmin):
        verbose_name = 'Soperton'
        verbose_name_plural = 'Soperton'
        
        list_display = [
        'Address',
        'Sort_Code',
        'City_RTE'
        ]
        
        list_actions = [
        DeleteSelection(),
        AddressLabels(),
        AddressLabelsDotMatrix(),
        ]
        
        
class VC12345 (Entity):
    __tablename__ = "vc12345"
    
    Address = Column(Unicode(70))
    Sort_Code = Column(Integer())
    City_RTE = Column(Integer())
    
    class Admin(EntityAdmin):
        verbose_name = 'VC12345'
        verbose_name_plural = 'VC12345'
        
        list_display = [
        'Address',
        'Sort_Code',
        'City_RTE'
        ]
        
        list_actions = [
        DeleteSelection(),
        AddressLabels(),
        AddressLabelsDotMatrix(),
        ]
        

class VPO_Box (Entity):
    __tablename__ = "vpo_boxes"
    
    Number = Column(Unicode(9))
    City_Code = Column(Unicode(3))
    Select_Code = Column(Unicode(2))
    Label_Stop = Column(Boolean())
    Walk_Sequence = Column(Integer())
    Tag = Column(Boolean())
    
    class Admin(EntityAdmin):
        verbose_name = 'Vidalia P.O. Box'
        verbose_name_plural = 'Vidalia P.O. Boxes'
        
        list_display = [
        'Number',
        'City_Code',
        'Select_Code',
        'Walk_Sequence',
        'Tag',
        ]
        
        list_actions = [
        DeleteSelection(),
        AddressLabels(),
        AddressLabelsDotMatrix(),
        ]
        
        
class LPO_Box (Entity):
    __tablename__ = "lpo_boxes"
    
    Number = Column(Unicode(9))
    City_Code = Column(Unicode(3))
    Select_Code = Column(Unicode(2))
    Label_Stop = Column(Boolean())
    Walk_Sequence = Column(Integer())
    Tag = Column(Boolean())
    
    class Admin(EntityAdmin):
        verbose_name = 'Lyons P.O. Box'
        verbose_name_plural = 'Lyons P.O. Boxes'
        
        list_display = [
        'Number',
        'City_Code',
        'Select_Code',
        'Walk_Sequence',
        'Tag',
        ]
        
        list_actions = [
        DeleteSelection(),
        AddressLabels(),
        AddressLabelsDotMatrix(),
        ]
        

class Vidalia (Entity):
    __tablename__ = "vidalia"
    
    id = Column(Integer(), primary_key=True)
    
    First_Name = Column(Unicode(35))
    Last_Name = Column(Unicode(35))
    Address = Column(Unicode(70))
    # PO_Box either stores Line 2 of the address (apt #, etc) or specifies that it's a PO Box, with the number in Rural_Box.
    PO_Box = Column(Unicode(30))
    Rural_Box = Column(Unicode(30))
    City = Column(Unicode(35), default=u'VIDALIA')
    # Remember, these are unicode objects. Can't set the default to 'GA'.
    State = Column(Unicode(4), default = u'GA')
    ZIP = Column(Unicode(9))  
    
    Phone = Column(Unicode(20))
    Email = Column(Unicode(35), nullable=True)
    
    Start_Date = Column(Date(), default = datetime.datetime.today(), nullable=True)
    # Default value of the start date + 365.24 days. ("years=1" is not valid, leads to bugs on leap days.)
    End_Date = Column(Date(), default = (datetime.datetime.today() + datetime.timedelta(days=365.24)), nullable=True)
    
    Sort_Code = Column(Integer())
    Walk_Sequence = Column(Integer())
    City_Code = Column(Unicode(5))
    Zone = Column(Unicode(5))
    Level = Column(Unicode(5))
    
    Advance = Column(Boolean(), default=True)
    Clipper = Column(Boolean(), default=False)
    
    
    class Admin(EntityAdmin):
        verbose_name = 'Vidalia'
        verbose_name_plural = 'Vidalia'
        
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
        
        # Actions for a single record - renewal actions.
        form_actions = [
        RenewSixMonths(),
        RenewTwelveMonths(),
        ]
        
        # Actions encompassing the whole table or a selection of it - address labels, address lists, notices.
        list_actions = [
        AddressLabels(),
        AddressLabelsDotMatrix(),
        AddressList(),
        RenewalNotice(),
        DeleteSelection()
        ]
        
        list_filter = [EditorFilter(field_name="End_Date", default_operator=between_op, default_value_1=today.replace(day=1), 
                       default_value_2=today.replace(day=days_in_current_month))]
    
    def __Unicode__ (self):
        return self.Address
        
class Lyons (Entity):
    __tablename__ = "lyons"
    
    id = Column(Integer(), primary_key=True)
    
    First_Name = Column(Unicode(35))
    Last_Name = Column(Unicode(35))
    Address = Column(Unicode(70))
    # PO_Box either stores Line 2 of the address (apt #, etc) or specifies that it's a PO Box, with the number in Rural_Box.
    PO_Box = Column(Unicode(30))
    Rural_Box = Column(Unicode(30))
    City = Column(Unicode(35), default=u'LYONS')
    # Remember, these are unicode objects. Can't set the default to 'GA'.
    State = Column(Unicode(4), default = u'GA')
    ZIP = Column(Unicode(9))  
    
    Phone = Column(Unicode(20))
    Email = Column(Unicode(35), nullable=True)
    
    Start_Date = Column(Date(), default = datetime.datetime.today(), nullable=True)
    # Default value of the start date + 365.24 days. ("years=1" is not valid, leads to bugs on leap days.)
    End_Date = Column(Date(), default = (datetime.datetime.today() + datetime.timedelta(days=365.24)), nullable=True)
    
    Sort_Code = Column(Integer())
    Walk_Sequence = Column(Integer())
    City_Code = Column(Unicode(5))
    Zone = Column(Unicode(5))
    Level = Column(Unicode(5))
    
    Advance = Column(Boolean(), default=True)
    Clipper = Column(Boolean(), default=False)
    
    
    
    class Admin(EntityAdmin):
        verbose_name = 'Lyons'
        verbose_name_plural = 'Lyons'
        
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
        
        # Actions for a single record - renewal actions.
        form_actions = [
        RenewSixMonths(),
        RenewTwelveMonths(),
        ]
        
        # Actions encompassing the whole table or a selection of it - address labels, address lists, notices.
        list_actions = [
        AddressLabels(),
        AddressLabelsDotMatrix(),
        AddressList(),
        RenewalNotice(),
        DeleteSelection(),
        ]
		
        list_filter = [EditorFilter(field_name="End_Date", default_operator=between_op, default_value_1=today.replace(day=1), 
                       default_value_2=today.replace(day=days_in_current_month))]
    
    def __Unicode__ (self):
        return self.Address
        
class Out304 (Entity):
    __tablename__ = "out304"
    
    id = Column(Integer(), primary_key=True)
    
    First_Name = Column(Unicode(35))
    Last_Name = Column(Unicode(35))
    Address = Column(Unicode(70))
    # PO_Box either stores Line 2 of the address (apt #, etc) or specifies that it's a PO Box, with the number in Rural_Box.
    PO_Box = Column(Unicode(30))
    Rural_Box = Column(Unicode(30))
    City = Column(Unicode(35), default=u'VIDALIA')
    # Remember, these are unicode objects. Can't set the default to 'GA'.
    State = Column(Unicode(4), default = u'GA')
    ZIP = Column(Unicode(9))  
    
    Phone = Column(Unicode(20))
    Email = Column(Unicode(35), nullable=True)
    
    Start_Date = Column(Date(), default = datetime.datetime.today(), nullable=True)
    # Default value of the start date + 365.24 days. ("years=1" is not valid, leads to bugs on leap days.)
    End_Date = Column(Date(), default = (datetime.datetime.today() + datetime.timedelta(days=365.24)), nullable=True)
    
    Sort_Code = Column(Integer())
    Walk_Sequence = Column(Integer())
    City_Code = Column(Unicode(5))
    Zone = Column(Unicode(5))
    Level = Column(Unicode(5))
    
    Advance = Column(Boolean(), default=True)
    Clipper = Column(Boolean(), default=False)
    
    
    
    class Admin(EntityAdmin):
        verbose_name = 'Out304'
        verbose_name_plural = 'Out304'
        
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
        RenewSixMonths(),
        RenewTwelveMonths(),
        ]
        
        # Actions encompassing the whole table or a selection of it - address labels, address lists, notices.
        list_actions = [
        AddressLabels(),
        AddressLabelsDotMatrix(),
        AddressList(),
        RenewalNotice(),
        DeleteSelection(),
        ]
		
        list_filter = [EditorFilter(field_name="End_Date", default_operator=between_op, default_value_1=today.replace(day=1), 
                       default_value_2=today.replace(day=days_in_current_month))]
    
    def __Unicode__ (self):
        return self.Address
        
class Outco (Entity):

    __tablename__ = "outco"
    
    id = Column(Integer(), primary_key=True)
    
    First_Name = Column(Unicode(35))
    Last_Name = Column(Unicode(35))
    Address = Column(Unicode(70))
    # PO_Box either stores Line 2 of the address (apt #, etc) or specifies that it's a PO Box, with the number in Rural_Box.
    PO_Box = Column(Unicode(30))
    Rural_Box = Column(Unicode(30))
    City = Column(Unicode(35))
    # Remember, these are unicode objects. Can't set the default to 'GA'.
    State = Column(Unicode(4), default = u'GA')
    ZIP = Column(Unicode(9))  
    
    Phone = Column(Unicode(20))
    Email = Column(Unicode(35), nullable=True)
    
    Start_Date = Column(Date(), default = datetime.datetime.today(), nullable=True)
    # Default value of the start date + 365.24 days. ("years=1" is not valid, leads to bugs on leap days.)
    End_Date = Column(Date(), default = (datetime.datetime.today() + datetime.timedelta(days=365.24)), nullable=True)
    
    Sort_Code = Column(Integer())
    Walk_Sequence = Column(Integer())
    City_Code = Column(Unicode(5))
    Zone = Column(Unicode(5))
    Level = Column(Unicode(5))
    
    Advance = Column(Boolean(), default=True)
    Clipper = Column(Boolean(), default=False)
    
    
    
    class Admin(EntityAdmin):
        verbose_name = 'Outco'
        verbose_name_plural = 'Outco'
        
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
        RenewSixMonths(),
        RenewTwelveMonths(),
        ]
        
        # Actions encompassing the whole table or a selection of it - address labels, address lists.
        list_actions = [
        AddressLabels(),
        AddressLabelsDotMatrix(),
        AddressList(),
        RenewalNotice(),
        DeleteSelection(),
        ]
		
        list_filter = [EditorFilter(field_name="End_Date", default_operator=between_op, default_value_1=today.replace(day=1), 
                       default_value_2=today.replace(day=days_in_current_month))]
    
    def __Unicode__ (self):
        return self.Address
        