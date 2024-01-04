"""
Reads the model (CARRA) grib file in regular lat lon format
Extracts all data for a particular time 
In this case the time is set to 600, since
this is the time when the snow data is available

Once the values of snow cover are read, the data is written
as snow/no snow when the snow cover is over a threshold
Using 80 % as threshold below
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
    print("Please provide the hour, input grib file and the output file name")
    sys.exit(1)
else:
    hour = sys.argv[1]
    infile = sys.argv[2]
    outfile = sys.argv[3]
#setting this one above now
#fname = os.path.split(infile)[-1].replace(".grib2","")
#outfile = os.path.join(DATA,"MODEL_DATA",fname+"_600.grib2")
hour_select = str(hour).zfill(2)+"00"
hour_select = int(hour_select)

print(f"Extracting hour {hour_select} from {infile} to {outfile}")
#hour_select=600 #in integer format
ikey="param"

if os.stat(infile).st_size==0:
    print(f"{infile} is empty!")
    sys.exit(1)

nhours=8
year=2022
month=10
ndays=calendar.monthrange(year, month)[1]


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


#it will save all values here:
# I will only take values on hour 6, which is when the snow data is available
values_read = np.zeros([ndays,latdim*londim], dtype=np.float32) #I will be saving all days
i=0
found_var=False
gfile = open(infile)
while True:
    msg = ecc.codes_grib_new_from_file(gfile)
    if msg is None:
        break
    key = ecc.codes_get_long(msg, ikey)
    date = ecc.codes_get_long(msg, "date")
    hour = ecc.codes_get_long(msg, "time")

    if (key == param_code) and (hour == hour_select):
        print(f"Found key and input for {date} and time {hour}" )
        values_read[i,:] = ecc.codes_get_values(msg)
        i+=1
        found_var=True
gfile.close()
if not found_var:
    print(f"{param_code} not found in {infile}!")


gfile = open(infile)
collect_msg = []
nmsg=0
while True:
    msg_clone = ecc.codes_grib_new_from_file(gfile)
    if msg_clone is None: break
    key = ecc.codes_get_long(msg_clone, ikey)
    hour = ecc.codes_get_long(msg_clone, "time")
    if (key == param_code) and (hour == hour_select):
        print(f"Found key for cloning the output of {key} on hour {hour}" )
        msg2 = ecc.codes_clone(msg_clone)
        collect_msg.append(msg2)
        nmsg+=1
gfile.close()

# Now setting the snow_no_snow variable here

set_values = np.zeros([ndays,latdim*londim], dtype=np.float32) #I will be saving all days
for i in range(ndays):
    set_values[i,:] = np.where((values_read[i,:] >= snow_cover_thr) & (values_read[i,:] != 9999.0), 1.0, 0.0)

#write the output
with open(outfile,'wb') as f:
    for i in range(ndays):
        #ecc.codes_set_values(collect_msg[i], values_read[i,:])
        ecc.codes_set_values(collect_msg[i], set_values[i,:])
        ecc.codes_write(collect_msg[i], f)
