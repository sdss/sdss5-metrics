#!/usr/bin/env/python

from quart import render_template, Blueprint

from metrics import wrapBlocking

from . import getTemplateDictBase


cumulative_page = Blueprint("cumulative_page", __name__)


@cumulative_page.route('/cumulative.html')
async def index():
    """ Index page. """
    templateDict = getTemplateDictBase()

    return await render_template("cumulative.html", **templateDict)
