#!/usr/bin/env/python

from collections import defaultdict

from quart import render_template, Blueprint

import numpy as np

from metrics import wrapBlocking
from metrics.dbConvenience import fieldQueryDone

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


summary_page = Blueprint("summary_page", __name__)


@summary_page.route('/summary.html')
async def index():
    """ Index page. """
    templateDict = getTemplateDictBase()

    cadence = None

    fields = await wrapBlocking(fieldQueryDone, cadence=cadence)

    cadenceTab = defaultdict(list)
    for f in fields:
        cadenceTab[convertCadence(f.cadence.label)].append(f.doneCount)

    cadences = list()
    plotBins = list()
    hists = list()
    for k, v in cadenceTab.items():
        cadences.append(k)

        start = np.min(v)
        end = np.max(v)

        if end - start <= 8:
            size = 1
            while end - start < 8:
                end += 1
        else:
            size = int(np.ceil((end-start)/8))
        bins = np.arange(start, end, size)

        hist, bin_edges = np.histogram(v, bins=bins)
        hists.append([int(i) for i in hist])
        plotBins.append([int(i) for i in bins[:-1]])

    templateDict.update({
        "cadences": cadences,
        "hists": hists,
        "bins": plotBins
        })

    return await render_template("summary.html", **templateDict)
