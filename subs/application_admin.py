from camelot.view.art import Icon
from camelot.admin.application_admin import ApplicationAdmin
from camelot.admin.section import Section
from camelot.core.utils import ugettext_lazy as _

from subs.model import Subscription, PO_Box, Soperton_VC12345, LC12

from camelot.core.conf import settings
import os

class MyApplicationAdmin(ApplicationAdmin):
  
    name = 'Subscriptions'
    application_url = 'github.com/hollowaytape'
    help_url = 'github.com/hollowaytape'
    author = 'Max Silbiger'
    domain = 'github.com/hollowaytape'
    
    def get_sections(self):
        from camelot.model.memento import Memento
        from camelot.model.i18n import Translation
        return (Section( _('Subscription'),
                          self,
                          # Icon(os.path.join(settings.CAMELOT_MEDIA_ROOT, 'images', 'onion22.png')),
                          Icon('tango/22x22/apps/internet-news-reader.png'),
                          items = [Subscription, PO_Box, Soperton_VC12345, LC12]),)
               
    def get_icon(self):
        """:return: the :class:`camelot.view.art.Icon` that should be used for the application"""
        from camelot.view.art import Icon
        return Icon('tango/22x22/apps/onion22.png').getQIcon()
