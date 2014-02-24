# Copyright 2014 Max Silbiger.
# Created using the Camelot application framework, with its source made open under a GPL license.

import logging
from camelot.core.conf import settings, SimpleSettings

logging.basicConfig( level = logging.ERROR )
logger = logging.getLogger( 'main' )

# begin custom settings
class MySettings( SimpleSettings ):

    # add an ENGINE or a CAMELOT_MEDIA_ROOT method here to connect
    # to another database or change the location where files are stored
    #
    # def ENGINE( self ):
    #     from sqlalchemy import create_engine
    #     return create_engine( 'postgresql://user:passwd@127.0.0.1/database' )
    
    def setup_model( self ):
        """This function will be called at application startup, it is used to 
        setup the model"""
        from camelot.core.sql import metadata
        from sqlalchemy.orm import configure_mappers
        metadata.bind = self.ENGINE()
        import camelot.model.authentication
        import camelot.model.i18n
        import camelot.model.memento
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
    