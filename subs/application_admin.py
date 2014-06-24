from camelot.view.art import Icon
from camelot.admin.application_admin import ApplicationAdmin
from camelot.admin.section import Section
from camelot.core.utils import ugettext_lazy as _

from subs.model import Vidalia, Lyons, Out304, Outco, VPO_Box, LPO_Box, Soperton, VC12345, LC12, Price

from camelot.core.conf import settings
import os

class MyApplicationAdmin(ApplicationAdmin):
  
    name = 'Subscriptions'
    application_url = 'github.com/hollowaytape'
    help_url = 'github.com/hollowaytape'
    author = 'Max Silbiger'
    domain = 'github.com/hollowaytape'
    
    def get_sections(self):
        return (Section( _('Subscriptions'),
                          self,
                          # Icon(os.path.join(settings.CAMELOT_MEDIA_ROOT, 'images', 'onion22.png')),
                          Icon('tango/22x22/apps/internet-news-reader.png'),
                          items = [Vidalia, Lyons, Out304, Outco, VPO_Box, LPO_Box, Soperton, VC12345, LC12]),
                Section( _('Options'),
                          self,
                          Icon('tango/22x22/categories/applications-system.png'),
                          items = [Price]))
               
    def get_icon(self):
        """:return: the :class:`camelot.view.art.Icon` that should be used for the application"""
        from camelot.view.art import Icon
        return Icon('tango/22x22/apps/onion22.png').getQIcon()
        
    def get_splashscreen(self):
        """:return: a :class:`PyQt4.QtGui.QPixmap` to be used as splash screen"""
        from camelot.view.art import Pixmap
        qpm = Pixmap('color_logo.png').getQPixmap()
        img = qpm.toImage()
        # support transparency
        if not qpm.mask(): 
            if img.hasAlphaBuffer(): bm = img.createAlphaMask() 
            else: bm = img.createHeuristicMask() 
            qpm.setMask(bm) 
        return qpm
