#!/usr/bin/env python
"""
Upsample the CARRA data to the Met Norway grid.
The MET Norway grid covers the whole and it is projected
first to a regular lat lon grid before being used in this script.

The domain selected from CARRA is not  precisely the same as
the original. Cutting the grid based on the lon min and max values
always resulted in a smaller than expected domain (due to issues with
the range of lat crossing the 0 longitude line).
Hence only the limits of latitude where used to setup
a mask in the harmonie grid. Since the purpose
of this script is to generate a file that has the same
resolution as the original netcdf file, the exact
domain extent is unimportant as long as the resolution is upscaled
to the correct size.
In the verification step only the matching domains
will be used. Additionally, the 
"""

import os
import sys
import argparse
import datetime
import xarray as xr
import pyresample as pr
import numpy as np
from netCDF4 import Dataset

from pyproj import Transformer
from warnings import filterwarnings
filterwarnings('ignore')


def seconds_to_unix_time(seconds_since_1978):
    """Convert seconds since 1978-01-01 to Unix timestamp."""
    base_datetime = datetime.datetime(1978, 1, 1, 0, 0, 0)
    target_datetime = base_datetime + datetime.timedelta(seconds=seconds_since_1978)
    return target_datetime.timestamp()

def get_geom_def(
    input_file, harmonie_file, obs_var="prob_snow_c", var_out="prob_snow_c", model_var="fscov", prob_snow_thr=80.0
):
    """
    This function dumps the domain
    """
    # Open input datasets
    nc = xr.open_dataset(input_file)

    # Attempt to normalize the longitude values to -180 to 180 range
    # Did not help in this part.
    #nc = nc.assign_coords(lon=((nc.lon + 360) % 360))
    #nc = nc.assign_coords(x=((nc.x + 360) % 360))
    #nc = nc.sortby('x')

    ds_harm = xr.open_dataset(harmonie_file)
    #ds_harm.assign_coords(longitude=((ds_harm.longitude + 360) % 360))
    #ds_harm = ds_harm.sortby('longitude')

    # Create source definition (HARMONIE grid)
    harm_lat = ds_harm["latitude"].values
    harm_lon = ds_harm["longitude"].values
    
    harm_lon, harm_lat = np.meshgrid(harm_lon, harm_lat)
    src_def = pr.geometry.SwathDefinition(lons=harm_lon, lats=harm_lat)

    # Get the domain bounds from HARMONIE
    lat_min = harm_lat.min()
    lat_max = harm_lat.max()
    lon_min = harm_lon.min()
    lon_max = harm_lon.max()
    
    print("Borders of the harmonie grid")
    print(lat_min,lat_max)
    print(lon_min,lon_max)

    # before using the lon min and max, convert to 0 to 360
    #lon_min, lon_max = (lon_min + 360) % 360, lon_max
    #print("New lon min and max")
    #print(lon_min,lon_max)

    
    # Create target definition (subset of NetCDF grid)
    # Get the 2D lat/lon arrays from the NetCDF file
    nc_lat = nc.lat.values  # This is already 2D
    nc_lon = nc.lon.values  # This is already 2D

    nc_lat_filt = nc.lat.where((nc.lat >= 0) & (nc.lat <= 90))
    nc_lon_filt = nc.lon.where((nc.lon >= -180) & (nc.lon <= 180))

    #nc_lon = corrected_lons
    orig_def = pr.geometry.GridDefinition(lons = nc_lon, lats = nc_lat)
    

    # Create mask for points within HARMONIE domain
    #domain_mask = (nc_lat >= lat_min) & (nc_lat <= lat_max) & \
    #              (nc_lon >= lon_min) & (nc_lon <= lon_max)

    #this one considers only the lat min and max to avoid issues with
    # the lon min and max
    domain_mask = (nc_lat >= lat_min) & (nc_lat <= lat_max) 
    
    # Get the corresponding x and y indices where the mask is True
    y_indices, x_indices = np.where(domain_mask)

    # Get the unique x and y coordinates that fall within our domain
    unique_x = np.unique(nc.x.values[x_indices])
    unique_y = np.unique(nc.y.values[y_indices])

    # Create the target grid definition using the masked coordinates
    x_grid, y_grid = np.meshgrid(unique_x, unique_y)

    # Get corresponding lat/lon for these points
    target_lat = nc_lat[np.ix_(range(len(unique_y)), range(len(unique_x)))]
    target_lon = nc_lon[np.ix_(range(len(unique_y)), range(len(unique_x)))]
   
    # Create target definition
    target_def = pr.geometry.GridDefinition(lons=target_lon, lats=target_lat)
    #target_def = pr.geometry.GridDefinition(lons=x_grid, lats=y_grid)
    # Get the arrays
    print("Borders of the resulting mesh")
    print(unique_y.min(),unique_y.max())
    print(unique_x.min(),unique_x.max())
    flip_y = np.flip(unique_y) #for some reason this is inverted!!
    return src_def, target_def, orig_def, flip_y, unique_x




def upsample_snowcover_carra_to_metgrid(
    input_file, harmonie_file, obs_var="prob_snow_c", var_out="prob_snow_c", model_var="fscov", prob_snow_thr=80.0
):
    # Open input datasets
    nc = xr.open_dataset(input_file)
    ds_harm = xr.open_dataset(harmonie_file)

    
    src_def,target_def, orig_def, target_lat, target_lon = get_geom_def(input_file, harmonie_file, obs_var, var_out, model_var, prob_snow_thr)

    # Resample data
    data_in = ds_harm[model_var].values
    bin_data_in = np.where((~np.isnan(data_in)) & (data_in > prob_snow_thr), 1, 0)
    times = ds_harm["time"].values
    # Using average resampling for downscaling
    data_out = pr.kd_tree.resample_nearest(
        src_def,
        #bin_data_in, #usig this I get a NaN error
        data_in,
        target_def,
        radius_of_influence=50000, #this is the default value!
        #sigmas=25000,
        fill_value=np.nan
    )
    # Process time values
    reference_date = np.datetime64("1978-01-01T00:00:00.0000")
    times = np.atleast_1d(times)
    seconds_since_1978 = [(t - reference_date) / np.timedelta64(1, "s") for t in times]
    std_unix_time = [seconds_to_unix_time(ts) for ts in seconds_since_1978]

    # Reshape data for output
    n_time = len(times)
    if len(data_out.shape) == 2:
        data_out = data_out.reshape(1, *data_out.shape)

    # Create binary snow cover data
    bin_data = np.where((~np.isnan(data_out)) & (data_out > prob_snow_thr), 1, 0)
        # Create output dataset
    ds = xr.Dataset(
        {
            var_out: (["time", "lat", "lon"], data_out),
            "bin_snow": (["time", "lat", "lon"], bin_data),
        },
        coords={
            "time": std_unix_time,
            "lat": target_lat,
            "lon": target_lon,
            #"lat": ds_harm["latitude"].values,
            #"lon": ds_harm["longitude"].values,
        },
    )


    return data_out, ds


#src_def,target_def, orig_def, target_lat, target_lon = get_geom_def(
#        input_file, harmonie_file, obs_var, var_out, model_var,prob_snow_thr
#    )




def dump_to_nc(ds,output_file):
    
    # Set attributes
    ds.time.attrs.update(
        {
            "units": "seconds since 1970-01-01 00:00:00",
            "long_name": "reference time of product",
        }
    )
    ds.lon.attrs["units"] = "degrees_east"
    ds.lat.attrs["units"] = "degrees_north"
    ds[var_out].attrs["units"] = "None"
    ds["bin_snow"].attrs.update(
        {"units": "None", "coordinates": "lat lon", "grid_mapping": "longlat"}
    )

    # Set grid mapping attributes
    # Set attributes
    ds.time.attrs.update(
        {
            "units": "seconds since 1970-01-01 00:00:00",
            "long_name": "reference time of product",
        }
    )
    ds.lon.attrs["units"] = "degrees_east"
    ds.lat.attrs["units"] = "degrees_north"
    ds[var_out].attrs["units"] = "None"
    ds["bin_snow"].attrs.update(
        {"units": "None", "coordinates": "lat lon", "grid_mapping": "longlat",
         "proj4": "+proj=longlat +datum=WGS84"}
    )
    # Save to NetCDF
    ds.to_netcdf(output_file)

    # Add projection information
    with Dataset(output_file, "a", format="NETCDF4") as fid:
        proj_var = fid.createVariable("projection_regular_ll", "i4", ())
        proj_var.grid_mapping_name = "longlat"
        proj_var.false_northing = 0.0
        proj_var.earth_shape = "spherical"
        proj_var.proj4 = "+proj=longlat +datum=WGS84"

    # Set grid mapping attributes


input_file = "../../sample_data/Cryo_clim/reg_ll_prob_snow_c_date.nc"
nc = xr.open_dataset(input_file)

harmonie_file = "../../sample_data/CARRA1/260289_20150501_analysis_NO-AR-CE_reg.grib2"

obs_var = "prob_snow_c"
var_out = "fscov"
model_var = "fscov"
prob_snow_thr = 0.8
data_out,ds = upsample_snowcover_carra_to_metgrid(
       input_file, harmonie_file, obs_var, var_out, model_var,prob_snow_thr
    )

ds_harm = xr.open_dataset(harmonie_file)
lon_min = ds_harm.longitude.min()
lon_max = ds_harm.longitude.max()


if lon_min < lon_max:
    # Simple case: lon_min to lon_max is continuous
    subset = ds.sel(lon=slice(lon_min, lon_max))
else:
    # Case where the range crosses the 0° longitude line
    subset = xr.concat(
        [ds.sel(lon=slice(lon_min, 360)), ds.sel(lon=slice(0, lon_max))],
        dim="lon"
    )
#dump_to_nc(ds,"snow_cover_from_carra_upsampled_to_met_grid.nc")
subset.to_netcdf("snow_cover_from_carra2.nc")




