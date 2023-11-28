"""
Read the carra grib file in regular lat lon format
clone the contents.
Set all values to np.nan

Read the snow data. Replace where there is data to snow observations.
Save


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
infile=os.path.join(DATA,"MODEL_DATA","snow_cover_202210_ll_grid.grib2")
origin="no-ar-cw"
if os.stat(infile).st_size==0:
    print(f"{infile} is empty!")
    sys.exit(1)

gfile = open(infile)
nf=ecc.codes_count_in_file(gfile)
gfile.close()
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

year=2022
month=10
ndays=calendar.monthrange(year, month)[1]

#it will save all values here:
# I will only take values on hour 6, which is when the snow data is available
values_modify = np.zeros([latdim*londim], dtype=np.float32)
values_leave=np.zeros([ndays*nhours-1,latdim*londim], dtype=np.float32)
ikey="param"
count_others=0
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
    if (key == param_code) and (hour == 600):
        print(f"Found key and input for {date} and time {hour}" )
        values_modify[:] = np.nan #ecc.codes_get_values(msg)
        i+=1
        found_var=True
    else:
        values_leave[count_others,:] = ecc.codes_get_values(msg)
        count_others+=1
gfile.close()
if not found_var:
    print(f"{param_code} not found in {infile}!")


# Now to read the data from snow
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

    return date, lat, lon, snowFrac
obs=OrderedDict()
for key in ["date","lat","lon","snowc"]:
    obs[key]=[]

import gc
save_index =[]
OBS_DATA=os.path.join(DATA,"CRYO_SW")
for file_path in sorted(Path(OBS_DATA).glob('*.dat')):
    print(f"Processing {file_path}")
    obs["date"],obs["lat"],obs["lon"],obs["snowc"] = get_data_fromtxt(str(file_path))
    #obs["date"].extend(date)
    #obs["lat"].extend(lat)
    #obs["lon"].extend(lon)
    #obs["snowc"].extend(snow)
    df_obs = pd.DataFrame(obs)
    for _,r in df_obs.iterrows():
        lat = r.lat
        lon = r.lon
        snow = r.snowc/100.
        obs_date = r.date
        gfile = open(infile)
        #with open(infile) as f:
        while True:
            msg = ecc.codes_grib_new_from_file(gfile) #gfile) #f)
            #msg = ecc.codes_grib_new_from_file(f)
            if msg is None: 
                gfile.close()
                break
            param = ecc.codes_get_long(msg, 'param')
            date = ecc.codes_get_long(msg, "date")
            hour = ecc.codes_get_long(msg, "time")
            also_hour = ecc.codes_get_long(msg, "hour")
            this_hour = str(hour)[0].zfill(2) #the hour will be 600, want to put it in 06 format
            this_date = str(date)+this_hour
            if (param == param_code) and (obs_date == this_date):
                latlonidx = ecc.codes_grib_find_nearest(msg,lat,lon)
                change_index = latlonidx[0]["index"]
                #print(f"Index to change {change_index}")
                #print(f"Before modifying: {values_modify[change_index]}")
                #print(f"Now changing to {snow}")
                #values_modify[change_index] = snow
                save_index.append(change_index)
                # Monitor memory usage
                object_size = sys.getsizeof(msg)
                #print(f"Message size {object_size}")
                gfile.close()
                # gc.collect()
                break
            #else:
            #    print(f"Finding {param}, {date} and {hour} {also_hour} but  obs_date != this_date ({obs_date} ? {this_date})")
        #print("Now closing")
    del df_obs
    import pdb 
    pdb.set_trace()

#df_obs = pd.DataFrame(obs)
#
#all_lats = df_obs.drop_duplicates(subset=["lat","lon"])
#all_dates = df_obs.drop_duplicates(subset=["date"])["date"].to_list()
#save_index =[]

#for _,r in df_obs.iterrows():
for date in all_dates:
    for _,r in all_lats.iterrows():
        lat = r.lat
        lon = r.lon
        snow = r.snowc/100.
        obs_date = r.date
        gfile = open(infile)
        #with open(infile) as f:
        while True:
            msg = ecc.codes_grib_new_from_file(gfile) #gfile) #f)
            if msg is None: break
            param = ecc.codes_get_long(msg, 'param')
            date = ecc.codes_get_long(msg, "date")
            hour = ecc.codes_get_long(msg, "time")
            this_hour = str(hour)[0].zfill(2) #the hour will be 600, want to put it in 06 format
            this_date = str(date)+this_hour
            if (param == param_code) and (obs_date == this_date):
                latlonidx = ecc.codes_grib_find_nearest(msg,lat,lon)
                change_index = latlonidx[0]["index"]
                #print(f"Index to change {change_index}")
                #print(f"Before modifying: {values_modify[change_index]}")
                #print(f"Now changing to {snow}")
                #values_modify[change_index] = snow
                save_index.append(change_index)
                break
        gfile.close()
    import pdb
    pdb.set_trace()

print("Paso esta parte")
gfile = open(infile)
while True:
    msg_clone = ecc.codes_grib_new_from_file(gfile)
    if msg_clone is None: break
    key = ecc.codes_get_long(msg_clone, ikey)
    hour = ecc.codes_get_long(msg, "time")
    if (key == param_code) and (hour == 600):
        print(f"Found key for cloning the output of {key} on hour {hour}" )
        msg2 = ecc.codes_clone(msg_clone)
        #break
    else:
        get_msg = ecc.codes_clone(msg_clone)
        other_msg.append(get_msg)
        i+=1
gfile.close()
outfile = os.path.join(DATA,"obs_202210_dummy.grib2")
#write the output
with open(outfile,'wb') as f:
    ecc.codes_set_values(msg2, values_modify)
    ecc.codes_write(msg2, f)
    for i in range(nf-1):
        ecc.codes_set_values(other_msg[i],other_values[i,:])
        ecc.codes_write(other_msg[i], f)

