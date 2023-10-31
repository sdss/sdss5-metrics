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
#seems like an ok default

def read_field_files(filelist):
    n_files = len(filelist)
    data = []
    for n in range(n_files):
        hdu = fits.open(str(field_filenames[n]))
        hdu.verify('fix')
        data.append(hdu[1].data)
    return(data)
    
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

rs_version = os.getenv("RS_VERSION")
loc = os.getenv("OBSERVATORY").lower()

filepath = '/home/sdss5/tmp/metrics_plots/'
filepath = os.path.join(filepath, f"{rs_version}-{loc}")
field_filename = f'{rs_version}-{loc}-fields-0.fits'
field_filename = os.path.join(filepath, field_filename)
observations_filename = f'{rs_version}-{loc}-observations-0.fits'
observations_filename = os.path.join(filepath, observations_filename)

apo_designs = os.path.join(filepath,'designs.fits')

plotfilepath = filepath + "/"

# Check whether the specified path exists or not
isExist = os.path.exists(plotfilepath)

if not isExist:
  
  # Create a new directory because it does not exist 
  os.makedirs(plotfilepath)
  print('made new directory')


hdu = fits.open(field_filename)
hdu.verify('fix')
field_data = hdu[1].data

hdu = fits.open(observations_filename)
hdu.verify('fix')
obs_data = hdu[1].data

hdu = fits.open(apo_designs)
hdu.verify('fix')
design_data = hdu[1].data

min_mjd = np.min(design_data['mjd'])
g = (obs_data['mjd'] < min_mjd + 365)  #look at the first year of data


first_year_data = obs_data[g]
first_year_mjd = obs_data[g]['mjd'] + 37 #cludge because observations started on Mar 1, not Jan 23

g = (design_data['completion_status'] == 'done')
design_mjd = design_data[g]['mjd']
design_count = np.array(range(len(design_mjd)))+1
design_t = Time(np.sort(design_mjd), format='mjd')

time_file = '/home/sdss5/tmp/metrics_plots/time_avail_apo.csv'
time_array = np.genfromtxt(time_file, names=True, delimiter=",", dtype=None, encoding="UTF-8")

dark_design = 23 / 60
bright_design = 21 / 60

bright_factor = 1.1
dark_factor = 1.8

end_date = np.max(design_data['mjd'])

subset = time_array[time_array["mjd"] < end_date]

# divided by 2 again for weather
max_bright = subset["cum_bright"] / bright_design / 2
adjusted_bright = max_bright / bright_factor
max_dark = subset["cum_dark"] / dark_design / 2
adjusted_dark = max_dark / dark_factor

total = max_bright + max_dark
realistic_total = adjusted_bright + adjusted_dark


# count = np.array(range(len(first_year_data['mjd'])))+1
t = Time(np.sort(subset["mjd"]), format='mjd')

now = datetime.now()
plt.plot(t.to_datetime(), realistic_total, '.', label='baseline')
plt.plot(design_t.to_datetime(), design_count, '.', label='Observed')
plt.xlabel('Date - First Year of SDSS V at APO')
plt.ylabel('Cumulative Number of Designs')
plt.legend()
plt.title('Designs as of ' + now.strftime("%m/%d/%Y %H:%M:%S"))
plt.tight_layout()
plt.savefig(str(plotfilepath + 'cumulative_designs_today.png'), dpi=300)
plt.close()

plt.plot(subset["mjd"], realistic_total, '.', label='baseline')
plt.plot(np.sort(design_mjd), design_count, '.', label='Observed')
plt.xlabel('Date - First Year of SDSS V at APO')
plt.ylabel('Cumulative Number of Designs')
plt.legend()

plt.title('Designs as of ' + now.strftime("%m/%d/%Y %H:%M:%S"))
plt.tight_layout()
plt.savefig(str(plotfilepath + 'cumulative_designs_today_mjd.png'), dpi=300)
plt.close()

buffer_mjd = 10.  
buffer_count = 5.1

min_mjd_plot = min(design_mjd) - buffer_mjd 
max_mjd_plot = max(design_mjd) + 4*buffer_mjd



# plt.plot(t.to_datetime(), count, '.', label='baseline')
# plt.plot(design_t.to_datetime(), design_count, '.', label='Observed')

# plt.xlabel('Date - First Year of SDSS V at APO')
# plt.ylabel('Cumulative Number of Designs')
# plt.xlim([Time(min_mjd_plot, format='mjd').to_datetime(),Time(max_mjd_plot, format='mjd').to_datetime()])
# plt.ylim(-10, max(design_count)*buffer_count)
# plt.legend()
# plt.title('Designs as of ' + now.strftime("%m/%d/%Y %H:%M:%S"))
# plt.gcf().autofmt_xdate()
# plt.tight_layout()
# plt.savefig(str(plotfilepath + 'cumulative_designs_during_year1_zoom.png'), dpi=300)
# plt.close()


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
plt.xlabel('Date - First Year of SDSS V at APO')
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
plt.xlabel('Date - First Year of SDSS V at APO')
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
plt.xlabel('Date - First Year of SDSS V at APO')
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

#url = 'https://wiki.sdss.org/rest/api/content/115082850/child/attachment'
url = 'https://wiki.sdss.org/rest/api/content/115082850/child/attachment/115082889/data'
headers = {"X-Atlassian-Token": "nocheck"}
data = {"comment":"metrics plot - cumulative with weather spread "}


# please, uncomment to attach inline content
#files = {'file': ('report.xml', '&lt;?xml version="1.0" encoding="UTF-8"?&gt;&lt;note&gt;&lt;to&gt;RECIPIENT&lt;/to&gt;&lt;from&gt;SENDER&lt;/from&gt;&lt;heading&gt;ATTACHMENT&lt;/heading&gt;&lt;body&gt;CONTENT&lt;/body&gt;&lt;/note&gt;')}

# please uncomment to attach external file
#files = {'file': open('text.txt', 'rb')}
files = {'file': open(str(plotfilepath + 'weather_spread_cumulative_calendar.png'), 'rb')}

# upload file to page
# [USERNAME], i.e.: admin
# [PASSWORD], i.e.: admin
#r = requests.post(url, data=data, auth=('jbochanski', '}jxmpKP4Dbjd2M4'), files=files, headers=headers)