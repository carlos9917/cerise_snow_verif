#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

"""
Resample data from the snow cover in the nc file from MET Norway
to  the grid in CARRA2

"""

import os, sys
import xarray as xr
import pyresample as pr
import numpy as np
from matplotlib import pyplot as plt
nc_file = sys.argv[1]
output_filename = sys.argv[2]
var_out = "scfg"

nc = xr.open_dataset(nc_file)
# Create resampling source definition (AreaDefinition) for pyresample from data on file
# Extent is outer edges (not centre) of grid cell in order (lower_left_x, lower_left_y, upper_right_x, upper_right_y

lon_grid_spacing= abs(nc.lon[2]-nc.lon[3]).item()
lat_grid_spacing= abs(nc.lat[2]-nc.lat[3]).item()


x_half = lon_grid_spacing/2
y_half = lat_grid_spacing/2
area_extent = ( nc.lon.data[0] - x_half, nc.lat.data[-1] - y_half, nc.lon.data[-1] + x_half, nc.lat.data[0] + y_half )

# Define the projection
proj_dict = {
  'proj': 'longlat',
  'datum': 'WGS84',
  'no_defs': None
}

# Create area definition
area_id = 'global_wgs84_05deg'
description = 'Global WGS84 grid at 0.05 degree resolution'
proj_id = 'WGS84'

src_def = pr.geometry.AreaDefinition(area_id, description, proj_id, proj_dict,
                              nc.lon.size, nc.lat.size, area_extent)

#src_def = pr.geometry.AreaDefinition('nh_laea-50', 'nh_laea-50', 'nh_laea-50', nc.Lambert_Azimuthal_Grid.proj4, nc.lon.size, nc.lat.size, area_extent)

# Create resampling target definition.
#file_harmonie = "../../CARRA2/snowc_2015-01-01_reg.grib2"
file_harmonie = "../../ANALYSIS_FILES/260289_20150520_analysis_reg.grib2"
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

#bin_data = np.where((~np.isnan(data_out)) & (data_out > 80.0), 1, 0)
fscov = data_out/100.0 #setting this up as fraction of snow cover

#convert to standard unix time
from time_units import seconds_to_unix_time
std_unix_time=[seconds_to_unix_time(ts) for ts in seconds_since_1978]


# Create xarray Dataset
var_out = "fscov" # to be used in the call to ds_harm below and setting the attributes down below
ds = xr.Dataset(
    {
        "fscov": (["time","lat","lon"], fscov),
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
ds["fscov"].attrs["units"] = "None"
ds["fscov"].attrs["coordinates"] = "lat lon"
ds["fscov"].attrs["grid_mapping"] = "longlat"

ds.attrs["grid_mapping"] = "latitude_longitude"
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
ds.to_netcdf(output_filename)


#open and add the projection information
from netCDF4 import Dataset

fid = Dataset(output_filename, 'a', format='NETCDF4')
proj_var = fid.createVariable('projection_regular_ll', 'i4', ())
proj_var.grid_mapping_name = "longlat"
proj_var.false_northing = 0.0
proj_var.earth_shape = "spherical"
proj_var.proj4 = "+proj=longlat +datum=WGS84"
fid.close()


