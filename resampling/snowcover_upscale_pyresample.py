#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

"""
Resample data from the snow cover in the nc file from MET Norway
to  the grid in Harmonie.

"""

import os, sys
import xarray as xr
import pyresample as pr
import numpy as np
from matplotlib import pyplot as plt
nc_file = sys.argv[1]
output_filename = sys.argv[2]
var_out = "prob_snow_c" #to be used to dump data below

#nc_file = 'daily-avhrr-sce-nhl_ease-50_201505011200.nc'
#output_filename = "daily-avhrr-sce-nhl_ease-50_201505011200_resampled.nc"
#nc_file = 'snowcover_daily_nh_laea-50_avhrr_201503151200.nc'
nc = xr.open_dataset(nc_file)

# Create resampling source definition (AreaDefinition) for pyresample from data on file
# Extent is outer edges (not centre) of grid cell in order (lower_left_x, lower_left_y, upper_right_x, upper_right_y
x_half = nc.xc.grid_spacing/2
y_half = nc.yc.grid_spacing/2
area_extent = ( nc.xc.data[0] - x_half, nc.yc.data[-1] - y_half, nc.xc.data[-1] + x_half, nc.yc.data[0] + y_half )
src_def = pr.geometry.AreaDefinition('nh_laea-50', 'nh_laea-50', 'nh_laea-50', nc.Lambert_Azimuthal_Grid.proj4, nc.xc.size, nc.yc.size, area_extent)

# Create resampling target definition.
file_harmonie = "../MODEL_DATA/260289_20150501_analysis_reg.grib2"
ds_harm = xr.open_dataset(file_harmonie)


# Assuming target is a regular 2D lat/lon grid we use GridDefinition. If resampling to e.g. a satellite swath with irregular lat/lon then a SwathDefinition would be used instead.
#lat_1d = np.arange(-90.0, 91.0)
lat_1d = ds_harm['latitude'].values
lon_1d = ds_harm["longitude"].values
#times = ds_harm["time"].values #taking them from the nc file below now

#not doing this...
#lat_1d = np.flipud(lat_1d) # Resampled data_out is flipped upside-down unless lat is [90..-90]
#lon_1d = np.arange(-180.0, 180.0)
lon, lat = np.meshgrid(lon_1d, lat_1d) # GridDefinition requires 2D lat/lon
target_def = pr.geometry.GridDefinition(lons=lon, lats=lat)

# pyresample stuff
rad = 50000 # Only search for neighbours within this radius of the target grid cell 
nbs = 8 # Use at most X nearest neighbours as basis for gaussian resampling (still required to be within radius). Not used for simple nearest neighbour resampling.
fv = np.nan # Value to set at points in target grid where no data is found within radius

# Do a simple nearest neighbour resampling of the data
data_in = nc[var_out].data #[0]
times = nc["time"].data
data_out = pr.kd_tree.resample_nearest(src_def, data_in, target_def, radius_of_influence=rad, fill_value=fv)

n_lon = ds_harm.sizes["longitude"]
n_lat = ds_harm.sizes["latitude"]
print(n_lon,n_lat)
data_out = np.reshape(data_out, (1, n_lat, n_lon))
reference_date = np.datetime64('1978-01-01T00:00:00.000000000')
times = np.atleast_1d(times)
seconds_since_1978=[]
for t in times:
    seconds_since_1978.append((t - reference_date)/np.timedelta64(1, 's'))

bin_data = np.where((~np.isnan(data_out)) & (data_out > 80.0), 1, 0)

#convert to standard unix time
from time_units import seconds_to_unix_time
std_unix_time=[seconds_to_unix_time(ts) for ts in seconds_since_1978]

# The time is on the day at 12 UTC but this is only one data point per day
# The analysis file is set at 00 UTC. Force the time to match that of the analysis
# Not a bad approximation as there is only one snow cover observation per day anyhow
#modified_ts = []
#import datetime
#for original_timestamp in std_unix_time:
#    original_datetime = datetime.datetime.utcfromtimestamp(original_timestamp)
#
#    # Subtract 12 hours (using timedelta)
#    new_datetime = original_datetime - datetime.timedelta(hours=12)
#    
#    # Convert the new datetime back to a Unix timestamp
#    new_timestamp = int(new_datetime.timestamp())
#    modified_ts.append(new_timestamp)

# Other info in the grib file
# Ni = 1475; Equiv to nx
# Nj = 302;  -> ny
# latitudeOfFirstGridPointInDegrees = 86; -> SW_lat 
# longitudeOfFirstGridPointInDegrees = 250.3; -> SW_lon
# latitudeOfLastGridPointInDegrees = 55.9; -> NE_lat
# longitudeOfLastGridPointInDegrees = 37.7; NE_lon
# iDirectionIncrementInDegrees = 0.1; dx
# jDirectionIncrementInDegrees = 0.1; dy
# gridType = regular_ll;  proj


# Create xarray Dataset
var_out = "fscov" # to be used in the call to ds_harm below and setting the attributes down below
ds = xr.Dataset(
    {
        "fscov": (["time","lat","lon"], data_out),
        "bin_snow": (["time","lat","lon"], bin_data),
    },
    coords={
        "time": std_unix_time, #seconds_since_1978,
        "lat": ds_harm["latitude"].values,
        "lon": ds_harm['longitude'].values,
    },
)



#ds.time.attrs["units"] = "seconds since 1978-01-01 00:00:00"
ds.time.attrs["units"] = "seconds since 1970-01-01 00:00:00"
ds.time.attrs["long_name"] = "reference time of product" 
ds.lon.attrs["units"] = "degrees_east"
ds.lat.attrs["units"] = "degrees_north"
ds[var_out].attrs["units"] = "None"
ds["bin_snow"].attrs["units"] = "None"
ds["bin_snow"].attrs["coordinates"] = "lat lon"
ds["bin_snow"].attrs["grid_mapping"] = "longlat"

#write the information about the grid
# Create the Lambert Azimuthal grid projection variable
#ds["projection_regular_ll"] = np.nan

dummy_array = xr.DataArray(np.array(0, dtype=np.int32))

#ds['Lambert_Azimuthal_Grid'] = xr.Variable('Lambert_Azimuthal_Grid', np.zeros_like(data, dtype=np.int32))

#Last Attempt to write the projection info
#ds['projection_regular_ll'] = xr.Variable('projection_regular_ll', "i4") #dummy_array)
#ds["projection_regular_ll"].attrs["grid_mapping_name"] = "latitude_longitude"
#ds["projection_regular_ll"].attrs["earth_radius"] = 6367470.


#regular_grid = nc_file.createVariable('projection_regular_ll', 'i4')
#regular_grid.grid_mapping_name = "latitude_longitude"
#lambert_azimuthal_grid.false_northing = 0.0
#lambert_azimuthal_grid.earth_shape = "spherical"
#lambert_azimuthal_grid.proj4 = "+proj=laea +ellps=WGS84 +lat_0=90 +lon_0=0"

#ds["bin_snow"].attrs["grid_mapping"] = "projection_regular_ll"
ds.attrs["grid_mapping"] = "latitude_longitude"
#ds.attrs["proj4"] = "+proj=laea +ellps=WGS84 +lat_0=90 +lon_0=0"
ds.attrs["proj4"] = "+proj=longlat +datum=WGS84"
ds.attrs["proj"] = ds_harm[var_out].attrs["GRIB_gridType"]
ds.attrs["nx"] = ds_harm[var_out].attrs["GRIB_Nx"]
ds.attrs["ny"] = ds_harm[var_out].attrs["GRIB_Ny"]
ds.attrs["dx"] = ds_harm[var_out].attrs["GRIB_iDirectionIncrementInDegrees"]
ds.attrs["dy"] = ds_harm[var_out].attrs["GRIB_jDirectionIncrementInDegrees"]
ds.attrs["SW_lat"] = ds_harm[var_out].attrs["GRIB_latitudeOfFirstGridPointInDegrees"]
ds.attrs["NE_lat"] = ds_harm[var_out].attrs["GRIB_latitudeOfLastGridPointInDegrees"]
ds.attrs["SW_lon"] = ds_harm[var_out].attrs["GRIB_longitudeOfFirstGridPointInDegrees"]
ds.attrs["NE_lon"] = ds_harm[var_out].attrs["GRIB_longitudeOfLastGridPointInDegrees"]
# Ni = 1475; Equiv to nx
# Nj = 302;  -> ny
# latitudeOfFirstGridPointInDegrees = 86; -> SW_lat 
# longitudeOfFirstGridPointInDegrees = 250.3; -> SW_lon
# latitudeOfLastGridPointInDegrees = 55.9; -> NE_lat
# longitudeOfLastGridPointInDegrees = 37.7; NE_lon

ds.to_netcdf(output_filename)
#open and add the projection information
from netCDF4 import Dataset

fid = Dataset(output_filename, 'a', format='NETCDF4')
#proj_var = fid.createVariable('projection_regular_ll', 'S1', ())
proj_var = fid.createVariable('projection_regular_ll', 'i4', ())
proj_var.grid_mapping_name = "longlat"
proj_var.false_northing = 0.0
proj_var.earth_shape = "spherical"
#proj_var.proj4 = "+proj=laea +ellps=WGS84 +lat_0=90 +lon_0=0"
proj_var.proj4 = "+proj=longlat +datum=WGS84"
fid.close()

#plt.imshow(data_in)
#plt.show()

#plt.imshow(data_out)
#plt.show()

