"""
    Advance Subscription Program: organizes subscription records and generates print reports.
    Copyright (C) 2014, 2015 Max Silbiger.

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

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
