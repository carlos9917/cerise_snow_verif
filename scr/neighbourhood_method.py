"""
Script based on Fabiola's idea to search for the nearest points
and implement the neighbourhood verification method
of Mittermeier

"""

import xarray as xr
import pandas as pd
import datetime
import numpy as np
import re
from scipy.spatial import KDTree
import pdb
import sys


if __name__=="__main__":
    EXP="CARRA"
    param_obs = "fscov"
    param_fcst = "fscov"
    grib_fcst = "/ec/res4/scratch/nhd/CERISE/MODEL_DATA/snow_cover_201505_ll_grid_600.grib2"
    grib_obs = "/ec/res4/scratch/nhd/CERISE/CRYO_SW/obs_201505_600.grib2"
    n = 3
    if n == 3:
            nrange = 2
            domain = '3x3domain'
    if n == 5:
            nrange = 4
            domain = '5x5domain'
    if n == 7:
        nrange = 6
        domain = '7x7domain'
    #Define output columns name
    ilist=['lon', 'lat', f'{EXP}']
    col_name = [x + str(i) for i in range(1,(n*n)+1) for x in ilist]
    output = pd.DataFrame(columns=['fcdate', 'validdate', 'leadtime', 'parameter', 'units', 'SID', 'ELEV', 'lon', 'lat', f'{param_obs}'])
    output = pd.concat([output,pd.DataFrame(columns=col_name)])
    model = xr.open_dataset(grib_fcst,engine='cfgrib', backend_kwargs={'filter_by_keys':{'shortName': param_fcst}})
    dtime_fcst = model['time'].values 
    print(dtime_fcst)
    obs = xr.open_dataset(grib_fcst,engine='cfgrib', backend_kwargs={'filter_by_keys':{'shortName': param_fcst}})
    dtime_obs = obs['time'].values 
    print(dtime_obs)


    valid_dtime = pd.to_datetime(model['valid_time'].values, format='%Y%m%d%H%M')
    hours = valid_dtime.strftime('%H')
    for vtime in valid_dtime:
        date = vtime.isoformat().replace("-", "")
        date_fcst = date.split("T")[0]
        #obs_not_nan = obs["fscov"].data
        #obs_not_nan = obs.dropna(dim="fscov")
        ds = obs.dropna(dim='time', subset={param_obs: [np.nan, None]})
        import pdb
        pdb.set_trace()


