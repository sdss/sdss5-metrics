#!/usr/bin/env/python

from quart import render_template, Blueprint
import numpy as np

from metrics import wrapBlocking
from metrics.dbConvenience import tabulateRaObs

from . import getTemplateDictBase


index_page = Blueprint("index_page", __name__)


@index_page.route('/')
async def index():
    """ Index page. """
    templateDict = getTemplateDictBase()

    # ra = await wrapBlocking(tabulateRaObs)

    # binned = np.mod(ra, 15)

    return await render_template("index.html", **templateDict)
