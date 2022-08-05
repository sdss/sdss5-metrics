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
    d2f = targetdb.DesignToField

    obsDB = targetdb.Observatory()
    obs = obsDB.get(label=observatory)

    doneCount = Design.select(fn.COUNT(Design.design_id).alias("count"))\
                      .join(d2s, JOIN.LEFT_OUTER,
                            on=(Design.design_id == d2s.design_id))\
                      .switch(Design)\
                      .join(d2f, on=(Design.design_id == d2f.design_id))\
                      .join(doneField, JOIN.LEFT_OUTER,
                            on=(d2f.field_pk == doneField.pk))\
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

    Field = targetdb.Field
    dbVersion = targetdb.Version.get(plan=rs_version)
    Design = targetdb.Design
    d2s = opsdb.DesignToStatus
    doneStatus = opsdb.CompletionStatus.get(label="done").pk
    d2f = targetdb.DesignToField

    dquery = d2s.select(d2s.mjd, dbCad.label)\
                .join(Design)\
                .join(d2f, on=(Design.design_id == d2f.design_id))\
                .join(Field, on=(Field.pk == d2f.field_pk))\
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
    d2f = targetdb.DesignToField

    dquery = d2s.select(d2s.mjd)\
                .join(Design)\
                .join(d2f, on=(Design.design_id == d2f.design_id))\
                .join(Field, on=(Field.pk == d2f.field_pk))\
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
    d2f = targetdb.DesignToField

    # apogee exposures are 8 digits, boss are 6
    # boss is always exposed? apogee may not be, e.g. rm?
    # can select exposure_no < 1e6 to only get boss

    fields = Field.select(Field.racen)\
                  .join(d2f, on=(Field.pk == d2f.field_pk))\
                  .join(Design, on=(Design.design_id == d2f.design_id))\
                  .join(cfg).join(exp)\
                  .where(exp.exposure_flavor == db_flavor,
                         Field.version == dbVersion,
                         exp.exposure_no < 1e6)\
                  .tuples()

    return [f[0] for f in fields]


def fieldForEpochs():
    Design = targetdb.Design
    Field = targetdb.Field
    Cadence = targetdb.Cadence
    DesignToStatus = opsdb.DesignToStatus
    CompletionStatus = opsdb.CompletionStatus
    doneStatus = CompletionStatus.get(label="done").pk
    d2f = targetdb.DesignToField

    query = Design.select(Design.design_id, DesignToStatus.mjd,
                          Cadence.nexp, Cadence.label.alias("cadence"),
                          Field.pk)\
                  .join(DesignToStatus, on=(Design.design_id == DesignToStatus.design_id))\
                  .switch(Design)\
                  .join(d2f, on=(Design.design_id == d2f.design_id))\
                  .join(Field, on=(Field.pk == d2f.field_pk))\
                  .join(Cadence, on=(Field.cadence_pk == Cadence.pk))\
                  .where(DesignToStatus.completion_status_pk == doneStatus)

    return query.dicts()


def programProgress():
    dbVersion = targetdb.Version.get(plan=rs_version)
    Design = targetdb.Design
    d2s = opsdb.DesignToStatus
    doneStatus = opsdb.CompletionStatus.get(label="done").pk

    AT = targetdb.AssignedTargets

    doneCount = AT.select(AT.program, fn.count(AT.program))\
                  .join(Design)\
                  .join(d2s)\
                  .where(d2s.completion_status_pk == doneStatus,
                         AT.version == dbVersion.plan)\
                  .group_by(AT.program).dicts()

    doneDict = {d["program"]: d["count"] for d in doneCount}

    fullCount = AT.select(AT.program, fn.count(AT.program))\
                  .where(AT.version == dbVersion.plan)\
                  .group_by(AT.program).dicts()

    fullDict = {f["program"]: f["count"] for f in fullCount}

    return doneDict, fullDict


def cartonQueryMjd(carton=None):
    dbVersion = targetdb.Version.get(plan=rs_version)
    d2s = opsdb.DesignToStatus
    doneStatus = opsdb.CompletionStatus.get(label="done").pk
    c2t = targetdb.CartonToTarget
    Carton = targetdb.Carton

    AT = targetdb.AssignedTargets

    cquery = d2s.select(d2s.mjd)\
                .join(AT, on=(d2s.design_id == AT.design_id))\
                .join(c2t)\
                .join(Carton)\
                .where(d2s.completion_status_pk == doneStatus,
                       AT.version == dbVersion.plan,
                       Carton.carton == carton).tuples()

    fullCount = Carton.select(fn.count(AT.assignment_pk))\
                      .join(c2t)\
                      .join(AT)\
                      .where(AT.version == dbVersion.plan,
                             Carton.carton == carton)\
                      .scalar()

    return [d for d in dquery], fullCount


def getCartons():
    Carton = targetdb.Carton

    query = Carton.select(Carton.carton).distinct()

    return [c.carton for c in query]
