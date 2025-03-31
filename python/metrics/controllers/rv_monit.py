#!/usr/bin/env/python

from quart import render_template, Blueprint, request

import numpy as np

from metrics import wrapBlocking
from metrics.dbConvenience import mjd_by_cadence

from . import getTemplateDictBase


rv_monit_page = Blueprint("rv_monit_page", __name__)


@rv_monit_page.route('/rv_monit.html')
async def index():
    templateDict = getTemplateDictBase()

    mjd_start = "none"
    if request.args:
        try:
            mjd_start = int(request.args["mjd_start"])
        except ValueError:
            mjd_start = "none"

    field_mjds, delta_nom = await wrapBlocking(mjd_by_cadence, "bright_single_18x1_v2")

    fields = dict()
    for f in field_mjds:
        fid = f["field_id"]
        dates = f["mjd"]
        if mjd_start != "none":
            if np.min(dates) < mjd_start:
                continue
        deltas = list(np.sort(dates - np.min(dates)))
        fields[fid] = [[i, d] for i, d in enumerate(deltas)]
    
    goal = [[i, d] for i, d in enumerate(np.cumsum(delta_nom))]

    templateDict.update({
        "fields": fields,
        "goal": goal,
        "mjd_start": mjd_start
        })

    return await render_template("rv_monit.html", **templateDict)
