# sdss5-metrics

![Versions](https://img.shields.io/badge/python->3.7-blue)
[![Documentation Status](https://readthedocs.org/projects/sdss5-metrics/badge/?version=latest)](https://sdss5-metrics.readthedocs.io/en/latest/?badge=latest)
[![Travis (.org)](https://img.shields.io/travis/sdss/sdss5-metrics)](https://travis-ci.org/sdss/sdss5-metrics)
[![codecov](https://codecov.io/gh/sdss/sdss5-metrics/branch/main/graph/badge.svg)](https://codecov.io/gh/sdss/sdss5-metrics)

webapp for showing sdss5 metrics

Much of this package is based off the [Material Dashboard template](https://github.com/creativetimofficial/material-dashboard). Portions borrowed from this template are licensed under an MIT license.

## Installation for development

This webapp is based on the [quart](https://pgjones.gitlab.io/quart/) framework. Installation for development simply requires a pip install and setting an environment variable. A virtual environment to hold this install is highly recommended.

Clone the repo:

`git clone https://github.com/sdss/sdss5-metrics.git`
`cd sdss5-metrics`

Inside your virtual environment, install the product:

`pip install -e .`

The `-e` flag is necessary for the code you're working on to show up in the app.

Next you need a `QUART_APP` environment variable pointing to the "app". In bash:

`export QUART_APP=/absolute/path/to/sdss5-metrics/python/metrics/app:app`

Then the app can be run with:

`quart run`

By default it runs at "localhost:5000" in any browser, but passing `-p WXYZ` will start the app on port WXYZ (ports over 3000 are recommended unless you know what you're doing)
