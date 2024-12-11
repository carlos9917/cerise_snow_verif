"""
Project the grid from the met norway file
to a regular grid
From Lambert equidistant to regular grid
"""

import xarray as xr  
import rioxarray  
import numpy as np  
from rasterio.enums import Resampling  
import os

# Open the dataset  
data_path = "../../sample_data/Cryo_clim"
ncfile = os.path.join(data_path,"daily-avhrr-sce-nhl_ease-50_201505011200.nc")
date = ncfile.split("_")[-1].replace(".nc","")
ds = xr.open_dataset(ncfile)

# Dump only this variable
variable_name = 'prob_snow_c'
ds_single = ds[[variable_name]]  

# Remove the grid_mapping attribute if it exists  
if 'grid_mapping' in ds_single[variable_name].attrs:  
    del ds_single[variable_name].attrs['grid_mapping']  

# Add CRS information to the dataset  
ds_single.rio.write_crs(  
    "+proj=laea +ellps=WGS84 +lat_0=90 +lon_0=0",  
    inplace=True  
)  

# Set spatial dimensions  
ds_single.rio.set_spatial_dims(x_dim="xc", y_dim="yc", inplace=True)  

# Reproject to WGS84 (regular lat-lon)  
ds_reproj = ds_single.rio.reproject(  
    "EPSG:4326",  # WGS84 lat-lon  
    resolution=0.05,  # Choosing 0.05 as the resolution is 5km
    resampling=Resampling.bilinear  
)  

# Clean up any remaining grid mapping references  
if 'grid_mapping' in ds_reproj[variable_name].attrs:  
    del ds_reproj[variable_name].attrs['grid_mapping']  

# Save to new NetCDF file  
ds_reproj.to_netcdf(os.path.join(data_path,f'reg_ll_{variable_name}_date.nc'))
