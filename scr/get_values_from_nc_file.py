"""

This script proceses the data from the files
daily-avhrr-sce-nhl_ease-50_201503291200.nc

Read the template obs file in grib format.
Read the snow data. Replace where there is data to snow observations.
Find the indices where the obs data is defined.
Save all to ascii files.

NOTE: the snow data is converted to binary format here:
setting snow as 1.0 if snow  prob is >= 90 % or zero otherwise

"""

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
import pyproj

import pandas as pd
from datetime import datetime

def get_snow_orig(df_ll:pd.DataFrame, ds:xr.Dataset, params: list) -> list:
    all_values = OrderedDict()
    for param in params:
        all_values[param] = []
    #define projections to convert xc and yc coordinates in file to lat lon
    central_lon = ds["Lambert_Azimuthal_Grid"].attrs["longitude_of_projection_origin"]
    central_lat = ds["Lambert_Azimuthal_Grid"].attrs["latitude_of_projection_origin"]
    projection_params = { 'proj': 'laea', 'ellps': 'WGS84', 'lat_0': central_lat, 'lon_0': central_lon }
    # Define the Lambert Azimuthal Equal Area projection using Cartopy
    laea_projection = ccrs.LambertAzimuthalEqualArea( central_latitude=projection_params['lat_0'], central_longitude=projection_params['lon_0'], 
                            globe=ccrs.Globe(ellipse=projection_params['ellps']))

    # Define the original projection of the dataset using pyproj.CRS
    original_projection = pyproj.CRS.from_proj4('+proj=laea +ellps=WGS84 +lat_0=90 +lon_0=0')

    for lat,lon in zip(df_ll.lat,df_ll.lon):
        # Convert latitude and longitude to Lambert Azimuthal Grid coordinates
        desired_xc, desired_yc = pyproj.Transformer.from_crs(ccrs.PlateCarree(), original_projection).transform(lon, lat)
        for param in params:
            value_at_point = ds[param].sel(xc=desired_xc, yc=desired_yc,method="nearest").values[0]
            if np.isnan(value_at_point):
                value_at_point = 9999.
            all_values[param].append(value_at_point)
    all_values["lat"] = df_ll.lat.to_list()
    all_values["lon"] = df_ll.lon.to_list()
    return all_values

def get_snow_by_threshold(df_ll:pd.DataFrame, ds:xr.Dataset, parameter:str, prob_thr:float) -> list:
    """
    Uses variable classed_value_o
    with pixel class: -1=ocean, 0=nodata, 1=no snow, 2=snow, 4=cloud
    """
    all_values=[]
    #define projections to convert xc and yc coordinates in file to lat lon
    central_lon = ds["Lambert_Azimuthal_Grid"].attrs["longitude_of_projection_origin"]
    central_lat = ds["Lambert_Azimuthal_Grid"].attrs["latitude_of_projection_origin"]
    projection_params = { 'proj': 'laea', 'ellps': 'WGS84', 'lat_0': central_lat, 'lon_0': central_lon }
    # Define the Lambert Azimuthal Equal Area projection using Cartopy
    laea_projection = ccrs.LambertAzimuthalEqualArea( central_latitude=projection_params['lat_0'], central_longitude=projection_params['lon_0'], 
                            globe=ccrs.Globe(ellipse=projection_params['ellps']))

    # Define the original projection of the dataset using pyproj.CRS
    original_projection = pyproj.CRS.from_proj4('+proj=laea +ellps=WGS84 +lat_0=90 +lon_0=0')
    for lat,lon in zip(df_ll.lat,df_ll.lon):
        # Convert latitude and longitude to Lambert Azimuthal Grid coordinates
        desired_xc, desired_yc = pyproj.Transformer.from_crs(ccrs.PlateCarree(), original_projection).transform(lon, lat)
        value_at_point = ds[var_nc].sel(xc=desired_xc, yc=desired_yc,method="nearest").values[0]

        if np.isnan(value_at_point):
            value_at_point = 9999.
        else:
            if "prob" in parameter:
                if value_at_point >= prob_thr:
                    value_at_point = 1.0
                else:
                    value_at_point = 0.0

            elif parameter == "classed_value_o":

                if value_at_point == 2:
                    value_at_point = 1.0
                elif value_at_point == 1:
                    value_at_point = 0.0
                else:
                    value_at_point = 9999.
            else: 
                print(f"Parameter {parameter} unknown")
                sys.exit(1)
        all_values.append(value_at_point)
    return all_values

if __name__ == "__main__":
    DATA="/ec/res4/scratch/nhd/CERISE/"
    origin="no-ar-cw"
    param_code = 260289

    if len(sys.argv) == 1:
        print("Please provide the input nc file, the list of lat lon to process and the output file")
        sys.exit(1)
    else:
        infile = sys.argv[1] #the nc file with the data
        csv_ll = sys.argv[2] # the lat and lon values from the model grid 
        out_csv = sys.argv[3] # the csv file where the interpolated values from the nc files will be written
    dump_type = "original"   
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
    if dump_type == "by_threshold":
        prob_thr = 90. #set everything above this thresold to 1, otherwise 0
        var_nc = "prob_snow_o" #'prob_snow_c'
        all_values = get_snow_by_threshold(df_ll, ds, var_nc, prob_thr)
        print(f"Writing the data to {out_csv}") 
        df_out = pd.DataFrame({"lat":df_ll.lat.values,"lon":df_ll.lon.values,"snow_no_snow":all_values})
        df_out.to_csv(out_csv,index=False)
    elif dump_type == "original":
        params = ["prob_snow_o","classed_value_o"]
        all_values = get_snow_orig(df_ll, ds, params)
        df_out = pd.DataFrame(all_values)
        df_out.to_csv(out_csv,index=False)
