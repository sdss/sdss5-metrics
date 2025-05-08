import numpy as np
import matplotlib.pyplot as plt
from astropy.time import Time

from metrics.dbConvenience import designQueryMjd

doneMjds = np.array(designQueryMjd())

start_date = np.min(doneMjds)
end_date = np.max(doneMjds)

design_mjd = np.arange(start_date, end_date, 1)

design_mjd = [int(m) for m in design_mjd]

cumulative_weeks = list()
cumulative_months = list()
cumulative_biweekly = list()
for m in design_mjd[30:]:
    w_mjds = np.where(np.logical_and(doneMjds > m - 7, doneMjds < m ))[0]
    rate = len(w_mjds) / 7
    cumulative_weeks.append(rate)
    
    w_mjds = np.where(np.logical_and(doneMjds > m - 30, doneMjds < m ))[0]
    rate = len(w_mjds) / 30
    cumulative_months.append(rate)
    
    w_mjds = np.where(np.logical_and(doneMjds > m - 14, doneMjds < m ))[0]
    rate = len(w_mjds) / 14
    cumulative_biweekly.append(rate)

formatted_time = Time(design_mjd[30:], format='mjd').to_datetime()

plt.figure()
plt.plot(formatted_time, cumulative_weeks)
plt.xticks(rotation=30, fontsize=10)
plt.savefig("progress_weekly_cumulative.png")

plt.figure()
plt.plot(formatted_time, cumulative_months)
plt.xticks(rotation=30, fontsize=10)
plt.savefig("progress_monthly_cumulative.png")

plt.figure()
plt.plot(formatted_time, cumulative_biweekly)
plt.xticks(rotation=30, fontsize=10)
plt.savefig("progress_biweekly_cumulative.png")

