
from camelot.view.art import Icon
from camelot.admin.application_admin import ApplicationAdmin
from camelot.admin.section import Section
from camelot.core.utils import ugettext_lazy as _

from subs.model import Subscription

class MyApplicationAdmin(ApplicationAdmin):
  
    name = 'Subscriptions'
    application_url = 'github.com/hollowaytape'
    help_url = 'github.com/hollowaytape'
    author = 'Max Silbiger'
    domain = 'github.com/hollowaytape'
    
    def get_sections(self):
        from camelot.model.memento import Memento
        from camelot.model.i18n import Translation
        return [ Section( _('Subscription'),
                          self,
                          Icon('tango/22x22/apps/system-users.png'),
                          items = [Subscription] ),
                 Section( _('Configuration'),
                          self,
                          Icon('tango/22x22/categories/preferences-system.png'),
                          items = [Memento, Translation] )
                ]
    