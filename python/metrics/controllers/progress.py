#!/usr/bin/env/python

from os import listdir

from quart import render_template, Blueprint, current_app

from metrics import wrapBlocking

from . import getTemplateDictBase


progress_page = Blueprint("progress_page", __name__)


@progress_page.route('/progress.html')
async def index():
    """ Index page. """
    templateDict = getTemplateDictBase()

    imgdir = current_app.config["STORE_FOLDER"]
    pngs = await wrapBlocking(listdir, imgdir)

    pngs = [p for p in pngs if "png" in p ]

    templateDict.update({
        "pngs": pngs
    })

    return await render_template("progress.html", **templateDict)
