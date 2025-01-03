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
GRIB_MODEL=$MOD_DIR/snow_cover_${PERIOD}.grib2 # this one is the grid in lambert projection
GRIB_MODEL=$MOD_DIR/snow_cover_${PERIOD}_regular_grid.grib2 #this one in the regular grid

GRIB_HOUR=$MOD_DIR/binary_snow_model_${PERIOD}_ll_grid_$HOUR.grib2
TEMP_OBS=$MOD_DIR/template_obs_${PERIOD}_$HOUR.grib2
OUT_OBS=$MOD_DIR/binary_snow_cryo_${PERIOD}_ll_grid_$HOUR.grib2

CSV_LL_MODEL=model_lat_lon_ordered.csv #for tha lambert
CSV_LL_MODEL=model_reg_lat_lon_ordered.csv #for the reg grid


#this one reads the nc file and dumps the lat,lon and values above threshold in a csv file
for F in $(ls $OBS_DIR/daily-*${PERIOD}0?????.nc); do
  echo "Processing $F"
  BNAME=$(basename $F)
  SUF=$(echo $BNAME | awk 'BEGIN { FS="_"; } { print $3 }')
  DATE=$(basename $SUF .nc)
  DAY=${DATE:0:8}
  python get_values_from_nc_file.py $F $CSV_LL_MODEL csv_files_regular_grid/ll_snow_${DAY}.csv
done

