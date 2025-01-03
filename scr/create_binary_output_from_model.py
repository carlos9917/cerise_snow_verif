"""
Reads the analysis (CARRA) and clones the contents,
then writes them to a file where
all fscov is set to 0 if below a given
threshold, 1 otherwise

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
param_code = 260289 #snow cover
origin="no-ar-cw"
bin_thr = 0.8 #if values under this, set to zero

if len(sys.argv) == 1:
    print("Please provide input and output file")
    sys.exit(1)
else:
    infile = sys.argv[1]
    outfile = sys.argv[2]
    year=int(sys.argv[3])
    month=int(sys.argv[4])


if os.stat(infile).st_size==0:
    print(f"{infile} is empty!")
    sys.exit(1)

nhours=8
gfile = open(infile)
while 1:
    gid = ecc.codes_grib_new_from_file(gfile)
    if gid is None:
        break
    Nx = ecc.codes_get(gid, "Nx")
    Ny = ecc.codes_get(gid, "Ny")

gfile.close()
print(f"Grid size Nx: {Nx}")
print(f"Grid size Ny: {Ny}")

values={}
latdim=Ny
londim=Nx
print(f"lat and lon dimensions {latdim}, {londim}")

# packing all values here

#year=2022
#month=10
ndays=calendar.monthrange(year, month)[1]
# Doing it for one day for the moment
ndays=1

#it will save all values here:
# I will only take values on hour 6, which is when the snow data is available
values_modify = np.zeros([ndays,latdim*londim], dtype=np.float32) #I will be saving all days
#values_leave=np.zeros([ndays*nhours-1,latdim*londim], dtype=np.float32)
ikey="param"
count_others=0
i=0
found_var=False
gfile = open(infile)
MISSING = 9999 #1.0e36  # A value out of range

while True:
    msg = ecc.codes_grib_new_from_file(gfile)
    if msg is None:
        break
    ecc.codes_set(msg, 'missingValue', MISSING)
    #print(msg['param'])
    key = ecc.codes_get_long(msg, ikey)
    date = ecc.codes_get_long(msg, "date")
    hour = ecc.codes_get_long(msg, "time")

    if (key == param_code):# and (hour == 600):
        print(f"Found key and input for {date}")
        values_modify[i,:] = ecc.codes_get_values(msg)
        # Find indices where values are not equal to 'MISSING'
        indices_one = (values_modify[i, :] != MISSING) & (values_modify[i, :] >= bin_thr)
        indices_zero = (values_modify[i, :] != MISSING) & (values_modify[i, :] < bin_thr)
        values_modify[i, indices_one] = 1.0
        values_modify[i, indices_zero] = 0.0
        # Set values to 0.0 where they are less than bin_thr
        #values_modify[i, valid_indices] = (values_modify[i, valid_indices] >= bin_thr).astype(float)
        #values_modify[i, valid_indices] = (values_modify[i, valid_indices] >= bin_thr).astype(float)
        #values_modify[i, ~valid_indices] = 0.0

        #for k in values_modify[i,:].shape[1]:
        #    if values_modify[i,k] != MISSING:
        #        if values_modify[i,k] < bin_thr:
        #            values_modify[i,k] = 0.0
        #        else:
        #            values_modify[i,k] = 1.0
        i+=1
        found_var=True
    #else:
    #    values_leave[count_others,:] = ecc.codes_get_values(msg)
    #    count_others+=1
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
    if (key == param_code): # and (hour == 600):
        print(f"Found key for cloning the output of {key} on hour {hour}" )
        msg2 = ecc.codes_clone(msg_clone)
        collect_msg.append(msg2)
        nmsg+=1
    #else:
    #    get_msg = ecc.codes_clone(msg_clone)
    #    other_msg.append(get_msg)
    #    i+=1

gfile.close()
#write the output
nf = ndays*nhours-1
with open(outfile,'wb') as f:
    for i in range(ndays):
        ecc.codes_set_values(collect_msg[i], values_modify[i,:])
        ecc.codes_write(collect_msg[i], f)
    #for i in range(count_others):
    #    ecc.codes_set_values(other_msg[i],values_leave[i,:])
    #    ecc.codes_write(other_msg[i], f)


