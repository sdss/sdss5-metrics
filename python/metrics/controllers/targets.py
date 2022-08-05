#!/usr/bin/env/python

from collections import defaultdict

from quart import render_template, Blueprint

import numpy as np

from metrics import wrapBlocking
from metrics.dbConvenience import programProgress

from . import getTemplateDictBase


targets_page = Blueprint("targets_page", __name__)


@targets_page.route('/targets.html')
async def index():
    """ Index page. """
    templateDict = getTemplateDictBase()

    doneDict, fullDict = await wrapBlocking(programProgress)

    programs = [k for k in doneDict.keys() if "ops" not in k]

    done = [doneDict[p] for p in programs]
    full = [fullDict[p] for p in programs]
    percents = [f"{(d/f)*100:4.1f}" for d, f in zip(done, full)]

    templateDict.update({
        "programs": programs,
        "done": done,
        "full": full,
        "percents": percents
        })

    return await render_template("targets.html", **templateDict)
