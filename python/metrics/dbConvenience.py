from peewee import fn, JOIN

from sdssdb.peewee.sdss5db import opsdb, targetdb

from metrics import rs_version, observatory

boss_threshold = 0.2
apogee_threshold = 100


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

    dbVersion = targetdb.Version.get(plan=rs_version)
    doneStatus = opsdb.CompletionStatus.get(label="done").pk
    AT = targetdb.AssignedTargets

    dquery = AT.select(AT.mjd)\
               .where(AT.completion_status_pk == doneStatus,
                      AT.version_pk == dbVersion.pk,
                      AT.program == program).tuples()

    fullCount = AT.select(fn.count(AT.assignment_pk))\
                  .where(AT.version_pk == dbVersion.pk,
                         AT.program == program).scalar()

    return [d for d in dquery], fullCount


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
                         AT.version_pk == dbVersion.pk)\
                  .group_by(AT.program).dicts()

    doneDict = {d["program"]: d["count"] for d in doneCount}

    fullCount = AT.select(AT.program, fn.count(AT.program))\
                  .where(AT.version_pk == dbVersion.pk)\
                  .group_by(AT.program).dicts()

    fullDict = {f["program"]: f["count"] for f in fullCount}

    return doneDict, fullDict


def cartonQueryMjd(carton=None):
    dbVersion = targetdb.Version.get(plan=rs_version)
    doneStatus = opsdb.CompletionStatus.get(label="done").pk
    Carton = targetdb.Carton
    # cartons across target selection versions have same name
    carton_pks = Carton.select(Carton.pk)\
                       .where(Carton.carton == carton)

    AT = targetdb.AssignedTargets

    cquery = AT.select(AT.mjd)\
               .where(AT.completion_status_pk == doneStatus,
                      AT.version_pk == dbVersion.pk,
                      AT.carton_pk << carton_pks).tuples()

    fullCount = AT.select(fn.count(AT.assignment_pk))\
                  .where(AT.version_pk == dbVersion.pk,
                         AT.carton_pk << carton_pks).scalar()

    return [c for c in cquery], fullCount


def getCartons():
    Carton = targetdb.Carton
    AT = targetdb.AssignedTargets

    aquery = AT.select(AT.carton_pk).distinct()

    assigned_cartons = [a.carton_pk for a in aquery]

    cquery = Carton.select(Carton.carton, Carton.pk)\
                   .where(Carton.pk << assigned_cartons)


    return [c.carton for c in cquery]


def bossSN():
    exp = opsdb.Exposure
    b1 = opsdb.CameraFrame.alias()
    r1 = opsdb.CameraFrame.alias()
    cfg = opsdb.Configuration
    d2f = targetdb.DesignToField
    f = targetdb.Field
    cad = targetdb.Cadence
    dbVersion = targetdb.Version.get(plan=rs_version)
    if observatory.lower() == "lco":
        bcamera = opsdb.Camera.get(label="b2")
        rcamera = opsdb.Camera.get(label="r2")
    else:
        bcamera = opsdb.Camera.get(label="b1")
        rcamera = opsdb.Camera.get(label="r1")

    sn2 = exp.select(b1.sn2.alias("b1"), r1.sn2.alias("r1"))\
             .join(b1).switch(exp)\
             .join(r1)\
             .switch(exp).join(cfg)\
             .join(d2f, on=(d2f.design_id == cfg.design_id))\
             .join(f).join(cad)\
             .where(b1.camera == bcamera, r1.camera == rcamera,
                    b1.sn2 >= boss_threshold, r1.sn2 >= boss_threshold,
                    cad.label % '%dark%', f.version == dbVersion)

    b1 = list()
    r1 = list()
    for d in sn2.dicts():
        b1.append(d["b1"])
        r1.append(d["r1"])

    return b1, r1


def apogeeSN():
    exp = opsdb.Exposure
    cf = opsdb.CameraFrame
    cfg = opsdb.Configuration
    d2f = targetdb.DesignToField
    f = targetdb.Field
    cad = targetdb.Cadence
    dbVersion = targetdb.Version.get(plan=rs_version)
    apcamera = opsdb.Camera.get(label="APOGEE")

    sn2 = exp.select(cf.sn2)\
             .join(cf)\
             .switch(exp).join(cfg)\
             .join(d2f, on=(d2f.design_id == cfg.design_id))\
             .join(f).join(cad)\
             .where(cf.camera == apcamera, cf.sn2 >= apogee_threshold,
                    cad.label % '%bright%', f.version == dbVersion)

    ap = list()
    for d in sn2.dicts():
        ap.append(d["sn2"])

    return ap
