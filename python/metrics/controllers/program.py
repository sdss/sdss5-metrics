#!/usr/bin/env/python

from quart import render_template, Blueprint, request

import numpy as np

from metrics import wrapBlocking
from metrics.dbConvenience import programQueryMjd, getPrograms

from . import getTemplateDictBase

program_page = Blueprint("program_page", __name__)


@program_page.route('/programs.html', methods=['GET', 'POST'])
async def index():
    """ Index page. """
    templateDict = getTemplateDictBase()

    programs = await wrapBlocking(getPrograms)

    program = "none"
    if request.args:
        program = request.args["program"].strip()
        if len(program) == 0:
            program = "none"

    if program == "none":
        mjds = []
    else:
        mjds = await wrapBlocking(programQueryMjd, program=program)

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
        "programs": programs,
        "counts": counts
        })

    return await render_template("programs.html", **templateDict)
