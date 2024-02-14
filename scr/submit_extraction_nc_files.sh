#!/usr/bin/env bash
#SBATCH --mem-per-cpu=16GB
#SBATCH --time=48:00:00


ATOS=ac
if [[ "$HOSTNAME" =~ .*"$ATOS".* ]]; then
  echo "Working in ECMWF"
  ml conda
  conda activate glat
fi


#python clone_create_snow.py
PERIOD=201505
IDATE=${PERIOD}01
EDATE=${PERIOD}31
HOUR=6
OBS_DIR=../../CRYO_NC
MOD_DIR=../../FC_OB_DATA_USING_CRYO_NC
SCR=$PWD

#these are for binary snow
GRIB_MODEL=$MOD_DIR/snow_cover_${PERIOD}_fcst.grib2 # this one is the grid in lambert projection
#GRIB_MODEL=$MOD_DIR/snow_cover_${PERIOD}_regular_grid.grib2 #this one in the regular grid

GRIB_HOUR=$MOD_DIR/binary_snow_model_${PERIOD}_ll_grid_$HOUR.grib2 
TEMP_OBS=$MOD_DIR/template_obs_${PERIOD}_$HOUR.grib2
OUT_OBS=$MOD_DIR/binary_snow_cryo_${PERIOD}_ll_grid_$HOUR.grib2
CSV_LL_MODEL=model_lat_lon_ordered.csv #for tha lambert
#CSV_LL_MODEL=model_reg_lat_lon_ordered.csv #for the reg grid

#Step 1.
# this one extracts all the lat lon pairsfrom the model
#python extract_latlon_from_model.py $PERIOD $GRIB_MODEL $CSV_LL_MODEL

# Step 2
#this one reads the nc file and dumps the lat,lon and values above threshold in a csv file
# this can be slow, so I split it in 3 scripts in submit_split1,2,3 in this directory
#for F in $(ls $OBS_DIR/daily-*${PERIOD}??????.nc); do
#  echo "Processing $F"
#  python get_values_from_nc_file.py $F $CSV_LL_MODEL
#done

# This one uses the files above to clone a model file and replace values
# I got from the step above. The model file is for the whole month
python create_gridded_obs_from_cloned_model_file.py $GRIB_MODEL $MOD_DIR/snow_cover_${PERIOD}_obs.grib2
