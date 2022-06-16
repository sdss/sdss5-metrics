#!/usr/bin/env/python

from collections import defaultdict

from quart import render_template, Blueprint, request

import numpy as np

from metrics import wrapBlocking
from metrics.dbConvenience import fieldForEpochs
from metrics.controllers.cumulative import convertCadence

from . import getTemplateDictBase

epochs_page = Blueprint("epochs_page", __name__)


@epochs_page.route('/epochs.html', methods=['GET', 'POST'])
async def epochs():
    """ epochs page. """
    templateDict = getTemplateDictBase()

    fields = await wrapBlocking(fieldForEpochs)

    fieldMJDs = defaultdict(list)
    fieldToCad = dict()
    nexp = dict()
    for f in fields:
        fieldMJDs[f["pk"]].append(f["mjd"])
        fieldToCad[f["pk"]] = convertCadence(f["cadence"])
        expCount = [np.sum(f["nexp"][:i+1]) for i in range(len(f["nexp"]))]
        nexp[f["pk"]] = expCount

    cadMJDs = defaultdict(list)
    # cadDesigns = defaultdict(lambda x: 0)
    for f, mjds in fieldMJDs.items():
        i = 0
        done = not nexp[f][0] <= len(mjds)
        while not done:
            epoch_end_idx = nexp[f][i] - 1
            # print(i, fieldToCad[f], nexp[f][i], mjds[epoch_end_idx])
            cadMJDs[fieldToCad[f]].append(mjds[epoch_end_idx])
            i += 1
            done = i >= len(nexp[f])
            if not done:
                done = nexp[f][i] >= len(mjds)

    cumalative_mjds = defaultdict(list)

    for cad, mjds in cadMJDs.items():
        first = int(np.min(mjds))
        last = int(np.max(mjds))

        x_axis = np.arange(first, last, 1)

        x_axis = [int(m) for m in x_axis]

        counts = [[m, len(np.where(np.array(mjds) < m)[0])] for m in x_axis]
        cumalative_mjds[cad] = counts

    templateDict.update({
        "cadences": [c for c in cadMJDs.keys()],
        "mjds": [cumalative_mjds[c] for c in cadMJDs.keys()]
        })

    return await render_template("epochs.html", **templateDict)
