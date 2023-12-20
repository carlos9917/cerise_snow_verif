"""
Read the carra netcdf file in regular lat lon format
copy the contents.
1. Set all values to np.nan
2. Read the snow data. Replace where there is data to snow observations.
Save

This version uses the netcdf file, because eccodes python lib 
sucks sometimes. Getting memory issues and no fucking idea
where they come from.

"""

import os
import sys
import re
import xarray as xr
import numpy as np
import calendar
from pathlib import Path
import pandas as pd
from collections import OrderedDict

if __name__=="__main__":
    param_code = 260289 #snow cover
    DATA="/ec/res4/scratch/nhd/CERISE/"
    DATA="/media/cap/7fed51bd-a88e-4971-9656-d617655b6312/data/CERISE"
    infile=os.path.join(DATA,"MODEL_DATA","snow_cover_202210_ll_grid.nc")
    origin="no-ar-cw"

    if os.stat(infile).st_size==0:
        print(f"{infile} is empty!")
        sys.exit(1)
 
    ds = xr.open_dataset(infile,engine="netcdf4")
    nhours=8
    import pdb
    pdb.set_trace()
    #gfile = open(infile)
    #while 1:
    #    gid = ecc.codes_grib_new_from_file(gfile)
    #    if gid is None:
    #        break
    #    Nx = ecc.codes_get(gid, "Nx")
    #    Ny = ecc.codes_get(gid, "Ny")
    #
    #gfile.close()
    #print(f"Grid size Nx: {Nx}")
    #print(f"Grid size Ny: {Ny}")
    #
    #values={}
    #latdim=Ny
    #londim=Nx
    #print(f"lat and lon dimensions {latdim}, {londim}")

