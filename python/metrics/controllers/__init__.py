#!/usr/bin/python
import os

from metrics import __version__
from sdssdb import __version__ as dbVer


def getTemplateDictBase():
    version = __version__
    try:
        os.getlogin()
        isDev = True
    except OSError:
        # when run as a daemon, getlogin will fail
        isDev = False
    return {
        "isStable": False,
        "isDev": isDev,
        "version": version,
        "sdssdb_version": dbVer
    }
