#!/usr/bin/env bash

# Retrieves mars data for a whole month in a regular grid
OUTDIR=/ec/res4/scratch/nhd/CERISE/ANALYSIS_FILES
PERIOD=201505
INI=20150501
END=20150531
GRID="lambert"
GRID="reg"
TIME=0000/0300/0600/0900/1200/1500/1800/2100
TIME=0000
PARAM=141 #snow depth
PARAM=260038 #snow cover (%) NOT IN CARRA! Possibly in ERA5?
PARAM=260289 #snow cover FRACTION (0 to 1)
OUTFILE=$OUTDIR/${PARAM}_${PERIOD}_$GRID.grib2
if [ $GRID == "reg" ] ; then
echo "Downloading in regular grid"
mars << eof
RETRIEVE,
    CLASS      = RR,
    TYPE       = AN,
    STREAM     = OPER,
    EXPVER     = prod,
    REPRES     = SH, 
    GRID       = 0.1/0.1,
    LEVTYPE    = SFC,
    PARAM      = $PARAM,
    DATE       = $INI/TO/$END,
    TIME       = 0000/0300/0600/0900/1200/1500/1800/2100,
    STEP       = 00,
    ORIGIN     = NO-AR-CW,
    TARGET     = "$OUTFILE",
    PADDING    = 0,
    PROCESS    = LOCAL
eof
else

echo "Downloading in lambert grid"
mars << eof
RETRIEVE,
    CLASS      = RR,
    TYPE       = AN,
    STREAM     = OPER,
    EXPVER     = prod,
    REPRES     = SH, 
    LEVTYPE    = SFC,
    PARAM      = $PARAM,
    DATE       = $INI/TO/$END,
    TIME       = $TIME,
    STEP       = 00,
    ORIGIN     = NO-AR-CW,
    TARGET     = "$OUTFILE",
    PADDING    = 0,
    PROCESS    = LOCAL
eof
fi
