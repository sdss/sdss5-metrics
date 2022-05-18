#!/usr/bin/env/python

from quart import render_template, Blueprint

from metrics import wrapBlocking

from . import getTemplateDictBase


progress_page = Blueprint("progress_page", __name__)


@progress_page.route('/progress.html')
async def index():
    """ Index page. """
    templateDict = getTemplateDictBase()

    return await render_template("progress.html", **templateDict)
