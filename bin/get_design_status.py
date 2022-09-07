import numpy as np
from astropy.io import fits
from astropy.table import Table
from kronos import rs_version, observatory  # , wrapBlocking
from kronos.scheduler import design_time
from peewee import fn, JOIN, DoesNotExist
from collections import defaultdict
from operator import itemgetter

from astropy.time import Time

from sdssdb.peewee.sdss5db import opsdb, targetdb, database

database.set_profile('apo5')

dbCad = targetdb.Cadence

Field = targetdb.Field
dbVersion = targetdb.Version.get(plan=rs_version)
Design = targetdb.Design
d2s = opsdb.DesignToStatus
doneStatus = opsdb.CompletionStatus.get(label="done").pk
d2f = targetdb.DesignToField

design_dtype = [('mjd', np.float32),  # from design_to_status
                ('cadence', np.unicode_, 30),  # from cadence
                ('design_id', np.int64),
                ('field_id', np.int32),  # from field
                ('design_mode', np.unicode_, 40),
                ('mugatu_version', np.unicode_, 40),
                ('run_on', np.unicode_, 40),
                ('racen', np.float64),  # from field
                ('deccen', np.float64),  # from field
                ('position_angle', np.float32),  # from field
                #('start_time', np.unicode_, 40),
                ('completion_status', np.unicode_, 20),
                ('observatory', np.unicode_, 20)]

ndesigns = (d2s.select(Design.design_id)
                .join(Design)\
                .join(d2f, on=(Design.design_id == d2f.design_id))\
                .join(Field, on=(Field.pk == d2f.field_pk))\
                .join(targetdb.Version).switch(targetdb.Field)\
                .join(targetdb.Observatory).switch(targetdb.Field)\
                .join(dbCad)\
                .switch(d2s)\
                .join(opsdb.CompletionStatus, JOIN.LEFT_OUTER)\
                .where((Field.version == dbVersion) &
                       (targetdb.Version.plan == rs_version) & 
                       (targetdb.Observatory.label == 'APO'))).count()


designs = np.zeros(ndesigns, dtype=design_dtype)

print(ndesigns)




dquery = d2s.select(d2s.mjd, 
                    dbCad.label.alias('cadence'), 
                    Field.racen, 
                    Field.deccen,
                    Field.position_angle, 
                    Field.field_id, 
                    opsdb.CompletionStatus.label.alias('completion_status'),
                    Design.design_id,
                    Design.design_mode_label.alias('design_mode'),
                    Design.mugatu_version,
                    Design.run_on,
                    targetdb.Observatory.label.alias('observatory'))\
            .join(Design)\
            .join(d2f, on=(Design.design_id == d2f.design_id))\
            .join(Field, on=(Field.pk == d2f.field_pk))\
            .join(targetdb.Version).switch(targetdb.Field)\
            .join(targetdb.Observatory).switch(targetdb.Field)\
            .join(dbCad)\
            .switch(d2s)\
            .join(opsdb.CompletionStatus, JOIN.LEFT_OUTER)\
            .where((Field.version == dbVersion) &
                (targetdb.Version.plan == rs_version) & 
                (targetdb.Observatory.label == 'APO')).dicts()

castn = dict()
for n in designs.dtype.names:
    castn[n] = np.cast[type(designs[n][0])]

for indx, d in enumerate(dquery):
    for n in designs.dtype.names:
        if(d[n] is not None):
            designs[n][indx] = castn[n](d[n])

t = Table(designs)
t.write('designs.fits', format='fits', overwrite=True)

