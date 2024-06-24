#!/usr/bin/env bash
#/ec/res4/scratch/nhd/CERISE/CRYO_NC/daily-avhrr-sce-nhl_ease-50_201503021200.nc
ml conda
conda activate gpp
IDATE=20150501
EDATE=20150531
for DATE in $(seq -w $IDATE $EDATE); do
IFILE=/ec/res4/scratch/nhd/CERISE/CRYO_NC/daily-avhrr-sce-nhl_ease-50_${DATE}1200.nc
OFILE=daily-avhrr-sce-nhl_ease-50_${DATE}1200_resampled.nc
python snowcover_upscale_pyresample.py $IFILE $OFILE
exit

done
