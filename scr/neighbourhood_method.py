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
    dist = 1000
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
    obs = xr.open_dataset(grib_obs,engine='cfgrib', backend_kwargs={'filter_by_keys':{'shortName': param_fcst}})
    dtime_obs = obs['time'].values 
    print(dtime_obs)


    valid_dtime = pd.to_datetime(model['valid_time'].values, format='%Y%m%d%H%M')
    hours = valid_dtime.strftime('%H')
    lon_model = model['longitude'].values
    #Do I need to do this??
    #lon_model = (lon_model + 180) % 360 - 180 #convert from 0 - 360 to -180 - 180
    lat_model = model['latitude'].values
    points_model = list(zip(lon_model.flatten(),lat_model.flatten()))
    for k,vtime in enumerate(valid_dtime):
        date = vtime.isoformat().replace("-", "")
        date_fcst = date.split("T")[0]
        #obs_not_nan = obs["fscov"].data
        #obs_not_nan = obs.dropna(dim="fscov")
        #ds = obs.dropna(dim='time', subset={param_obs: [np.nan, None]})
        # these produces a tuple with the x and y dimensions of the indices
        not_nan_indices = np.where(~np.isnan(obs[param_fcst][k,:,:].values))
        lon_obs=[];lat_obs=[]
        for ilon,ilat in zip(not_nan_indices[0],not_nan_indices[1]):
            lon = obs[param_fcst][k,not_nan_indices[0][ilon],not_nan_indices[1][ilat]].longitude.values.item()
            lat = obs[param_fcst][k,not_nan_indices[0][ilon],not_nan_indices[1][ilat]].latitude.values.item()
            lon_obs.append(lon)
            lat_obs.append(lat)
        #if need to convert lon to same range as above
        #lon_obs = np.array(lon_obs)
        #lon_obs = (lon_obs + 180) % 360 - 180
        points_obs = np.vstack((lon_obs,lat_obs)).T
        kdtree = KDTree(points_model) #this is made of all the points in the forecast
        for pp in points_obs:
            print('obs point:', pp)
            dd, i = kdtree.query(pp, k=1) #find the nearest grid point to station. The grid of the obs is the same as fcst
            import pdb
            pdb.set_trace()
            #if dd <= dist:


