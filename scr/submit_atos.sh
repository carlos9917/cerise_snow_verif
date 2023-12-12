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
OBS_DIR=../../CRYO_SW
MOD_DIR=../../MODEL_DATA
SCR=$PWD

echo "Extracting hour 600 from $$MOD_DIR/snow_cover_${PERIOD}_ll_grid.grib2"
python extract_hour_from_model.py $MOD_DIR/snow_cover_${PERIOD}_ll_grid.grib2

for DATE in $(seq -w $IDATE $EDATE); do
  concat_all=()
  SNOW=$OBS_DIR/snow_cryo_5-10km_${DATE}06.dat
  GRIB=$MOD_DIR/snow_cover_${PERIOD}_ll_grid_600.grib2 #snow_cover_${PERIOD}_600.grib2
  #split SNOW in smaller files to avoid memory issue
  split -d -a 3 -l 200 $SNOW tmp_snow_${DATE}_ --additional-suffix ".dat"
  for F in tmp_snow_${DATE}_*.dat; do
      OUT=$(basename $F .dat).csv
      python extract_indices_snow_obs.py $GRIB $F $OUT
      concat_all+=($OUT)
  done
  echo ${concat_all[@]}
  cat ${concat_all[@]} > $OBS_DIR/snow_cryo_${DATE}06_idx_obs.csv
  rm -f tmp_snow_${DATE}_*.dat
  rm ${concat_all[@]}
done
