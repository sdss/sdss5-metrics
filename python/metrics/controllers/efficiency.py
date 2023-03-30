#!/usr/bin/env/python

from quart import render_template, Blueprint, request

import numpy as np

from metrics import wrapBlocking, observatory
from metrics.dbConvenience import bossSN

from . import getTemplateDictBase

efficiency_page = Blueprint("efficiency_page", __name__)


@efficiency_page.route('/efficiency.html', methods=['GET', 'POST'])
async def index():
    """ Index page. """

    b1, r1 = await wrapBlocking(bossSN)

    meta = {"r_threshold": 3.0,
            "b_threshold": 1.5,
            "r_max_bin": 10,
            "b_max_bin": 4}
    meta["b_bin_width"] = meta["b_max_bin"] / 20
    meta["r_bin_width"] = meta["r_max_bin"] / 20

    if observatory.lower() == "apo":
        meta["b_camera"] = "b1"
        meta["r_camera"] = "r1"
    else:
        meta["b_camera"] = "b2"
        meta["r_camera"] = "r2"

    bins = np.arange(0, meta["b_max_bin"], meta["b_bin_width"])
    Nb1, edges = np.histogram(b1, bins=bins)
    bins = np.arange(0, meta["r_max_bin"], meta["r_bin_width"])
    Nr1, edges = np.histogram(r1, bins=bins)

    meta["b_max"] = np.max(Nb1)
    meta["r_max"] = np.max(Nr1)

    b_good = np.array(b1) > meta["b_threshold"]
    r_good = np.array(r1) > meta["r_threshold"]

    meta["b_good"] = len(np.where(b_good)[0])
    meta["r_good"] = len(np.where(r_good)[0])

    meta["b_bad"] = len(np.where(~b_good)[0])
    meta["r_bad"] = len(np.where(~r_good)[0])


    meta["r_and_b"] = len(np.where(np.logical_and(r_good, b_good))[0])
    meta["r_not_b"] = len(np.where(np.logical_and(r_good, ~b_good))[0])
    meta["b_not_r"] = len(np.where(np.logical_and(~r_good, b_good))[0])
    meta["not_r_b"] = len(np.where(np.logical_and(~r_good, ~b_good))[0])

    templateDict = getTemplateDictBase()
    templateDict.update({
        "b1": b1,
        "r1": r1,
        "meta": meta
        })

    return await render_template("efficiency.html", **templateDict)