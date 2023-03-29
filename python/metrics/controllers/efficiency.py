#!/usr/bin/env/python

from quart import render_template, Blueprint, request

import numpy as np

from metrics import wrapBlocking
# from metrics.dbConvenience import cartonQueryMjd, getCartons

from . import getTemplateDictBase

efficiency_page = Blueprint("efficiency_page", __name__)


@efficiency_page.route('/efficiency.html', methods=['GET', 'POST'])
async def index():
    """ Index page. """
    templateDict = getTemplateDictBase()

    # mjds, fullCount = await wrapBlocking(cartonQueryMjd, carton=carton)

    # templateDict.update({
    #     "cartons": cartons,
    #     "counts": counts,
    #     "chosenCarton": carton,
    #     "goal": fullCount
    #     })

    return await render_template("efficiency.html", **templateDict)
