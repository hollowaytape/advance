import datetime
import time

from camelot.admin.action import application_action
from camelot.admin.action.base import Action
from camelot.admin.entity_admin import EntityAdmin
from camelot.admin.object_admin import ObjectAdmin
from camelot.admin.validator.object_validator import ObjectValidator
from camelot.view.action_steps import ChangeObject, UpdateProgress
from camelot.view.art import ColorScheme, Icon
from camelot.view.controls.delegates import DateDelegate
from camelot.view.filters import ComboBoxFilter, ValidDateFilter
from sqlalchemy.orm import mapper
from sqlalchemy.sql import select, func, and_, or_
from sqlalchemy import distinct

from camelot.model import metadata
__metadata__ = metadata

from model import Parameter
import config
import reports

class SubscriptionsInDateRange(object):
    class Admin(EntityAdmin):
        verbose_name = 'Subscriptions in Date Range'
        verbose_name_plural = 'Subscriptions in Date Range'
        list_display = [
            'End_Date',
            'Last_Name',
            'Address',
            'PO_Box',
            'Rural_Box',
            'City',
            'State',
            'Zip',
            ]
        list_actions = [
            AddressLabels(),
            AddressLabelsDotMatrix(),
            RenewalNotice(),
            ]
        
def date_range_query():
    tbl_vidalia = Vidalia.mapper.mapped_table
    tbl_parameter = Parameter.mapper.mapped_table

    tp = total_pagos_x_credito_activo_a_fecha()

    pre = select([tbl_vidalia.c.First_Name,
                  tbl_vidalia.c.Last_Name,
                  tbl_vidalia.c.Address,
                  tbl_vidalia.c.PO_Box,
                  tbl_vidalia.c.Rural_Box,
                  tbl_vidalia.c.City,
                  tbl_vidalia.c.State,
                  tbl_vidalia.c.Zip,
                  tbl_vidalia.c.Sort_Code,
                  tbl_vidalia.c.Walk_Sequence,
                  tbl_vidalia.c.City_Code,
                  tbl_vidalia.c.Zone,
                  tbl_vidalia.c.Level
                  ],
                  
                 from_obj=[tbl_credito.join(tbl_benef).join(tbl_barrio).join(tbl_cartera),
                           tp,
                           tbl_parametro,
                           ],
                 whereclause=and_(tp.c.credito_id == tbl_credito.c.id,
                                  tbl_benef.c.activa == True,
                                  tbl_credito.c.deuda_total != 0,
                                  tbl_credito.c.fecha_entrega <= tbl_parametro.c.fecha,
                                  or_(tbl_credito.c.fecha_finalizacion > tbl_parametro.c.fecha,
                                      tbl_credito.c.fecha_finalizacion == None)),
                 ).alias('pre')

    # Para cada beneficiaria activa, el estado de sus creditos.
    stmt = select([pre.c.beneficiaria_id,
                   pre.c.comentarios,
                   pre.c.barrio,
                   pre.c.beneficiaria,
                   pre.c.nro_credito,
                   pre.c.fecha_entrega,
                   pre.c.fecha_inicio,
                   pre.c.fecha_cancelacion,
                   pre.c.saldo_anterior,
                   pre.c.capital,
                   pre.c.tasa_interes,
                   pre.c.cartera,
                   pre.c.monto_aporte,
                   pre.c.deuda_total,
                   pre.c.cuotas,
                   pre.c.cuota_calculada,
                   pre.c.cuotas_pagadas,
                   pre.c.cuotas_pagadas_porcent,
                   pre.c.cuotas_teorico,
                   (pre.c.cuotas_teorico / pre.c.cuotas).label('cuotas_teorico_porcent'),
                   (pre.c.cuotas_teorico - pre.c.cuotas_pagadas).label('diferencia_cuotas'),
                   pre.c.saldo,
                   pre.c.monto_pagado,
                   (pre.c.deuda_total * pre.c.cuotas_teorico / pre.c.cuotas).label('monto_teorico'),
                   (pre.c.deuda_total * pre.c.cuotas_teorico / pre.c.cuotas - pre.c.monto_pagado).label('diferencia_monto'),
                   tbl_estado_credito.c.descripcion.label('estado'),
                   ],
                  from_obj=[pre,
                            tbl_estado_credito,
                            ],
                  whereclause=and_(pre.c.cuotas_teorico - pre.c.cuotas_pagadas > tbl_estado_credito.c.cuotas_adeudadas_min,
                                   pre.c.cuotas_teorico - pre.c.cuotas_pagadas <= tbl_estado_credito.c.cuotas_adeudadas_max,
                                   ),
                  )
    return stmt.alias('indicadores')
        
class DateRangeDialog(object):
    def __init__(self):
        default = datetime.date.today()
        self.start = get_config_date('start', default)
        self.end = get_config_date('end', default)

    def _get_start(self):
        return self.start

    def _set_start(self, value):
        self.start = value
        if self.end < value:
            self.end = value

    _start = property(_get_start, _set_start)

    class Admin(ObjectAdmin):
        verbose_name = 'Enter Date Range'
        form_display = ['_start', 'end']
        validator = DatesValidator
        form_size = (100, 100)
        field_attributes = dict(_start = dict(name = 'start',
                                              delegate = DateDelegate,
                                              editable = True),
                                end = dict(name = 'end',
                                             delegate = DateDelegate,
                                             editable = True,
                                             tooltip = 'Find all subscriptions up to and including this date',
                                             background_color = lambda o: ColorScheme.orange_1 if o.end < o.start else None))

class DateRangeDialog(Action):
    icon = Icon('tango/16x16/apps/office-calendar.png')

    def __init__(self, name, cls):
        self.verbose_name = name
        self._cls = cls

    def model_run(self, model_context):
        # ask for date intervals
        dates = DateRangeDialog()
        yield ChangeObject(dates)

        # truncate table (after ChangeObject since user may cancel)
        Parameter.query.delete()        # holds only start and end date

        start = dates.start
        end = dates.end

        if end < start:
            end = start

        # guardar valores para usar por default la proxima vez
        conf = config.Config()
        conf.set('start', start.strftime('%Y-%m-%d'))
        conf.set('end', end.strftime('%Y-%m-%d'))

        pstart = Parameter()
        pstart.date = start
        yield UpdateProgress()

        pend = Parameter()
        pend.date = end
        yield UpdateProgress()

        Parameter.query.session.flush()
        yield application_action.OpenTableView(model_context.admin.get_application_admin().get_related_admin(self._cls))

class DatesValidator(ObjectValidator):
    def objectValidity(self, entity_instance):
        messages = super(DatesValidator, self).objectValidity(entity_instance)
        if entity_instance.end < entity_instance.start:
            messages.append("'end' date must be equal or after 'start' date.'")
        return messages

def get_config_date(key, default):
    conf = config.Config()
    ff = conf.safe_get(key)
    if not ff:
        return default
    tt = time.strptime(ff, '%Y-%m-%d')
    return datetime.date(tt.tm_year, tt.tm_mon, tt.tm_mday)
    
def setup_views():
    stmt = indicadores()
    mapper(Indicadores, stmt, always_refresh=True,
           primary_key=[stmt.c.beneficiaria_id,
                        stmt.c.nro_credito,
                        ])