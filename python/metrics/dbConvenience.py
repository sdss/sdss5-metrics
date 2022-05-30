from collections import defaultdict
from operator import itemgetter

from peewee import fn, JOIN

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


def programQueryMjd(program=None):
    """query targetdb for fields matching parameters
    """

    Field = targetdb.Field
    dbVersion = targetdb.Version.get(plan=rs_version)
    Design = targetdb.Design
    d2s = opsdb.DesignToStatus
    doneStatus = opsdb.CompletionStatus.get(label="done").pk
    assn = targetdb.Assignment
    c2t = targetdb.CartonToTarget
    Carton = targetdb.Carton

    dquery = d2s.select(d2s.mjd)\
                .join(Design)\
                .join(Field, on=(Design.field_pk == Field.pk))\
                .switch(Design)\
                .join(assn)\
                .join(c2t)\
                .join(Carton)\
                .where(d2s.completion_status_pk == doneStatus,
                       Field.version == dbVersion,
                       Carton.program == program).tuples()

    return [d for d in dquery]


def getPrograms():
    Carton = targetdb.Carton

    query = Carton.select(Carton.program).distinct()

    return [c.program for c in query]


def tabulateRaObs():
    Field = targetdb.Field
    dbVersion = targetdb.Version.get(plan=rs_version)
    Design = targetdb.Design
    cfg = opsdb.Configuration
    exp = opsdb.Exposure
    db_flavor = opsdb.ExposureFlavor.get(pk=1)

    # apogee exposures are 8 digits, boss are 6
    # boss is always exposed? apogee may not be, e.g. rm?
    # can select exposure_no < 1e6 to only get boss

    fields = Field.select(Field.racen)\
                  .join(Design, on=(Field.pk == Design.field_pk))\
                  .join(cfg).join(exp)\
                  .where(exp.exposure_flavor == db_flavor,
                         Field.version == dbVersion,
                         exp.exposure_no < 1e6)\
                  .tuples()

    return [f[0] for f in fields]
