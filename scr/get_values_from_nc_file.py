"""
Read the template obs file in grib format.
Read the snow data. Replace where there is data to snow observations.
Find the indices where the obs data is defined.
Save all to ascii files.

NOTE: the snow data is converted to binary format here:
setting snow as 1.0 if snow  prob is >= 90 % or zero otherwise

"""
snow_thres = 90 #values equal or above this are set to 1

import os
import sys
import re
import eccodes as ecc
import numpy as np
import calendar
from pathlib import Path
import pandas as pd
from collections import OrderedDict
import xarray as xr

import cartopy.crs as ccrs
import pandas as pd
from datetime import datetime

def get_indices_snow_nc(param_code:int, cryo_file:str,infile:str) -> list:
    save_index=[]; save_snow=[]
    print(f"Processing {cryo_file}")
    obs["date"],obs["lat"],obs["lon"],obs["snowc"] = get_data_fromtxt(cryo_file)
    df_obs = pd.DataFrame(obs)
    file_date = os.path.split(cryo_file)[-1].split("_")[-1].replace(".dat","")
    gfile = open(infile)
    for _,r in df_obs.iterrows():
        lat = r.lat
        lon = r.lon
        #snow = r.snowc/100.
        if r.snowc >= snow_thres:
            snow = 1.0
        else:
            snow = 0.0
        obs_date = r.date
        #gfile = open(infile)
        #with open(infile) as f:
        while True:
            msg = ecc.codes_grib_new_from_file(gfile) #gfile) #f)
            #msg = ecc.codes_grib_new_from_file(f)
            if msg is None: 
                #gfile.close()
                break
            param = ecc.codes_get_long(msg, 'param')
            date = ecc.codes_get_long(msg, "date")
            hour = ecc.codes_get_long(msg, "time")
            date_file = int(obs_date[0:8])
 
            if (param == param_code) and date_file == date and hour == 600:
                latlonidx = ecc.codes_grib_find_nearest(msg,lat,lon)
                change_index = latlonidx[0]["index"]
                print(f"Index to change {change_index}")
                #print(f"Before modifying: {values_modify[change_index]}")
                #print(f"Now changing to {snow}")
                #values_modify[change_index] = snow
                save_index.append(change_index)
                save_snow.append(snow)
                # Monitor memory usage
                #object_size = sys.getsizeof(msg)
                #print(f"Message size {object_size}")
                #gc.collect()
                #break
            #else:
            #    print(f"Finding {param}, {date} and {hour} in {date_file} ")
    gfile.close()
    del df_obs
    return save_index, save_snow
def get_indices_lat_lon(param_code:int, cryo_file:str,infile:str,lat:float,lon:float, obs_date:str) -> list:
    gfile = open(infile)
    date_file = int(obs_date[0:8])
    while True:
        msg = ecc.codes_grib_new_from_file(gfile) #gfile) #f)
        #msg = ecc.codes_grib_new_from_file(f)
        if msg is None: 
            #gfile.close()
            break
        param = ecc.codes_get_long(msg, 'param')
        date = ecc.codes_get_long(msg, "date")
        hour = ecc.codes_get_long(msg, "time")
        if (param == param_code) and date_file == date and hour == 600:
            latlonidx = ecc.codes_grib_find_nearest(msg,lat,lon)
            change_index = latlonidx[0]["index"]
            #print(f"Index to change {change_index}")
    gfile.close()
    return change_index



if __name__ == "__main__":
    DATA="/ec/res4/scratch/nhd/CERISE/"
    origin="no-ar-cw"
    param_code = 260289
    prob_thr = 90. #set everything above this thresold to 1, otherwise 0

    if len(sys.argv) == 1:
        print("Please provide the input nc file and the list of lat lon to process")
        sys.exit(1)
    else:
        infile = sys.argv[1]
        csv_ll = sys.argv[2]
        
    # these are all the lat lon from model
    df_ll = pd.read_csv(csv_ll)
    
    if os.stat(infile).st_size==0:
        print(f"{infile} is empty!")
    date_file = infile.split("_")[-1].replace(".nc","")[0:8]
    ds = xr.open_dataset(infile,engine='netcdf4')
    # check the time in the file
    ts = ds["time"].values[0]
    dt_obj =pd.to_datetime(ts,unit="s")
    dt_str = datetime.strftime(dt_obj,"%Y%m%d%H")
    print(f"Timestamp in the file {infile}: {dt_str}")
    all_values=[]
    central_lon = ds["Lambert_Azimuthal_Grid"].attrs["longitude_of_projection_origin"]
    central_lat = ds["Lambert_Azimuthal_Grid"].attrs["latitude_of_projection_origin"]
    data_crs = ccrs.LambertConformal(central_longitude=central_lon,central_latitude=central_lat)
    var_nc = "prob_snow_o" #'prob_snow_c'
    for lat,lon in zip(df_ll.lat,df_ll.lon):
        #lat_index = (ds['lat'] - lat).argmin().item()
        #lon_index = (ds['lon'] - lon).argmin().item()
        #lat_index = abs(ds['yc'] - lat).argmin(dim='yc').item()
        #lon_index = abs(ds['xc'] - lon).argmin(dim='xc').item()
        #value_at_point = ds[var_nc].values[0,lon_index,lat_index]
        test_lat = 72.366
        test_lon = -31.920
        x, y = data_crs.transform_point(x=lon, y=lat, src_crs=ccrs.PlateCarree())
        value_at_point = ds[var_nc].sel(xc=x, yc=y,method="nearest").values[0]
        #selected_data = ds['prob_snow_o'].sel( xc=ds['lon'].sel(lat=test_lat, method='nearest').values, yc=ds['lat'].sel(lon=test_lon, method='nearest').values, method='nearest')
projection_params = { 'proj': 'laea', 'ellps': 'WGS84', 'lat_0': 90, 'lon_0': 0 }
laea_projection = ccrs.LambertAzimuthalEqualArea( central_latitude=projection_params['lat_0'], central_longitude=projection_params['lon_0'], globe=ccrs.Globe(ellipse=projection_params['ellps']))

        import pdb
        pdb.set_trace()

        if np.isnan(value_at_point):
            value_at_point = 9999.
        else:
            if value_at_point >= prob_thr:
                value_at_point = 1.0
            else:
                value_at_point = 0.0
        all_values.append(value_at_point)
        #find_closest = ds['prob_snow_c'].sel(lat=lat, lon=lon).item()
     
    df_out = pd.DataFrame({"lat":df_ll.lat.values,"lon":df_ll.lon.values,"snow_no_snow":all_values})
    df_out.to_csv(f"all_lat_lons_snow_ordered_{date_file}.csv",index=False)
