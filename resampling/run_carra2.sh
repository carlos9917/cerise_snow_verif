#!/usr/bin/env bash
#SBATCH --mem-per-cpu=16GB
#SBATCH --time=12:00:00

ml conda
conda activate gpp
CRYO_DATA=/ec/res4/scratch/nhd/CERISE/CRYO_NC
IDATE=20150501
EDATE=20150520
input_var="prob_snow_c" #the variable I want to read from the grib file
output_var="snowc" # the variable to dump as extra variable in the cryo file for comparison. The code will calculate the binary variable too
ref_harm=../../CARRA2/snowc_2015-01-01_reg.grib2 #reading the grid from this sample file

for DATE in $(seq -w $IDATE $EDATE); do
IFILE=$CRYO_DATA/daily-avhrr-sce-nhl_ease-50_${DATE}1200.nc
OFILE=cryo_${DATE}1200_resampled.nc
echo "Reading $IFILE"
python cryo2carragrid.py $IFILE $OFILE --harmonie_file $ref_harm --var_in ${input_var} --var_out ${output_var}
exit

done
