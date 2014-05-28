from camelot.view.filters import Filter, FilterWidget, filter_option, filter_data
from camelot.core.utils import ugettext_lazy as _

import datetime
import calendar

class DateFilter(Filter):

    def render( self, filter_data, parent ):
        return FilterWidget(filter_data, parent)

    def get_filter_data(self, admin):
        from sqlalchemy.sql import and_
        filter_names = []
        if admin.mapper!=admin.mapper.base_mapper:
            table = admin.mapper.local_table
        else:
            table = admin.mapper.mapped_table
        path = self.attribute.split('.')
        for field_name in path:
            attributes = admin.get_field_attributes(field_name)
            filter_names.append(attributes['name'])
            if 'target' in attributes:
                admin = attributes['admin']
                joins.append(field_name)
                if attributes['direction'] == 'manytoone':
                    table = admin.entity.table.join( table )
                else:
                    table = admin.entity.table

        col = getattr( admin.entity, field_name )

        today = datetime.date.today()
        tomorrow = today + datetime.timedelta(days=1)
        days_in_current_month = calendar.monthrange(today.year, today.month)
        most_recent_sunday = today - datetime.timedelta(days=(today.weekday() + 1))

        dates_range = (
            (_('Today'), today, tomorrow),
            
            (_('This week'), most_recent_sunday, (most_recent_sunday + datetime.timedelta(days=7)))
            (_('This month'), today.replace(day=1), today.replace(day=days_in_current_month))
            )

        def query_decorator(col, since, until):
            def decorator(q):
                return q.filter(and_(col>=since, col<=until))
            return decorator

        options = [ filter_option( name = _('All'),
                                   value = Filter.All,
                                   decorator = lambda q:q ) ]

        for option_name, since, until in dates_range:
            options.append( filter_option(name = option_name,
                                          value = None,
                                          decorator = query_decorator(col, since, until)
                                          )
                            )

        return filter_data( name = "Date",
                            options = options,
                            default = self.default )