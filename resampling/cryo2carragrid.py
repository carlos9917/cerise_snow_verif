#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

"""
Resample snow cover data from MET Norway nc file to CARRA2 grid.
"""

import os
import sys
import argparse
import datetime
import xarray as xr
import pyresample as pr
import numpy as np
from netCDF4 import Dataset


def seconds_to_unix_time(seconds_since_1978):
    """Convert seconds since 1978-01-01 to Unix timestamp."""
    base_datetime = datetime.datetime(1978, 1, 1, 0, 0, 0)
    target_datetime = base_datetime + datetime.timedelta(seconds=seconds_since_1978)
    return target_datetime.timestamp()


def resample_snowcover(
    input_file, output_file, harmonie_file, var_in="prob_snow_c", var_out="prob_snow_c",prob_snow_thr=80.0
):
    """
    Resample snow cover data from input grid to CARRA2 grid.

    Parameters:
    -----------
    input_file : str
        Path to input NetCDF file
    output_file : str
        Path for output NetCDF file
    harmonie_file : str
        Path to HARMONIE reference file
    var_in : str
        Input variable name
    var_out : str
        Output variable name
    pron_snow_thr : double
        probability threshold to define the binary snow variable
    """
    # Open input datasets
    nc = xr.open_dataset(input_file)
    ds_harm = xr.open_dataset(harmonie_file)

    # Create source definition
    x_half = nc.xc.grid_spacing / 2
    y_half = nc.yc.grid_spacing / 2
    area_extent = (
        nc.xc.data[0] - x_half,
        nc.yc.data[-1] - y_half,
        nc.xc.data[-1] + x_half,
        nc.yc.data[0] + y_half,
    )
    src_def = pr.geometry.AreaDefinition(
        "nh_laea-50",
        "nh_laea-50",
        "nh_laea-50",
        nc.Lambert_Azimuthal_Grid.proj4,
        nc.xc.size,
        nc.yc.size,
        area_extent,
    )

    # Create target definition
    lat_1d = ds_harm["latitude"].values
    lon_1d = ds_harm["longitude"].values
    lon, lat = np.meshgrid(lon_1d, lat_1d)
    target_def = pr.geometry.GridDefinition(lons=lon, lats=lat)

    # Resample data
    data_in = nc[var_in].data
    times = nc["time"].data
    rad = 50000  # Search radius
    fv = np.nan  # Fill value
    data_out = pr.kd_tree.resample_nearest(
        src_def, data_in, target_def, radius_of_influence=rad, fill_value=fv
    )

    # Reshape data
    n_lon = ds_harm.sizes["longitude"]
    n_lat = ds_harm.sizes["latitude"]
    data_out = np.reshape(data_out, (1, n_lat, n_lon))

    # Process time values
    reference_date = np.datetime64("1978-01-01T00:00:00.0000")
    times = np.atleast_1d(times)
    seconds_since_1978 = [(t - reference_date) / np.timedelta64(1, "s") for t in times]
    std_unix_time = [seconds_to_unix_time(ts) for ts in seconds_since_1978]

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
            "lat": ds_harm["latitude"].values,
            "lon": ds_harm["longitude"].values,
        },
    )

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
    ds.attrs.update(
        {
            "grid_mapping": "latitude_longitude",
            "proj4": "+proj=longlat +datum=WGS84",
            "proj": ds_harm[var_out].attrs["GRIB_gridType"],
            "nx": ds_harm[var_out].attrs["GRIB_Nx"],
            "ny": ds_harm[var_out].attrs["GRIB_Ny"],
            "dx": ds_harm[var_out].attrs["GRIB_iDirectionIncrementInDegrees"],
            "dy": ds_harm[var_out].attrs["GRIB_jDirectionIncrementInDegrees"],
            "SW_lat": ds_harm[var_out].attrs["GRIB_latitudeOfFirstGridPointInDegrees"],
            "NE_lat": ds_harm[var_out].attrs["GRIB_latitudeOfLastGridPointInDegrees"],
            "SW_lon": ds_harm[var_out].attrs["GRIB_longitudeOfFirstGridPointInDegrees"],
            "NE_lon": ds_harm[var_out].attrs["GRIB_longitudeOfLastGridPointInDegrees"],
        }
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


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Resample snow cover data from MET Norway nc file to CARRA2 grid."
    )
    parser.add_argument("input_file", help="Input NetCDF file")
    parser.add_argument("output_file", help="Output NetCDF file")
    parser.add_argument(
        "--harmonie_file",
        default="../../CARRA2/snowc_2015-01-01_reg.grib2",
        help="HARMONIE reference file",
    )
    parser.add_argument("--var_in", default="prob_snow_c", help="Input variable name")
    parser.add_argument("--var_out", default="prob_snow_c", help="Output variable name")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_arguments()
    resample_snowcover(
        args.input_file, args.output_file, args.harmonie_file, args.var_in, args.var_out
    )
