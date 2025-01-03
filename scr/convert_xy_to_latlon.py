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


def get_latlon(ds:xr.Dataset, parameter:str) -> list:
    """
    ds: the dataframe with the obs data
    parameter: the parameter I want to get
    """
    all_values=[]
    #define projections to convert xc and yc coordinates in file to lat lon
    #central_lon = ds["Lambert_Azimuthal_Grid"].attrs["longitude_of_projection_origin"]
    #central_lat = ds["Lambert_Azimuthal_Grid"].attrs["latitude_of_projection_origin"]
    #projection_params = { 'proj': 'laea', 'ellps': 'WGS84', 'lat_0': central_lat, 'lon_0': central_lon }
    # Define the Lambert Azimuthal Equal Area projection using Cartopy
    #laea_projection = ccrs.LambertAzimuthalEqualArea( central_latitude=projection_params['lat_0'], central_longitude=projection_params['lon_0'], 
    #                        globe=ccrs.Globe(ellipse=projection_params['ellps']))

    # Define the original projection of the dataset using pyproj.CRS
    #original_projection = pyproj.CRS.from_proj4('+proj=laea +ellps=WGS84 +lat_0=90 +lon_0=0')
    # Define the WGS84 projection
    #wgs84 = pyproj.CRS.from_epsg(4326)
    wgs84 = pyproj.Proj(proj="longlat", ellps="WGS84")

    
    # Define the Plate Carrée (equirectangular) projection
    plate_carree = pyproj.CRS.from_proj4('+proj=eqc +lat_ts=0 +lon_0=0 +x_0=0 +y_0=0 +datum=WGS84 +units=m +no_defs')
    # details from the netcdf file 

    # Define the transformer
    transformer = pyproj.Transformer.from_crs(wgs84, plate_carree)


    #geospatial_lat_min', 'geospatial_lat_max', 'geospatial_lon_min', 'geospatial_lon_max', 'geospatial_vertical_min', 'geospatial_vertical_max', 'geospatial_lon_resolution', 'geospatial_lat_resolution', 'geospatial_lat_units', 'geospatial_lon_units', 'time_coverage_start', 'time_coverage_end', 'time_coverage_duration', 'time_coverage_resolution', '
    for lat,lon in zip(ds.lat.values,ds.lon.values):
        # Convert latitude and longitude to Lambert Azimuthal Grid coordinates
        #desired_xc, desired_yc = pyproj.Transformer.from_crs(ccrs.PlateCarree(), original_projection).transform(lon, lat)
        desired_xc, desired_yc = transformer.transform(lat,lon)
        import pdb
        pdb.set_trace()
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
    infile = "/perm/nhd/data_sample/MET_Norway_snow/daily-avhrr-sce-nhl_ease-50_201505011200.nc" #sys.argv[1] #the nc file with the data
    #infile = "/ec/res4/scratch/nhd/CERISE/CRYO_NC/daily-avhrr-sce-nhl_ease-50_201503171200.nc"
    infile = "/perm/nhd/data_sample/CCI_snow/20150501-slice_matching_carra_domain.nc"
    #infile = "/perm/nhd/data_sample/CCI_snow/20150501-ESACCI-L3C_SNOW-SCFG-AVHRR_MERGED-fv2.0.nc"
    ds = xr.open_dataset(infile,engine='netcdf4')  
    var_nc = "prob_snow_b"
    all_data = get_latlon(ds, var_nc)
