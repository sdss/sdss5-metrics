#!/usr/bin/env/python

from quart import render_template, Blueprint, request

import numpy as np

from metrics import wrapBlocking
from metrics.dbConvenience import cartonQueryMjd, getCartons

from . import getTemplateDictBase

carton_page = Blueprint("carton_page", __name__)


@carton_page.route('/cartons.html', methods=['GET', 'POST'])
async def index():
    """ Index page. """
    templateDict = getTemplateDictBase()

    cartons = await wrapBlocking(getCartons)

    carton = "none"
    if request.args:
        carton = request.args["carton"].strip()
        if len(carton) == 0:
            carton = "none"

    if carton == "none":
        mjds = []
    else:
        mjds = await wrapBlocking(cartonQueryMjd, carton=carton)

    if len(mjds) == 0:
        counts = []
        x_axis = []
    else:
        first = int(np.min(mjds))
        last = int(np.max(mjds))

        x_axis = np.arange(first, last, 1)

        x_axis = [int(m) for m in x_axis]

        counts = [[m, len(np.where(np.array(mjds) < m)[0])] for m in x_axis]

    templateDict.update({
        "cartons": cartons,
        "counts": counts
        })

    return await render_template("cartons.html", **templateDict)
