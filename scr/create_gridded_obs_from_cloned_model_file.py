"""
Read the gribfile from the model and use it as template
to create the obs output based on the list
of coordinates generated by get_values_from_nc_file.py
The script will loop through the ascii files named

obs_file = "ll_snow_"+date_str+".csv"
for a whole month

The values in the cloned file will be replaced by
that of the lat lon pairs in the csv file

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

MISSING = 9999 #1.0e36  # A value out of range
param_code = 260289 #snow cover in the grib file
DATA="/ec/res4/scratch/nhd/CERISE/"
CSV_DATA="/ec/res4/scratch/nhd/CERISE/cerise_snow_verif/scr/csv_files_lambert_grid"
hour_select = 0
if len(sys.argv) == 1:
    print("Please provide the model file to clone, and the output file name")
    sys.exit(1)
else:
    grib_file = sys.argv[1]
    outfile = sys.argv[2]

snow_variable_obs = "prob_snow_o" #"snow_no_snow"
snow_thr = 80 #snow threshold in prob_snow_o to set it to 1 (snow) or 0 (no snow)
nhours=8
gfile = open(grib_file)
while 1:
    gid = ecc.codes_grib_new_from_file(gfile)
    if gid is None:
        break
    Nx = ecc.codes_get(gid, "Nx")
    Ny = ecc.codes_get(gid, "Ny")
    date = ecc.codes_get_long(gid, "date")
    hour = ecc.codes_get_long(gid, "time")
    break #only gotta do this once

gfile.close()
print(f"Grid size Nx: {Nx}")
print(f"Grid size Ny: {Ny}")
latdim = Ny
londim = Nx

year = int(str(date)[0:4])
month = int(str(date)[6:8])
ndays=calendar.monthrange(year, month)[1]

#test_date = 20150501 #for testing readin only one
#ndays = 1 # for testing only
values_read = np.zeros([ndays,latdim*londim], dtype=np.float32) #I will be saving all days

i=0
found_var=False
gfile = open(grib_file)

#this loop will run over all the dates in the grib file, containing a month of data
while True:
    msg = ecc.codes_grib_new_from_file(gfile)
    if msg is None:
        break
    #print(msg['param'])
    key = ecc.codes_get_long(msg, "param")
    date = ecc.codes_get_long(msg, "date")
    hour = ecc.codes_get_long(msg, "time")
    if (key == param_code) and (hour == hour_select): 
    #just for testing only one
    #if (key == param_code) and (hour == hour_select) and (date == test_date): 
        found_var=True
        print(f"Found key and input for {date} and time {hour}" )
        values_read[i,:] = ecc.codes_get_values(msg)
        date_str = str(date)
        #obs_file = "all_lat_lons_snow_ordered_"+date_str+".csv"
        obs_file = os.path.join(CSV_DATA,"ll_snow_"+date_str+".csv")
        print(f"Reading file {obs_file}")
        if not os.path.isfile(obs_file):
            print(f"{obs_file} does not exist!")
            sys.exit(1)
        df_obs = pd.read_csv(obs_file,sep=",")
        if 'Unnamed: 0' in df_obs.columns:
            df_obs.drop(columns='Unnamed: 0',inplace=True)
        # saving the values here. 
        #Testing: using a threshold to convert this to a binary variable
        for _,r in df_obs.iterrows():
            snow_obs = r[snow_variable_obs] #.snow_no_snow
            if snow_obs != 9999.0:
                if snow_obs >= snow_thr:
                    values_read[i,_] = 1.0 #snow_obs/100
                else:
                    values_read[i,_] = 0.0 #snow_obs/100
            else:
                values_read[i,_] = MISSING
        i+=1
gfile.close()
if not found_var:
    print(f"{param_code} not found in {grib_file}!")
    sys.exit(1)

# 2. clone the file and write new file with the snow values
#for file_path in sorted(Path(OBS_DATA).glob(fpre+yyyymm+'*.npz')):
gfile = open(grib_file)
collect_msg = []
nmsg=0
while True:
    msg_clone = ecc.codes_grib_new_from_file(gfile)
    if msg_clone is None: break
    key = ecc.codes_get_long(msg_clone, "param")
    hour = ecc.codes_get_long(msg_clone, "time")
    if (key == param_code) and (hour == hour_select):
        print(f"Found key for cloning the output of {key} on hour {hour}" )
        msg2 = ecc.codes_clone(msg_clone)
        collect_msg.append(msg2)
        nmsg+=1

gfile.close()
#write the output
nf = ndays*nhours-1
with open(outfile,'wb') as f:
    #this for the 1 day test
    #ecc.codes_set_values(collect_msg[0], values_read[0,:])
    #ecc.codes_write(collect_msg[0], f)
    for i in range(ndays):
        ecc.codes_set(collect_msg[i], 'missingValue', MISSING)
        ecc.codes_set_values(collect_msg[i], values_read[i,:])
        ecc.codes_write(collect_msg[i], f)

