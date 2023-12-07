"""
Read the numpy files with the indices.
Read the dummy file with values set to -999 and at specific time (ie, template_obs_202210_600.grib2)
Reads the modified csv files  with the indices and the values of the observations
Modify the contents at the selected indices
Dumps the new obs file

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
DATA="/ec/res4/scratch/nhd/CERISE/"
year=2022
month=10
yyyymm=str(year)+str(month).zfill(2)
ndays=calendar.monthrange(year, month)[1]
infile=os.path.join(DATA,"MODEL_DATA", "template_obs_202210_600.grib2") #"snow_cover_202210_600.grib2")
outfile = os.path.join(DATA,"CRYO_SW","obs_202210_600.grib2")
origin="no-ar-cw"
obs_fpre="snow_cryo_" #2906_ix.npz"
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
# Read the data from snow
def get_data_fromtxt(txtFile):
    """
    20221030  6  71.11412  -75.79826  100.00  1
    """
    date = []
    lat     = []
    lon     = []
    snowFrac = []
    f = open(txtFile, 'r')

    for line in f:
        line    = line.strip()
        columns = line.split()
        hour = str(columns[1]).zfill(2)
        date.append(str(columns[0])+hour) #   [str(i)+str(j).zfill(2) for i,j in zip(columns[0],columns[1])]
        lat.append(float(columns[2]))
        lon.append(float(columns[3]))
        snowFrac.append(float(columns[4]))

    f.close()

    return snowFrac


# packing all values here
values_read = np.zeros([ndays,latdim*londim], dtype=np.float32) #I will be saving all days

ikey="param"
i=0
found_var=False
gfile = open(infile)
while True:
    msg = ecc.codes_grib_new_from_file(gfile)
    if msg is None:
        break
    #print(msg['param'])
    key = ecc.codes_get_long(msg, ikey)
    date = ecc.codes_get_long(msg, "date")
    hour = ecc.codes_get_long(msg, "time")
    if (key == param_code) and (hour == 600): #altready in 600 but check nevertheless
        found_var=True
        print(f"Found key and input for {date} and time {hour}" )
        values_read[i,:] = ecc.codes_get_values(msg)
        date_str = str(date)
        obs_file = os.path.join(DATA,"CRYO_SW",obs_fpre+date_str+"06_idx_obs.csv") #snow_cryo_2022100106_idx_obs.csv
        df_obs = pd.read_csv(obs_file,sep=" ",header=None)
        df_obs.columns=["idx","obs"]
        df_obs["idx"] = df_obs["idx"].astype(int)
        for _,r in df_obs.iterrows():
            snow_obs = r.obs
            snow_idx = int(r.idx)
            values_read[i,snow_idx] = snow_obs
        i+=1
gfile.close()
if not found_var:
    print(f"{param_code} not found in {infile}!")


# 2. clone the file and write new file with the snow values
#for file_path in sorted(Path(OBS_DATA).glob(fpre+yyyymm+'*.npz')):
gfile = open(infile)
collect_msg = []
nmsg=0
while True:
    msg_clone = ecc.codes_grib_new_from_file(gfile)
    if msg_clone is None: break
    key = ecc.codes_get_long(msg_clone, ikey)
    hour = ecc.codes_get_long(msg_clone, "time")
    if (key == param_code) and (hour == 600):
        print(f"Found key for cloning the output of {key} on hour {hour}" )
        msg2 = ecc.codes_clone(msg_clone)
        collect_msg.append(msg2)
        nmsg+=1

gfile.close()
#write the output
nf = ndays*nhours-1
with open(outfile,'wb') as f:
    for i in range(ndays):
        ecc.codes_set_values(collect_msg[i], values_read[i,:])
        ecc.codes_write(collect_msg[i], f)

