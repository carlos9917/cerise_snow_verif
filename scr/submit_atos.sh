#!/usr/bin/env bash
#SBATCH --mem-per-cpu=48GB
#SBATCH --time=12:00:00


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
OBS_DIR=../../CRYO_SW
MOD_DIR=../../MODEL_DATA
SCR=$PWD

#original setup
#GRIB_MODEL=$MOD_DIR/snow_cover_${PERIOD}_ll_grid.grib2
#GRIB_600=$MOD_DIR/snow_cover_${PERIOD}_ll_grid_600.grib2 
#TEMP_OBS=$MOD_DIR/template_obs_${PERIOD}_600.grib2
#OUT_OBS=$MOD_DIR/obs_${PERIOD}_600.grib2

#these are for binary snow
GRIB_MODEL=$MOD_DIR/snow_cover_${PERIOD}_ll_grid.grib2
GRIB_HOUR=$MOD_DIR/binary_snow_model_${PERIOD}_ll_grid_$HOUR.grib2 
TEMP_OBS=$MOD_DIR/template_obs_${PERIOD}_$HOUR.grib2
OUT_OBS=$MOD_DIR/binary_snow_cryo_${PERIOD}_ll_grid_$HOUR.grib2

# 1. Extract the hour $HOUR from a model file containing the whole month
# Dont need to do this if I  extract the data at the correct time beforehand!
if [ ! -f $GRIB_HOUR ]; then
  echo "Extracting hour $HOUR from $GRIB_MODEL"
  python extract_hour_from_model.py $HOUR $PERIOD $GRIB_MODEL $GRIB_HOUR
else
  echo "Skipping extraction of hour $HOUR from $GRIB_MODEL since $GRIB_HOUR already exists"
fi 

extract_points()
{
# 2. Loop through all dates to extract the points where snow
#    is defined based on the observation data in the snow*.dat files.
#    This is done in such a way to avoid memory issues with eccodes,
#    that does not seem to be able to close all files opened

echo "Extracting points in snow obs"
for DATE in $(seq -w $IDATE $EDATE); do
  concat_all=()
  SNOW=$OBS_DIR/snow_cryo_5-10km_${DATE}06.dat
  #split SNOW in smaller files to avoid memory issue
  split -d -a 3 -l 200 $SNOW tmp_snow_${DATE}_ --additional-suffix ".dat"

  for F in tmp_snow_${DATE}_*.dat; do
      OUT=$(basename $F .dat).csv
      python extract_indices_snow_obs.py $GRIB_HOUR $F $OUT
      concat_all+=($OUT)
  done
  echo ${concat_all[@]}
  cat ${concat_all[@]} > $OBS_DIR/snow_cryo_${DATE}06_idx_obs.csv
  rm -f tmp_snow_${DATE}_*.dat
  rm ${concat_all[@]}
done
}

extract_points
# 3. Using the list of points generated in step 2, clone the 
#    model data and set the points where there is no data
#    to missing data and define the points where there is data
# 3.1 First create a template file from the obs, all is set to missing here
echo "Creating template obs file"
python create_obs_template_from_model.py $GRIB_MODEL $TEMP_OBS

# 3.2 Create final obs file from obs template and points above
echo "Creating obs file from points and template file"
python create_grib_for_snow.py ${PERIOD:0:4} ${PERIOD:4:2} $TEMP_OBS $OUT_OBS
