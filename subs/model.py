import os
import jinja2
import datetime
import calendar
import subprocess

from camelot.core.orm import Entity
from camelot.admin.entity_admin import EntityAdmin

from sqlalchemy import Unicode, Date, Boolean, Integer, Float
from sqlalchemy.schema import Column
from sqlalchemy.sql.operators import between_op

from camelot.admin.action import Action
from camelot.admin.action.list_action import ListContextAction, DeleteSelection
from camelot.core.utils import ugettext_lazy as _
from camelot.core.conf import settings

from camelot.view.art import Icon
from camelot.view.filters import EditorFilter
from camelot.view.action_steps.orm import FlushSession
from camelot.view.action_steps.print_preview import PrintHtml, PrintJinjaTemplate, PrintPreview
from camelot.view.action_steps.update_progress import UpdateProgress
from camelot.view.action_steps.open_file import OpenFile

from PyQt4.QtWebKit import QWebView
from PyQt4.QtCore import QUrl, QObject, QEventLoop, Qt, QThread
from PyQt4.QtGui import QPrinter, QApplication, QPlainTextEdit

today = datetime.date.today()
days_in_current_month = calendar.monthrange(today.year, today.month)[1]

JINJA_ENVIRONMENT = jinja2.Environment(autoescape=True,
                    loader=jinja2.FileSystemLoader(os.path.join(settings.ROOT_DIR,'templates')))

def chunks(l, n):
    """ Yield successive n-sized chunks from l. Used to split address lists into page-sized chunks."""
    for i in xrange(0, len(l), n):
        yield l[i:i+n]
               
       
def name_string(a, curtail=False):
    try:
        # Last Names sometimes have "           SR" appended onto them which breaks the labels. Split them.
        if curtail:
            return ("%s %s" % (a.First_Name, " ".join(a.Last_Name.split())))[0:21]
        else:
            return "%s %s" % (a.First_Name, " ".join(a.Last_Name.split()))
    except AttributeError:
        return "POSTAL PATRON"

def address_string(a, curtail=False):
    try:
        a = "PO BOX %s" % a.Number
    except AttributeError:
        try:
            if not a.PO_Box and not a.Rural_Box:
                a = a.Address
            elif not a.Address and not a.Rural_Box:
                a = a.PO_Box
            elif not a.Rural_Box:
                a = "%s %s" % (a.Address, a.PO_Box)
            elif not a.Address:
                a = "%s %s" % (a.PO_Box, a.Rural_Box)
            else:
                a = "%s %s %s" % (a.Address, a.PO_Box, a.Rural_Box)
        except AttributeError:
            a = a.Address

    if curtail:
        return a[0:27]
    else:
        return a

def city_state_zip_string(a, table):
    if table == "vpo_boxes":
        return "VIDALIA, GA 30475"
    elif table in ("lpo_boxes", "lc12"):
        return "LYONS, GA 30436"
    elif table == "vc12345":
        return "VIDALIA, GA 30474"
    elif table == "soperton":
        return "SOPERTON, GA 30457"
                
    else:
        return "%s, %s %s" % (a.City, a.State, a.ZIP)

def get_selection_or_collection(model_context):
    try:
        a = list(model_context.get_selection())[0]
        return list(model_context.get_selection())
    except IndexError:
        return list(model_context.get_collection())

class PrintHtmlWQ(PrintPreview):    
    # Thanks to Gonzalo from the Camelot Google Group for this image-rendering fix.
    from camelot.core.templates import environment
    def __init__ (self, template, context={}, environment=environment):
        self.document = None
        self.printer = None
        self.margin_left = None
        self.margin_top = None
        self.margin_right = None
        self.margin_bottom = None
        self.margin_unit = QPrinter.Millimeter
        self.page_size = QPrinter.Letter
        self.page_orientation = None
        
        self.template = environment.get_template(template)
        self.html = self.template.render(context)
      
    def generateDocument(self):       
        from PyQt4.QtWebKit import QWebView, QWebSettings
        if self.document:
            return
        self.document = QWebView()
       
        loop = QEventLoop()        
        self.finished = False
        self.document.loadFinished.connect(self.loadFinished)
        self.document.loadFinished.connect(loop.quit)
        baseUrl = QUrl.fromLocalFile(os.path.join(settings.ROOT_DIR, "images/"))
        self.document.setHtml(self.html, baseUrl)
        if not self.finished:
            loop.exec_()       
        
    def render(self, gui_context):
        self.generateDocument()
        return super(PrintHtmlWQ, self).render(gui_context)
                
    def loadFinished(self):
        self.finished = True
   
class PrintPlainText(PrintPreview):
    def __init__(self, text):
        self.text = text
        self.document = QPlainTextEdit()
        self.thread = QThread.currentThread()
        self.document.moveToThread(QApplication.instance().thread())

    def gui_run(self, gui_context):
        filepath = OpenFile.create_temporary_file('.txt')
        with open(filepath, "w") as text_file:
            text_file.write(self.text)
        return subprocess.call(['open', '-a', 'TextEdit', filepath])
        # return os.system("start " + filepath)

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
        collection = get_selection_or_collection(model_context)
        count = len(collection)
        subscriptions = []
        conn = model_context.session.begin()
        
        if collection[0].__tablename__ == "outco":
            q = model_context.session.query(Price).filter(Price.Type == u'Outco').first()
            price_six = format(q.Six_Months, '.2f')
            price_twelve = format(q.Twelve_Months, '.2f')
            conn.commit()
        else:
            q = model_context.session.query(Price).filter(Price.Type == u'Inco').first()
            price_six = format(q.Six_Months, '.2f')
            price_twelve = format(q.Twelve_Months, '.2f')
            conn.commit()
        
        for i, a in enumerate(collection):
            context = {}
            context['record_number'] = a.id
            context['name'] = name_string(a)
            context['address'] = address_string(a)
            context['city'], context['state'], context['zip'], context['expiration_date'] = a.City, a.State, a.ZIP, a.End_Date
            context['file_code'] = a.__tablename__.upper()
            context['price_six'], context['price_twelve'] = price_six, price_twelve
                        
            yield UpdateProgress(i, count)    
            subscriptions.append(context)
            
        pages = list(chunks(subscriptions, 3))
        context['pages'] = pages
        
        yield PrintHtmlWQ(template = "renewal_notice.html", context=context, environment=JINJA_ENVIRONMENT)
        
class AddressList(Action):
    """Print a list of addresses from the selected records."""
    verbose_name = _('Print Address List')
    icon = Icon('tango/16x16/actions/format-justify-fill.png')
    tooltip = _('Print Address List')

    def model_run(self, model_context):
        iterator = get_selection_or_collection(model_context)
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
                                               
        yield PrintHtmlWQ(template = 'addresses.html',
                              context = context,
                              environment = JINJA_ENVIRONMENT)
        
class AddressLabels(Action):
    """Print a (laser) sheet of address labels from a collection."""
    verbose_name= _('Print Labels (Laser)')
    icon = Icon('tango/16x16/actions/document-print.png')
    tooltip = _('Print Address Labels (Laser)')

    def model_run(self, model_context):
        collection = get_selection_or_collection(model_context)
        addresses = []
        count = len(collection)
        table = collection[0].__tablename__
        
        if table == "outco":
            # In OutCO, we want to count the number of addresses in each zone.
            zone_counts = {}
            for n in range(0, 9):
                zone_counts[n] = 0
        
        for i, a in enumerate(collection):
            try:
                if not a.Tag:
                    continue
            except AttributeError:
                pass
                
            left_1 = name_string(a)
            left_2 = address_string(a)
            left_3 = city_state_zip_string(a, table)
            
            # Fetch End_Date data.
            try:
                right_1 = a.End_Date
            except AttributeError:
                right_1 = ""
                
            right_2 = a.id
            
            # Fetch Mailing Stuff data.
            try:                                                 # This case includes major files and PO Boxes.
                right_3 = "%s    %s" % (a.City_Code, a.Walk_Sequence)
            
            except AttributeError:                              # LC12, VC12345, and Soperton have City RTE and Sort Code instead.
                right_3 = "%s    %s" % (a.City_RTE, a.Sort_Code)
                
            yield UpdateProgress(i, count)    
            addresses.append((left_1, left_2, left_3, right_1, right_2, right_3))
            
            # Count zones if necessary.
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
            
        yield PrintHtmlWQ(template = 'labels.html',
                          context = context,
                          environment = JINJA_ENVIRONMENT)             

class AddressLabelsDotMatrix(Action):
    """Print a (laser) sheet of address labels from the selected records."""
    verbose_name= _('Print Labels (Dot-Matrix)')
    icon = Icon('tango/16x16/actions/document-print.png')
    tooltip = _('Print Address Labels (Dot-Matrix)')

    def model_run(self, model_context):
        collection = get_selection_or_collection(model_context)
        total_document = ""
        count = 0
        table = collection[0].__tablename__

        if table == "outco":
            zone_counts = {}
            for n in range(0, 9):
                zone_counts[n] = 0
        
        for a in collection:
            try:
                if not a.Tag:
                    continue
            except AttributeError:
                pass

            name = name_string(a, curtail=True)

            try:
                end_date = str(a.End_Date)
            except AttributeError:
                end_date = ""

            name_date = name + " " + end_date

            address = address_string(a, curtail=True)
            address_id = address + str(a.id)

            city_state_zip = city_state_zip_string(a, table)
            try:
                zone = str(a.Zone)
                if table == "outco":
                    zone_counts[int(a.Zone)] += 1
            except AttributeError:
                zone = ""

            try:
                city_code = str(a.City_Code)
            except AttributeError:
                city_code = ""
            citycode_zone = city_code + zone
            
            # line_1 = Name, spaces so that the line adds up to 32char, End_Date
            line_1 = name + ((33 - (len(name_date)))*" ") + end_date + "\n"

            # line_2 = Address, spaces to ensure the line adds up to 32char, ID
            line_2 = address + ((32 - len(address_id))*" ") + str(a.id) + "\n"

            # line_3 = City, State, Zip, spaces, City_Code, spaces, Zone
            line_3a = city_state_zip + ((20 - (len(city_state_zip)))*" ")
            line_3b = ((10 - len(citycode_zone))*" ") + city_code + "  " + zone + "\n"
            line_3 = line_3a + line_3b

            contact = line_1 + line_2 + line_3 + "\n"
            
            count += 1
            total_document += contact       # Extra line break to separate the next label.
        
        # The count is displayed in the final label of the printout. So, add it to the list.
        total_document += ("Total Count: %s\n" % count)

        if table == "outco":
            for n in range(0, 3):
                total_document += ("Zone %s: %s " % (n, zone_counts[n]))
            total_document += "\n"
            for n in range(3, 6):
                total_document += ("Zone %s: %s " % (n, zone_counts[n]))
            total_document += "\n"
            for n in range(6, 9):
                total_document += ("Zone %s: %s " % (n, zone_counts[n]))


        print total_document
        yield PrintPlainText(total_document)                             
                           
 
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
        
        form_actions = [
        RenewSixMonths(),
        RenewTwelveMonths(),
        ]
        
        list_actions = [
        AddressLabels(),
        AddressLabelsDotMatrix(),
        AddressList(),
        RenewalNotice(),
        DeleteSelection()
        ]
        
        list_filter = [EditorFilter(field_name="End_Date", default_operator=between_op, default_value_1=today.replace(day=1), 
                       default_value_2=today.replace(day=days_in_current_month))]
                       
        delete_mode = 'on_confirm'
    
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
        
        form_actions = [
        RenewSixMonths(),
        RenewTwelveMonths(),
        ]
        
        list_actions = [
        AddressLabels(),
        AddressLabelsDotMatrix(),
        AddressList(),
        RenewalNotice(),
        DeleteSelection(),
        ]
		
        list_filter = [EditorFilter(field_name="End_Date", default_operator=between_op, default_value_1=today.replace(day=1), 
                       default_value_2=today.replace(day=days_in_current_month))]
                       
        delete_mode = 'on_confirm'
    
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
        
        form_actions = [
        RenewSixMonths(),
        RenewTwelveMonths(),
        ]
        
        list_actions = [
        AddressLabels(),
        AddressLabelsDotMatrix(),
        AddressList(),
        RenewalNotice(),
        DeleteSelection(),
        ]
		
        list_filter = [EditorFilter(field_name="End_Date", default_operator=between_op, default_value_1=today.replace(day=1), 
                       default_value_2=today.replace(day=days_in_current_month))]
                       
        delete_mode = 'on_confirm'
    
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
        
        form_actions = [
        RenewSixMonths(),
        RenewTwelveMonths(),
        ]
        
        list_actions = [
        AddressLabels(),
        AddressLabelsDotMatrix(),
        AddressList(),
        RenewalNotice(),
        DeleteSelection(),
        ]
		
        list_filter = [EditorFilter(field_name="End_Date", default_operator=between_op, default_value_1=today.replace(day=1), 
                       default_value_2=today.replace(day=days_in_current_month))]
                       
        delete_mode = 'on_confirm'
    
    def __Unicode__ (self):
        return self.Address
        
class LC12 (Entity):
    __tablename__ = "lc12"
    
    Address = Column(Unicode(70))
    Walk_Sequence = Column(Integer())
    City_Code = Column(Integer())
    
    class Admin(EntityAdmin):
        verbose_name = 'Lyons County 1&2'
        verbose_name_plural = 'Lyons County 1&2'
        
        list_display = [
        'Address',
        'Walk_Sequence',
        'City_Code'
        ]
        
        list_actions = [
        AddressLabels(),
        AddressLabelsDotMatrix(),
        DeleteSelection(),
        ]
        
        delete_mode = 'on_confirm'
         
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
        AddressLabels(),
        AddressLabelsDotMatrix(),
        DeleteSelection(),
        ]
        
        delete_mode = 'on_confirm'
        
class VC12345 (Entity):
    __tablename__ = "vc12345"
    
    Address = Column(Unicode(70))
    Sort_Code = Column(Integer())
    City_RTE = Column(Integer())
    
    class Admin(EntityAdmin):
        verbose_name = 'Vidalia County 12345'
        verbose_name_plural = 'Vidalia County 12345'
        
        list_display = [
        'Address',
        'Sort_Code',
        'City_RTE'
        ]
        
        list_actions = [
        AddressLabels(),
        AddressLabelsDotMatrix(),
        DeleteSelection(),
        ]
        
        delete_mode = 'on_confirm'
        
class VPO_Box (Entity):
    __tablename__ = "vpo_boxes"
    
    Number = Column(Unicode(9))
    City_Code = Column(Unicode(3))
    Select_Code = Column(Unicode(2))
    Label_Stop = Column(Boolean())
    Walk_Sequence = Column(Unicode(9))
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
        AddressLabels(),
        AddressLabelsDotMatrix(),
        DeleteSelection(),
        ]
        
        delete_mode = 'on_confirm'
        
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
        AddressLabels(),
        AddressLabelsDotMatrix(),
        DeleteSelection(),
        ]
        
        delete_mode = 'on_confirm'
       
class Price (Entity):
    __tablename__ = "price"
    
    id = Column(Integer(), primary_key=True)
    
    Type = Column(Unicode(20))
    Six_Months = Column(Float())
    Twelve_Months = Column(Float())
    
    class Admin(EntityAdmin):
        verbose_name = 'Price'
        verbose_name_plural = 'Prices'
        
        list_display = [
        'Type',
        'Six_Months',
        'Twelve_Months',
        ]
        
        delete_mode = 'on_confirm'