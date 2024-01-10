"""
Reads the model (CARRA) grib file 
and extracts all lat lon values, and their corresponding
indices
"""
snow_cover_thr = 0.8

import os
import sys
import re
import eccodes as ecc
import numpy as np
import calendar
from pathlib import Path
import pandas as pd
from collections import OrderedDict


param_code = 260289 #snow cover
DATA="/ec/res4/scratch/nhd/CERISE/"


#infile=os.path.join(DATA,"MODEL_DATA","snow_cover_202210_ll_grid.grib2")
if len(sys.argv) == 1:
    print("Please provide the yearmonth, input grib file and the output file name")
    sys.exit(1)
else:
    yyyymm = sys.argv[1]
    infile = sys.argv[2]
    outfile = sys.argv[3]

gfile = open(infile)
while 1:
    gid = ecc.codes_grib_new_from_file(gfile)
    if gid is None:
        break
    Nx = ecc.codes_get(gid, "Nx")
    Ny = ecc.codes_get(gid, "Ny")

gfile.close()
latdim=Ny
londim=Nx
print(f"lat and lon dimensions {latdim}, {londim}")

nhours=8
year=int(yyyymm[0:4])
month=int(yyyymm[4:6])
ndays=calendar.monthrange(year, month)[1]


# I only want to save the lat lon values once
#values_read = np.zeros([ndays,latdim*londim], dtype=np.float32) #I will be saving all days
found_var=False
gfile = open(infile)
i=0
while True:
    msg = ecc.codes_grib_new_from_file(gfile)
    if msg is None:
        break
    key = ecc.codes_get_long(msg, "param")
    date = ecc.codes_get_long(msg, "date")
    hour = ecc.codes_get_long(msg, "time")

    if (key == param_code):
        print(f"Found key and input for {date} and time {hour}" )
        #values_read[i,:] = ecc.codes_get_values(msg)
        lat_values = ecc.codes_get_array(msg, 'latitudes')
        lon_values = ecc.codes_get_array(msg, 'longitudes')
        break
        #Test: when I tried this on all the pairs I got
        # them ordered in the same way as they are output.
        # Assuming they are output in the same way
        #for lat,lon in zip(lat_values,lon_values):
        #    latlonidx = ecc.codes_grib_find_nearest(msg,lat,lon)
        #    get_index = latlonidx[0]["index"]
        #    import pdb
        #    pdb.set_trace()
# convert from 0 - 360 to -180 - 180
lon_180 = (lon_values + 180) % 360 - 180
gfile.close()
df=pd.DataFrame({"lat":lat_values,"lon":lon_180})
df.to_csv(outfile,index=False)
