# -*- coding: utf-8 -*-

from quart import request, render_template, Blueprint

from metrics import wrapBlocking
from kronos.dbConvenience import getCadences, fieldQuery
from . import getTemplateDictBase

fieldQuery_page = Blueprint("fieldQuery_page", __name__)


def sortFunc(elem):
    return elem.field_id


@fieldQuery_page.route('/fieldQuery.html', methods=['GET', 'POST'])
async def fieldDetail():

    ra_start, ra_end = 0, 360
    dec_start = -90
    dec_end = 90

    cadences = getCadences()

    templateDict = getTemplateDictBase()

    form = await request.form
    field_ids = list()
    errors = list()

    if  form:
        specialStatus = form["specialStatus"]
        chosenCadence = form["chosenCadence"]
    else:
        # set default, can change it below
        specialStatus = "none"
        chosenCadence = "none"

    if request.args:
        chosenCadence = request.args["cadence"].strip()
        if len(chosenCadence) == 0:
            chosenCadence = "none"
        specialStatus = request.args["specialStatus"]
        try:
            ra_start = int(request.args["ra0Select"])
            ra_end = int(request.args["ra1Select"])
        except:
            ra_start = 0
            ra_end = 360
        try:
            dec_start = int(request.args["dec0Select"])
            dec_end = int(request.args["dec1Select"])
        except:
            dec_start = 0
            dec_end = 360

        if "fieldids" in request.args:
            f_text = request.args["fieldids"]
            if len(f_text) > 0:
                try:
                    if "," in f_text:
                        field_ids = [int(d) for d in f_text.strip().split(",") if len(d)]
                    else:
                        field_ids = [int(f_text)]
                except:
                    errors.append("invalid design input")
                    field_ids = list()

    if chosenCadence == "none":
        queryCadence = None
    else:
        queryCadence = chosenCadence

    if specialStatus == "none":
        dbPriority = None
    else:
        dbPriority = specialStatus
    fields = await wrapBlocking(fieldQuery,
                                cadence=queryCadence,
                                priority=dbPriority,
                                ra_range=[ra_start, ra_end],
                                dec_range=[dec_start, dec_end],
                                field_ids=field_ids)
    fields.sort(key=sortFunc)

    templateDict.update({
        "cadences": [str(c.label) for c in cadences],
        "specialStatus": specialStatus,
        "chosenCadence": chosenCadence,
        "fields": fields,
        "ra_range": [int(ra_start), int(ra_end)],
        "dec_range": [int(dec_start), int(dec_end)]
    })

    return await render_template("fieldQuery.html", **templateDict)


if __name__ == "__main__":
    pass
