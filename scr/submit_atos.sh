#!/usr/bin/env bash
#SBATCH --mem-per-cpu=48GB
#SBATCH --time=12:00:00

ml conda
conda activate glat

#python clone_create_snow.py
PERIOD=202210
IDATE=20221001
EDATE=20221031
for DATE in $(seq -w $IDATE $EDATE); do
  python extract_indices_snow_obs.py ../../MODEL_DATA/snow_cover_${PERIOD}_600.grib2 ../../CRYO_SW/snow_cryo_5-10km_${DATE}06.dat
done
