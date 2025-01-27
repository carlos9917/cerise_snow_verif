#!/usr/bin/env bash

harmonie_file="../../sample_data/CARRA1/260289_20150501_analysis_NO-AR-CE_reg.grib2"
input_file="../../sample_data/Cryo_clim/reg_ll_prob_snow_c_date.nc"
output_file="snow_cover_from_carra.nc"

python upsample_carra_to_metnogrid.py $harmonie_file $input_file $output_file
