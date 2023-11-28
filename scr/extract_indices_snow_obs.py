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
import gc

#gfile = open(infile)
#nf=ecc.codes_count_in_file(gfile)
#gfile.close()
#nhours=8
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

    return date, lat, lon, snowFrac
obs=OrderedDict()
for key in ["date","lat","lon","snowc"]:
    obs[key]=[]

#OBS_DATA=os.path.join(DATA,"CRYO_SW")
#for file_path in sorted(Path(OBS_DATA).glob('*.dat')):
def get_indices_snow_obs(param_code:int, cryo_file:str,infile:str) -> list:
    save_index=[]
    print(f"Processing {cryo_file}")
    obs["date"],obs["lat"],obs["lon"],obs["snowc"] = get_data_fromtxt(cryo_file)
    df_obs = pd.DataFrame(obs)
    file_date = os.path.split(cryo_file)[-1].split("_")[-1].replace(".dat","")
    save_index = []
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
                #object_size = sys.getsizeof(msg)
                #print(f"Message size {object_size}")
                gfile.close()
                gc.collect()
                break
            else:
                print(f"Finding {param}, {date} and {hour} {also_hour} but  obs_date != this_date ({obs_date} ? {this_date})")
    del df_obs
    return save_index

if __name__ == "__main__":
    DATA="/ec/res4/scratch/nhd/CERISE/"
    infile=os.path.join(DATA,"MODEL_DATA","snow_cover_202210_600.grib2")
    origin="no-ar-cw"
    param_code = 260289
    if len(sys.argv) == 1:
        print("Please provide the input grib file and the input cryo ascii file")
        sys.exit(1)
    else:
        infile = sys.argv[1]
        cryo_file = sys.argv[2]
    
    if os.stat(infile).st_size==0:
        print(f"{infile} is empty!")
    indices= get_indices_snow_obs(param_code,cryo_file,infile)
    obs_file = os.path.join(DATA,"CRYO_SW",cryo_file.replace(".dat","_ix.npz"))
    #out_file = os.path.join(cryo_file
    with open(out_file,"wb") as f:
        np_list = np.array(indices)
        np.save(f,np_list)
