from collections import defaultdict
from operator import itemgetter

from peewee import fn, JOIN, DoesNotExist

from sdssdb.peewee.sdss5db import opsdb, targetdb

from metrics import rs_version, observatory

boss_threshold = 0.2


def sn_dict():
    # we're abusing the ddict default_factory
    return {"r1": 0, "b1": 0, "AP": 0}


def fields_dict():
    # we're abusing the ddict default_factory
    return {"field_id": 0, "r1": 0, "b1": 0, "AP": 0, "designs": list()}


def fieldQueryDone(cadence=None):
    """query targetdb for fields matching parameters
    """

    dbCad = targetdb.Cadence
    if cadence is not None:
        matchingCad = dbCad.select().where(dbCad.label.contains(cadence))
    else:
        matchingCad = dbCad.select()

    Field = targetdb.Field
    dbVersion = targetdb.Version.get(plan=rs_version)
    Design = targetdb.Design
    d2s = opsdb.DesignToStatus
    doneStatus = opsdb.CompletionStatus.get(label="done").pk
    doneField = Field.alias()

    obsDB = targetdb.Observatory()
    obs = obsDB.get(label=observatory)

    doneCount = Design.select(fn.COUNT(Design.design_id).alias("count"))\
                      .join(d2s, JOIN.LEFT_OUTER,
                            on=(Design.design_id == d2s.design_id))\
                      .switch(Design)\
                      .join(doneField, JOIN.LEFT_OUTER,
                            on=(Design.field_pk == doneField.pk))\
                      .where(d2s.completion_status_pk == doneStatus,
                             doneField.pk == Field.pk)\
                      .alias("doneCount")

    fields = Field.select(Field, doneCount)\
                  .where(Field.cadence << matchingCad,
                         Field.version == dbVersion,
                         Field.observatory == obs,
                         doneCount != 0)

    # print(fields.sql())
    # select returns query object, we want a list
    return [f for f in fields]


def designQueryMjd(cadence=None):
    """query targetdb for fields matching parameters
    """

    dbCad = targetdb.Cadence
    if cadence is not None:
        matchingCad = dbCad.select().where(dbCad.label.contains(cadence))
    else:
        matchingCad = dbCad.select()

    Field = targetdb.Field
    dbVersion = targetdb.Version.get(plan=rs_version)
    Design = targetdb.Design
    d2s = opsdb.DesignToStatus
    doneStatus = opsdb.CompletionStatus.get(label="done").pk

    dquery = d2s.select(d2s.mjd, dbCad.label)\
                .join(Design)\
                .join(Field, on=(Design.field_pk == Field.pk))\
                .join(dbCad)\
                .where(d2s.completion_status_pk == doneStatus,
                       Field.version == dbVersion).tuples()

    return [[d[0], d[1]] for d in dquery]
