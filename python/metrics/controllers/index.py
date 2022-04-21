#!/usr/bin/env/python

from quart import render_template, Blueprint

from metrics import wrapBlocking

from . import getTemplateDictBase


index_page = Blueprint("index_page", __name__)


@index_page.route('/')
async def index():
    """ Index page. """
    templateDict = getTemplateDictBase()

    return await render_template("index.html", **templateDict)
