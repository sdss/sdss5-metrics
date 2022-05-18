#!/usr/bin/env/python

from collections import defaultdict

from quart import render_template, Blueprint

import numpy as np

from metrics import wrapBlocking
from metrics.dbConvenience import designQueryMjd

from . import getTemplateDictBase


def convertCadence(cad):
    if "_v" in cad:
        cad = cad[:cad.index("_v")]
    split = cad.split("_")
    nums = split[-1]
    name = "".join([str(n) + "_" for n in split[:-1]])
    try:
        epochs, exps = nums.split("x")
    except ValueError:
        return cad
    if int(exps) > 6:
        return cad
    epochs = int(epochs)

    name += "Nx" + exps
    return name


cumulative_page = Blueprint("cumulative_page", __name__)


@cumulative_page.route('/cumulative.html')
async def index():
    """ Index page. """
    templateDict = getTemplateDictBase()

    cadence = None

    designs = await wrapBlocking(designQueryMjd, cadence=cadence)

    first = 1e7
    last = 0
    cadenceTab = defaultdict(list)
    for mjd, cad in designs:
        if mjd < first:
            first = int(mjd)
        elif mjd > last:
            last = int(mjd)
        cadenceTab[convertCadence(cad)].append(mjd)

    x_axis = np.arange(first, last, 1)

    x_axis = [int(m) for m in x_axis]

    cadences = list()
    counts = list()
    for k, v in cadenceTab.items():
        cadences.append(k)

        counts.append([[m, len(np.where(np.array(v) < m)[0])] for m in x_axis])

    templateDict.update({
        "cadences": cadences,
        "counts": counts,
        "x_axis": x_axis
        })

    return await render_template("cumulative.html", **templateDict)
