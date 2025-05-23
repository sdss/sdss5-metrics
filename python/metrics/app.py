#!/usr/bin/env/python

import sys
import os
from inspect import getmembers, isfunction
from logging import getLogger, ERROR

import psycopg2
from quart import Quart, render_template

from metrics import jinja_filters, observatory, rs_version

getLogger('quart.serving').setLevel(ERROR)

app = Quart(__name__)

print("{0}App '{1}' created.{2}".format('\033[92m', __name__, '\033[0m')) # to remove later

STORE_FOLDER = f"/home/sdss5/tmp/metrics_plots/{rs_version}-{observatory.lower()}/"

app.config.update({
    "STORE_FOLDER": STORE_FOLDER
    })

# Define custom filters into the Jinja2 environment.
# Any filters defined in the jinja_env submodule are made available.
custom_filters = {name: function
                  for name, function in getmembers(jinja_filters)
                  if isfunction(function)}
app.jinja_env.filters.update(custom_filters)


# Change the implementation of "decimal" to a C-based version (much! faster)
try:
    import cdecimal
    sys.modules["decimal"] = cdecimal
except ImportError:
    pass  # no available

# -----------------------------------------------------------------------------
# The JSON module is unable to serialize Decimal objects, which is a problem
# as psycopg2 returns Decimal objects for numbers. This block of code overrides
# how psycopg2 parses decimal data types coming from the database, using
# the "float" data type instead of Decimal. This must be done separately for
# array data types.
#
# See link for other data types: http://initd.org/psycopg/docs/extensions.html
# -----------------------------------------------------------------------------
DEC2FLOAT = psycopg2.extensions.new_type(
    psycopg2.extensions.DECIMAL.values,
    'DEC2FLOAT',
    lambda value, curs: float(value) if value is not None else None)
psycopg2.extensions.register_type(DEC2FLOAT)

# the decimal array is returned as a string in the form:
# "{1,2,3,4}"
DECARRAY2FLOATARRAY = psycopg2.extensions.new_type(
    psycopg2.extensions.DECIMALARRAY.values,
    'DECARRAY2FLOATARRAY',
    lambda value, curs: [float(x) if x else None for x in value[1:-1].split(",")]
        if value else None)
psycopg2.extensions.register_type(DECARRAY2FLOATARRAY)
# -----------------------------------------------------------------------------

# -------------------
# Register blueprints
# -------------------
from metrics.controllers.index import index_page
from metrics.controllers.cumulative import cumulative_page
from metrics.controllers.progress import progress_page
from metrics.controllers.summary import summary_page
from metrics.controllers.program import program_page
from metrics.controllers.epochs import epochs_page
from metrics.controllers.targets import targets_page
from metrics.controllers.cartons import carton_page
from metrics.controllers.efficiency import efficiency_page
from metrics.controllers.rv_monit import rv_monit_page
from metrics.controllers.fieldDetail import fieldDetail_page
from metrics.controllers.fieldQuery import fieldQuery_page

from metrics.controllers.local import localSource
from metrics.controllers import getTemplateDictBase

app.register_blueprint(index_page)
app.register_blueprint(cumulative_page)
app.register_blueprint(progress_page)
app.register_blueprint(localSource)
app.register_blueprint(summary_page)
app.register_blueprint(program_page)
app.register_blueprint(epochs_page)
app.register_blueprint(targets_page)
app.register_blueprint(carton_page)
app.register_blueprint(efficiency_page)
app.register_blueprint(rv_monit_page)
app.register_blueprint(fieldDetail_page)
app.register_blueprint(fieldQuery_page)


@app.errorhandler(404)
async def page_not_found(e):
    return await render_template('404.html'), 404


@app.errorhandler(500)
async def err_page(e):
    """ Err page. """
    return await render_template("500.html", **getTemplateDictBase())
