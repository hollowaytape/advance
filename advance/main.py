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

from camelot.core.conf import settings, SimpleSettings
import logging, os, jinja2

logging.basicConfig( level = logging.ERROR )
logger = logging.getLogger( 'main' )

# begin custom settings
class MySettings( SimpleSettings ):

    # add an ENGINE or a CAMELOT_MEDIA_ROOT method here to connect
    # to another database or change the location where files are stored

    ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
    CAMELOT_MEDIA_ROOT = os.path.abspath(os.path.join(ROOT_DIR, 'images'))
    
    def ENGINE( self ):
        from sqlalchemy import create_engine
        return create_engine(u'sqlite:///subscriptions.db')
    
    
    def setup_model( self ):
        """This function will be called at application startup, it is used to 
        setup the model"""
        from camelot.core.sql import metadata
        from sqlalchemy.orm import configure_mappers
        metadata.bind = self.ENGINE()
        import camelot.model.i18n
        import subs.model
        configure_mappers()
        metadata.create_all()

my_settings = MySettings( 'Max Silbiger', 'Subscriptions' ) 
settings.append( my_settings )
# end custom settings

def start_application():
    from camelot.view.main import main
    from subs.application_admin import MyApplicationAdmin
    main(MyApplicationAdmin())

if __name__ == '__main__':
    start_application()
    