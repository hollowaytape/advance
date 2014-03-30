from camelot.admin.action import Action
from camelot.core.utils import ugettext_lazy as _
from camelot.view.art import Icon

class ImportCSV( Action ):
    verbose_name = _('Import from CSV')
    icon = Icon('tango/22x22/mimetypes/image-x-generic.png')
    
# begin select files
    def model_run( self, model_context ):
        from camelot.view.action_steps import ( SelectFile, 
                                                UpdateProgress, 
                                                Refresh,
                                                FlushSession )
        
        select_csv_file = SelectFile( 'CSV Files (*.csv);;All Files (*)' )
        select_csv_file.single = True
        file_names = yield select_csv_file
        file_count = len( file_names )
# end select files
# begin create movies
        import os
        from sqlalchemy import orm
        from camelot.core.orm import Session
        from camelot_example.model import Subscription
              
        sub_mapper = orm.class_mapper(Subscription)
        for property in Subscription.__table__.columns:
            
        cover_property = movie_mapper.get_property( 'cover' )
        storage = cover_property.columns[0].type.storage
        session = Session()

        for i, file_name in enumerate(file_names):
            yield UpdateProgress( i, file_count )
            title = os.path.splitext( os.path.basename( file_name ) )[0]
            stored_file = storage.checkin( unicode( file_name ) )
            movie = Movie( title = unicode( title ) )
            movie.cover = stored_file
            
        yield FlushSession( session )
# end create movies
# begin refresh
        yield Refresh()
# end refresh