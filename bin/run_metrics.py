#!/usr/bin/env python
# encoding: utf-8

import os

import numpy as np
from matplotlib import pyplot as plt

from astropy.io import fits
from astropy.time import Time
import astropy.coordinates as coord
import astropy.units as un
# from astropy.visualization import LogStretch
# from matplotlib.colors import LinearSegmentedColormap
# from astropy.visualization.mpl_normalize import ImageNormalize
import matplotlib as mpl
import os
from datetime import datetime
# import glob
from scipy.interpolate import interp1d

import numpy as np
# from astropy.io import fits
from peewee import JOIN

from sdssdb.peewee.sdss5db import opsdb, targetdb

# matplotlib setup
plt.style.use(['seaborn-v0_8-talk','seaborn-v0_8-white', 'seaborn-v0_8-ticks']) 
plt.rcParams['axes.linewidth'] = 2
plt.rcParams['axes.labelsize'] = 20

plt.rcParams['lines.linewidth'] = 2
plt.rcParams['lines.markersize'] = 10

plt.rcParams['xtick.labelsize'] = 14
plt.rcParams['ytick.labelsize'] = 14

plt.rcParams['xtick.major.size'] = 10
plt.rcParams['xtick.major.width'] = 2
plt.rcParams['xtick.minor.size'] = 6
plt.rcParams['xtick.minor.width'] = 2

plt.rcParams['ytick.major.size'] = 10
plt.rcParams['ytick.major.width'] = 2
plt.rcParams['ytick.minor.size'] = 6
plt.rcParams['ytick.minor.width'] = 2

buffer_mjd = 10.
buffer_count = 5.1


def pullDesigns():
    rs_version = os.getenv("RS_VERSION")
    loc = os.getenv("OBSERVATORY").lower()

    dbCad = targetdb.Cadence

    Field = targetdb.Field
    dbVersion = targetdb.Version.get(plan=rs_version)
    Design = targetdb.Design
    d2s = opsdb.DesignToStatus
    doneStatus = opsdb.CompletionStatus.get(label="done").pk
    d2f = targetdb.DesignToField

    design_dtype = [('mjd', np.float32),  # from design_to_status
                    ('cadence', np.unicode_, 30),  # from cadence
                    ('design_id', np.int64),
                    ('field_id', np.int32),  # from field
                    ('design_mode', np.unicode_, 40),
                    ('mugatu_version', np.unicode_, 40),
                    ('run_on', np.unicode_, 40),
                    ('racen', np.float64),  # from field
                    ('deccen', np.float64),  # from field
                    ('position_angle', np.float32),  # from field
                    #('start_time', np.unicode_, 40),
                    ('completion_status', np.unicode_, 20),
                    ('observatory', np.unicode_, 20)]

    ndesigns = (d2s.select(Design.design_id)
                    .join(Design)\
                    .join(d2f, on=(Design.design_id == d2f.design_id))\
                    .join(Field, on=(Field.pk == d2f.field_pk))\
                    .join(targetdb.Version).switch(targetdb.Field)\
                    .join(targetdb.Observatory).switch(targetdb.Field)\
                    .join(dbCad)\
                    .switch(d2s)\
                    .join(opsdb.CompletionStatus, JOIN.LEFT_OUTER)\
                    .where((Field.version == dbVersion) &
                        (targetdb.Version.plan == rs_version) & 
                        (targetdb.Observatory.label == loc.upper()))).count()


    designs = np.zeros(ndesigns, dtype=design_dtype)


    dquery = d2s.select(d2s.mjd, 
                        dbCad.label.alias('cadence'), 
                        Field.racen, 
                        Field.deccen,
                        Field.position_angle, 
                        Field.field_id, 
                        opsdb.CompletionStatus.label.alias('completion_status'),
                        Design.design_id,
                        Design.design_mode_label.alias('design_mode'),
                        Design.mugatu_version,
                        Design.run_on,
                        targetdb.Observatory.label.alias('observatory'))\
                .join(Design)\
                .join(d2f, on=(Design.design_id == d2f.design_id))\
                .join(Field, on=(Field.pk == d2f.field_pk))\
                .join(targetdb.Version).switch(targetdb.Field)\
                .join(targetdb.Observatory).switch(targetdb.Field)\
                .join(dbCad)\
                .switch(d2s)\
                .join(opsdb.CompletionStatus, JOIN.LEFT_OUTER)\
                .where((Field.version == dbVersion) &
                    (targetdb.Version.plan == rs_version) & 
                    (targetdb.Observatory.label == loc.upper())).dicts()

    castn = dict()
    for n in designs.dtype.names:
        castn[n] = np.cast[type(designs[n][0])]

    for indx, d in enumerate(dquery):
        for n in designs.dtype.names:
            if(d[n] is not None):
                designs[n][indx] = castn[n](d[n])

    return designs

    
def find_means(data):
    n_data = len(data)
    f = []
    x = np.sort(data[0]['mjd'])
    xmin = min(x)
    xmax = max(x)
    xnew = np.linspace(min(x), max(x), num = int(max(x)-min(x)))
    for i in range(n_data):
        x = np.sort(data[i]['mjd'])
        y = np.array(range(len(data[i]['mjd'])))+1
        ff = interp1d(x,y, fill_value='extrapolate')
        f.append(ff(xnew))
        #plt.scatter(xnew, ff(xnew), s=1, alpha=0.1)
    
    
    f_mean = np.mean(f, axis=0)
    f_25 = np.quantile(f, 0.25, axis=0)
    f_50 = np.quantile(f, 0.5, axis=0)
    f_75 = np.quantile(f, 0.75, axis=0)
    #plt.plot(xnew, f_mean, linewidth=4)
    #plt.plot(xnew, f_25)
    #plt.plot(xnew, f_50)
    #plt.plot(xnew, f_75)
    
    return xnew-15.,f,f_mean, f_25, f_50, f_75  


def designVsMjd(design_data):
    doneMjds = design_data['mjd'][np.where(design_data["completion_status"] == "done")]

    start_date = np.min(doneMjds)
    end_date = np.max(doneMjds)

    design_mjd = np.arange(start_date, end_date, 1)

    design_mjd = [int(m) for m in design_mjd]

    design_count = [len(np.where(np.array(doneMjds) < m)[0]) for m in design_mjd]

    design_t = Time(design_mjd, format='mjd')

    time_file = f'/home/sdss5/tmp/metrics_plots/time_avail_{loc}.csv'
    time_array = np.genfromtxt(time_file, names=True, delimiter=",", dtype=None, encoding="UTF-8")

    if loc == "apo":
        dark_design = 23
        bright_design = 21
        dark_factor = 1.9
        bright_factor = 1.1
        weather = 0.5
    else:
        dark_design = 24
        bright_design = 21
        dark_factor = 1.9
        bright_factor = 1.1
        weather = 0.7

    dark_design = 23 / 60
    bright_design = 21 / 60

    bright_factor = 1.1
    dark_factor = 1.9

    end_date = np.max(design_data['mjd'])

    subset = time_array[time_array["mjd"] < end_date]

    # divided by 2 again for weather
    max_bright = subset["cum_bright"] / bright_design * weather
    adjusted_bright = max_bright / bright_factor
    max_dark = subset["cum_dark"] / dark_design * weather
    adjusted_dark = max_dark / dark_factor

    # total = max_bright + max_dark
    realistic_total = adjusted_bright + adjusted_dark

    # count = np.array(range(len(first_year_data['mjd'])))+1
    t = Time(np.sort(subset["mjd"]), format='mjd')

    now = datetime.now()
    plt.plot(t.to_datetime(), realistic_total, '.', label='baseline')
    plt.plot(design_t.to_datetime(), design_count, '.', label='Observed')
    plt.xlabel('Date')
    plt.ylabel('Cumulative Number of Designs')
    plt.legend()
    plt.title('Designs as of ' + now.strftime("%m/%d/%Y %H:%M:%S"))
    plt.tight_layout()
    plt.savefig(str(plotfilepath + 'cumulative_designs_today.png'), dpi=300)
    plt.close()

    plt.plot(subset["mjd"], realistic_total, '.', label='baseline')
    plt.plot(design_mjd, design_count, '.', label='Observed')
    plt.xlabel('Date')
    plt.ylabel('Cumulative Number of Designs')
    plt.legend()

    plt.title('Designs as of ' + now.strftime("%m/%d/%Y %H:%M:%S"))
    plt.tight_layout()
    plt.savefig(str(plotfilepath + 'cumulative_designs_today_mjd.png'), dpi=300)
    plt.close()


    min_mjd_plot = min(design_mjd) - buffer_mjd 
    max_mjd_plot = max(design_mjd) + 4*buffer_mjd

    return min_mjd_plot, max_mjd_plot


# plt.plot(t.to_datetime(), count, '.', label='baseline')
# plt.plot(design_t.to_datetime(), design_count, '.', label='Observed')

# plt.xlabel(f'Date - First Year of SDSS V at {loc.upper()}')
# plt.ylabel('Cumulative Number of Designs')
# plt.xlim([Time(min_mjd_plot, format='mjd').to_datetime(),Time(max_mjd_plot, format='mjd').to_datetime()])
# plt.ylim(-10, max(design_count)*buffer_count)
# plt.legend()
# plt.title('Designs as of ' + now.strftime("%m/%d/%Y %H:%M:%S"))
# plt.gcf().autofmt_xdate()
# plt.tight_layout()
# plt.savefig(str(plotfilepath + 'cumulative_designs_during_year1_zoom.png'), dpi=300)
# plt.close()

def cadenceCount(obs_data, first_year_data, ):
    #designs by cadence
    labels, counts = np.unique(obs_data['cadence'],return_counts=True)  #all of the cadences
    labels1, counts1 = np.unique(first_year_data['cadence'],return_counts=True)  #cadences from the first year

    labels = np.array([c[:c.index("_v")] for c in labels])
    labels1 = np.array([c[:c.index("_v")] for c in labels1])

    fig, (ax1) = plt.subplots(1, 1, figsize=(20,10))

    g = (design_data['completion_status'] == 'done')
    #plt.subplots(figsize=(20, 10))

    ticks = range(len(counts))
    #ax1.bar(ticks,counts, align='center', label='Projected')
    #plt.xticks(ticks, labels,rotation='vertical');

    cadence_col = design_data[g]['cadence']
    cadences = []

    for col in cadence_col:
        cadences.append(col[:-3])
        
    labels2, counts2 = np.unique(cadences,return_counts=True)  #completed cadences

    labels3 = labels  #copy all of the labels
    counts3 = np.zeros(len(labels))  #zero out counts

    labels_proj = labels  #make a copy of labels for the 1st year projection
    labels_obs = labels   #make a copy of labels for the completed cadences

    counts_obs = np.zeros(len(labels))  #zeros
    counts_proj = np.zeros(len(labels))  #zeros


    labels_proj[np.in1d(labels, labels1)]  = labels[np.in1d(labels, labels1)] 
    labels_proj[np.logical_not(np.in1d(labels, labels1))] = labels[np.logical_not(np.in1d(labels, labels1))]
    counts_proj[np.in1d(labels, labels1)]  = counts1 


    labels_obs[np.in1d(labels, labels2)]  = labels[np.in1d(labels, labels2)] 
    labels_obs[np.logical_not(np.in1d(labels, labels2))] = labels[np.logical_not(np.in1d(labels, labels2))]

    counts_obs[np.in1d(labels, labels2)]  = counts2 




    ax1.bar(ticks,counts_proj, align='center', label='Projection - 1st year')
    plt.xticks(ticks, labels_proj,rotation='vertical');

    ax1.bar(ticks,counts_obs, align='center', label='Observed')
    plt.xticks(ticks, labels_obs,rotation='vertical');

    plt.title('Design Completion (First Year) as of ' + now.strftime("%m/%d/%Y %H:%M:%S"))

    #plt.yscale('log')
    plt.ylabel('Number')
    plt.legend()
    plt.tight_layout()
    plt.savefig(str(plotfilepath + 'designs_during_year1_by_cadence_linear.png'), dpi=300)
    plt.close()

    fig, (ax1) = plt.subplots(1, 1, figsize=(20,10))
    ax1.bar(ticks,counts_proj, align='center', label='Projected')
    plt.xticks(ticks, labels_proj,rotation='vertical');
    ax1.bar(ticks,counts_obs, align='center', label='Observed')
    plt.xticks(ticks, labels_obs,rotation='vertical');
    plt.title('Design Completion (First Year) as of ' + now.strftime("%m/%d/%Y %H:%M:%S"))
    plt.yscale('log')
    plt.ylabel('Number')
    plt.legend()
    plt.tight_layout()
    plt.savefig(str(plotfilepath + 'designs_during_year1_by_cadence_log.png'), dpi=300)
    plt.close()

    fig, (ax1) = plt.subplots(1, 1, figsize=(20,10))

    ax1.bar(ticks,(counts_obs/counts_proj)*100., align='center')
    plt.xticks(ticks, labels_obs,rotation='vertical');
    plt.title('Design Completion (First Year) as of ' + now.strftime("%m/%d/%Y %H:%M:%S"))
    plt.ylabel('Percent');
    plt.tight_layout()
    plt.savefig(str(plotfilepath + 'designs_during_year1_by_cadence_percent.png'), dpi=300)
    plt.close()

def rm_aqmes(first_year_data, design_data):
    rm = (first_year_data['cadence'] == 'dark_174x8')
    aqmes_med = (first_year_data['cadence'] == 'dark_10x4_4yr')
    aqmes_wide = (first_year_data['cadence'] == 'dark_2x4')

    g = (design_data['completion_status'] == 'done')
    h = (design_data['cadence'] == 'dark_10x4_4yr_v1')
    i = np.logical_and(g,h)
    design_mjd = design_data[i]['mjd']
    design_count = np.array(range(len(design_mjd)))+1
    design_t = Time(np.sort(design_mjd), format='mjd')

    count = np.array(range(len(first_year_data[aqmes_med]['mjd'])))+1
    t = Time(np.sort(first_year_mjd[aqmes_med]), format='mjd')

    plt.plot(t.to_datetime(), count, '.', label='baseline')
    plt.plot(design_t.to_datetime(), design_count, '.', label='Observed')
    plt.xlabel(f'Date - First Year of SDSS V at {loc.upper()}')
    plt.title('AQMES Med Designs as of ' + now.strftime("%m/%d/%Y %H:%M:%S"))
    plt.xlim([Time(min_mjd_plot, format='mjd').to_datetime(),Time(max_mjd_plot, format='mjd').to_datetime()])
    plt.ylim(-10, max(design_count)*buffer_count)
    plt.ylabel('Cumulative Number of Designs')
    plt.legend()
    plt.gcf().autofmt_xdate()

    plt.tight_layout()
    plt.savefig(str(plotfilepath + 'AQMES_Med_cumulative_designs_during_year1.png'), dpi=300)
    plt.close()


    g = (design_data['completion_status'] == 'done')
    h = (design_data['cadence'] == 'dark_2x4_v1')
    i = np.logical_and(g,h)
    design_mjd = design_data[i]['mjd']
    design_count = np.array(range(len(design_mjd)))+1
    design_t = Time(np.sort(design_mjd), format='mjd')

    count = np.array(range(len(first_year_data[aqmes_wide]['mjd'])))+1
    t = Time(np.sort(first_year_mjd[aqmes_wide]), format='mjd')

    plt.plot(t.to_datetime(), count, '.', label='baseline')
    plt.plot(design_t.to_datetime(), design_count, '.', label='Observed')
    plt.xlabel(f'Date - First Year of SDSS V at {loc.upper()}')
    plt.title('AQMES Wide Designs as of ' + now.strftime("%m/%d/%Y %H:%M:%S"))
    plt.xlim([Time(min_mjd_plot, format='mjd').to_datetime(),Time(max_mjd_plot, format='mjd').to_datetime()])
    plt.ylim(-10, max(design_count)*buffer_count)
    plt.ylabel('Cumulative Number of Designs')
    plt.legend()
    plt.gcf().autofmt_xdate()

    plt.tight_layout()
    plt.savefig(str(plotfilepath + 'AQMES_Wide_cumulative_designs_during_year1.png'), dpi=300)
    plt.close()

    g = (design_data['completion_status'] == 'done')
    h = (design_data['cadence'] == 'dark_174x8_v1')
    i = np.logical_and(g,h)
    design_mjd = design_data[i]['mjd']
    design_count = np.array(range(len(design_mjd)))+1
    design_t = Time(np.sort(design_mjd), format='mjd')

    count = np.array(range(len(first_year_data[rm]['mjd'])))+1
    t = Time(np.sort(first_year_mjd[rm]), format='mjd')

    plt.plot(t.to_datetime(), count, '.', label='baseline')
    plt.plot(design_t.to_datetime(), design_count, '.', label='Observed')
    plt.xlabel(f'Date - First Year of SDSS V at {loc.upper()}')
    plt.title('RM Designs as of ' + now.strftime("%m/%d/%Y %H:%M:%S"))
    plt.xlim([Time(min_mjd_plot, format='mjd').to_datetime(),Time(max_mjd_plot, format='mjd').to_datetime()])
    plt.ylim(-10, max(design_count)*buffer_count)
    plt.ylabel('Cumulative Number of Designs')
    plt.legend()
    plt.gcf().autofmt_xdate()

    plt.tight_layout()
    plt.savefig(str(plotfilepath + 'RM_cumulative_designs_during_year1.png'), dpi=300)
    plt.close()

# filepath = '/Users/jbochanski/Dropbox/weather_mc/'
# field_filenames = glob.glob(filepath+'zeta*fits')

# data = read_field_files(field_filenames)
# xnew, f,f_mean,  f_25, f_50, f_75 = find_means(data)

# plt.plot(xnew, f_50, linewidth=4, label='Median')
# plt.fill_between(xnew, f_25, f_75, alpha=0.3, label='25-75%')
# plt.fill_between(xnew, np.quantile(f, 0.1, axis=0), np.quantile(f, 0.9, axis=0), alpha=0.1, label='10-90%')

def weather(design_data):
    g = (design_data['completion_status'] == 'done')
    design_mjd = design_data[g]['mjd']
    design_count = np.array(range(len(design_mjd)))+1
    design_t = Time(np.sort(design_mjd), format='mjd')
    plt.plot(np.sort(design_mjd), design_count, '.', label='Observed')

    min_mjd_plot = min(design_mjd) - buffer_mjd 
    max_mjd_plot = max(design_mjd) + 4*buffer_mjd
    plt.legend()
    plt.xlim(min_mjd_plot, max_mjd_plot)
    plt.ylim(-20, max(design_count)*buffer_count)
    plt.gcf().autofmt_xdate()
    plt.xlabel('MJD')
    plt.ylabel('Completed Designs')
    plt.tight_layout()
    plt.savefig(str(plotfilepath + 'weather_spread_cumulative_mjd.png'), dpi=300)
    plt.close()

    # x_t = Time(xnew, format='mjd')
    # scale = .70
    # plt.plot(x_t.to_datetime(), f_50*scale, linewidth=4, label='Median')
    # plt.fill_between(x_t.to_datetime(), f_25*scale, f_75*scale, alpha=0.3, label='25-75%')
    # plt.fill_between(x_t.to_datetime(), np.quantile(f, 0.1, axis=0)*scale, np.quantile(f, 0.9, axis=0)*scale, alpha=0.1, label='10-90%')

    g = (design_data['completion_status'] == 'done')
    design_mjd = design_data[g]['mjd']
    design_count = np.array(range(len(design_mjd)))+1
    design_t = Time(np.sort(design_mjd), format='mjd')
    plt.plot(design_t.to_datetime(), design_count, '.', label='Observed')

    min_mjd_plot = min(design_mjd) - buffer_mjd 
    max_mjd_plot = max(design_mjd) + 4*buffer_mjd
    now = datetime.now()
    plt.legend()
    plt.xlim([Time(min_mjd_plot, format='mjd').to_datetime(),Time(max_mjd_plot, format='mjd').to_datetime()])
    plt.ylim(-20, max(design_count)*buffer_count)
    plt.title('Design Completion as of ' + now.strftime("%m/%d/%Y %H:%M:%S"))
    plt.gcf().autofmt_xdate()
    plt.xlabel('MJD')
    plt.ylabel('Completed Designs')
    plt.tight_layout()
    plt.savefig(str(plotfilepath + 'weather_spread_cumulative_calendar.png'), dpi=300)
    plt.close()


def onSky(design_data):
    g = (design_data['completion_status'] == 'done')
    ra_design_all = coord.Angle(-(design_data[g]['racen']+90)*un.degree)
    dec_design_all = coord.Angle(design_data[g]['deccen']*un.degree)

    fig = plt.figure(figsize=(12,6))
    ax = fig.add_subplot(111, projection="mollweide")
    ra_design_all = ra_design_all.wrap_at(180*un.degree)
    dates = Time(design_data[g]['mjd'], format='mjd').decimalyear
    d =ax.scatter(ra_design_all.radian, dec_design_all.radian, s=40, cmap='viridis', alpha=0.5, marker='h')
    plt.title('Completed Designs')
    plt.tight_layout()
    plt.savefig(str(plotfilepath + 'completed_designs_on_sky.png'), dpi=300)
    plt.close()

    fig = plt.figure(figsize=(12,6))
    ax = fig.add_subplot(111, projection="mollweide")
    ra_design_all = ra_design_all.wrap_at(180*un.degree)
    h = (design_data[g]['design_mode'] == 'bright_time')
    i = (design_data[g]['design_mode'] == 'dark_faint') 
    j = (design_data[g]['design_mode'] == 'dark_monit') 
    k = (design_data[g]['design_mode'] == 'dark_plane') 
    l = (design_data[g]['design_mode'] ==  'dark_rm') 

    d =ax.scatter(ra_design_all[h].radian, dec_design_all[h].radian, s=50, alpha=0.5, label='bright_time', marker='h')
    d =ax.scatter(ra_design_all[i].radian, dec_design_all[i].radian, s=50, alpha=0.5, label='dark_faint', marker='h')
    d =ax.scatter(ra_design_all[j].radian, dec_design_all[j].radian, s=50, alpha=0.5, label='dark_monit', marker='h')
    d =ax.scatter(ra_design_all[k].radian, dec_design_all[k].radian, s=50, alpha=0.5, label='dark_plane', marker='h')
    d =ax.scatter(ra_design_all[l].radian, dec_design_all[l].radian, s=50, alpha=0.5, label= 'dark_rm', marker='h')
    plt.legend(fancybox=True, frameon=True, loc='lower center')
    plt.title('Completed Designs')
    plt.tight_layout()
    plt.savefig(str(plotfilepath + 'completed_designs_Jul7_by_mode.png'), dpi=300)
    plt.close()

# #url = 'https://wiki.sdss.org/rest/api/content/115082850/child/attachment'
# url = 'https://wiki.sdss.org/rest/api/content/115082850/child/attachment/115082889/data'
# headers = {"X-Atlassian-Token": "nocheck"}
# data = {"comment":"metrics plot - cumulative with weather spread "}


# # please, uncomment to attach inline content
# #files = {'file': ('report.xml', '&lt;?xml version="1.0" encoding="UTF-8"?&gt;&lt;note&gt;&lt;to&gt;RECIPIENT&lt;/to&gt;&lt;from&gt;SENDER&lt;/from&gt;&lt;heading&gt;ATTACHMENT&lt;/heading&gt;&lt;body&gt;CONTENT&lt;/body&gt;&lt;/note&gt;')}

# # please uncomment to attach external file
# #files = {'file': open('text.txt', 'rb')}
# files = {'file': open(str(plotfilepath + 'weather_spread_cumulative_calendar.png'), 'rb')}

# # upload file to page
# # [USERNAME], i.e.: admin
# # [PASSWORD], i.e.: admin
# #r = requests.post(url, data=data, auth=('jbochanski', '}jxmpKP4Dbjd2M4'), files=files, headers=headers)

if __name__ == "__main__":
    rs_version = os.getenv("RS_VERSION")
    loc = os.getenv("OBSERVATORY").lower()

    filepath = '/home/sdss5/tmp/metrics_plots/'
    filepath = os.path.join(filepath, f"{rs_version}-{loc}")

    plotfilepath = filepath + "/"

    # Check whether the specified path exists or not
    isExist = os.path.exists(plotfilepath)

    if not isExist:
        # Create a new directory because it does not exist 
        os.makedirs(plotfilepath)
        print('made new directory')

    design_data = pullDesigns()

    designVsMjd(design_data)
    onSky(design_data)
    # weather(design_data)
