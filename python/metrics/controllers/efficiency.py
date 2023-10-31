#!/usr/bin/env/python

import os

from quart import render_template, Blueprint, request

from astropy.io import fits
import numpy as np

from metrics import wrapBlocking, observatory
from metrics.dbConvenience import bossSN, apogeeSN

from . import getTemplateDictBase

efficiency_page = Blueprint("efficiency_page", __name__)


@efficiency_page.route('/efficiency.html', methods=['GET', 'POST'])
async def index():
    """ Index page. """

    b1, r1, boss_mjd = await wrapBlocking(bossSN)
    ap, ap_mjd = await wrapBlocking(apogeeSN)

    mjds = np.linspace(np.min(boss_mjd), np.max(boss_mjd), 20)

    meta = {"r_threshold": 3.0,
            "b_threshold": 1.5,
            "r_max_bin": 10,
            "b_max_bin": 4,
            "ap_threshold": 1012,
            "ap_max_bin": 4000,
            "mjd_min": np.min(boss_mjd),
            "mjd_max": np.max(boss_mjd)}
    meta["b_bin_width"] = meta["b_max_bin"] / 20
    meta["r_bin_width"] = meta["r_max_bin"] / 20
    meta["ap_bin_width"] = meta["ap_max_bin"] / 20

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
    bins = np.arange(0, meta["ap_max_bin"], meta["ap_bin_width"])
    Nap, edges = np.histogram(ap, bins=bins)

    meta["b_max"] = np.max(Nb1)
    meta["r_max"] = np.max(Nr1)
    meta["ap_max"] = np.max(Nap)

    # b_good = np.array(b1) > meta["b_threshold"]
    # r_good = np.array(r1) > meta["r_threshold"]
    # ap_good = np.array(ap) > meta["ap_threshold"]

    # meta["b_good"] = len(np.where(b_good)[0])
    # meta["r_good"] = len(np.where(r_good)[0])
    # meta["ap_good"] = len(np.where(ap_good)[0])

    # meta["b_bad"] = len(np.where(~b_good)[0])
    # meta["r_bad"] = len(np.where(~r_good)[0])
    # meta["ap_bad"] = len(np.where(~ap_good)[0])

    # meta["r_and_b"] = len(np.where(np.logical_and(r_good, b_good))[0])
    # meta["r_not_b"] = len(np.where(np.logical_and(r_good, ~b_good))[0])
    # meta["b_not_r"] = len(np.where(np.logical_and(~r_good, b_good))[0])
    # meta["not_r_b"] = len(np.where(np.logical_and(~r_good, ~b_good))[0])

    rs_version = os.getenv("RS_VERSION")
    loc = os.getenv("OBSERVATORY").lower()
    file_loc = f'/home/sdss5/tmp/metrics_plots/{rs_version}-{loc}/designs.fits'
    hdu = await wrapBlocking(fits.open, file_loc)
    hdu.verify('fix')
    design_data = hdu[1].data

    g = (design_data['completion_status'] == 'done')
    design_mjd = design_data[g]['mjd']
    design_count = np.array(range(len(design_mjd)))+1
    design_count = [float(i) for i in design_count]
    design_t = np.sort(design_mjd)
    design_t = [float(i) for i in design_t]

    end_date = np.max(design_data['mjd'])

    time_file = '/home/sdss5/tmp/metrics_plots/time_avail_apo.csv'
    time_array = await wrapBlocking(np.genfromtxt, time_file, names=True, 
                                    delimiter=",", dtype=None,
                                    encoding="UTF-8")
    
    subset = time_array[time_array["mjd"] < end_date]

    bright_time = subset["cum_bright"]
    bright_time = [float(i) for i in bright_time]
    dark_time = subset["cum_dark"]
    dark_time = [float(i) for i in dark_time]
    cumulative_mjds = subset["mjd"]
    cumulative_mjds = [float(i) for i in cumulative_mjds]

    templateDict = getTemplateDictBase()
    templateDict.update({
        "b1": b1,
        "r1": r1,
        "ap": ap,
        "boss_mjd": boss_mjd,
        "ap_mjd": ap_mjd,
        "meta": meta,
        "design_done": design_count,
        "design_mjds": design_t,
        "dark_time": dark_time,
        "bright_time": bright_time,
        "cumulative_mjds": cumulative_mjds
        })

    return await render_template("efficiency.html", **templateDict)
