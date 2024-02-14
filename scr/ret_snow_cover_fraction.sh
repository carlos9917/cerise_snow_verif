#!/usr/bin/env bash

# Retrieves mars data for a whole month in a regular grid
OUTDIR=/ec/res4/scratch/nhd/CERISE/FC_OB_DATA_USING_CRYO_NC
PERIOD=201505
INI=20150501
END=20150531
GRID="lambert"
GRID="reg"
TIME=0000/0300/0600/0900/1200/1500/1800/2100
TIME=0000

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
    PARAM      = 260289,
    DATE       = $INI/TO/$END,
    TIME       = 0000/0300/0600/0900/1200/1500/1800/2100,
    STEP       = 00,
    ORIGIN     = NO-AR-CW,
    TARGET     = "$OUTDIR/snow_cover_${PERIOD}_regular_grid.grib2",
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
    PARAM      = 260289,
    DATE       = $INI/TO/$END,
    TIME       = $TIME,
    STEP       = 00,
    ORIGIN     = NO-AR-CW,
    TARGET     = "$OUTDIR/snow_cover_${PERIOD}.grib2",
    PADDING    = 0,
    PROCESS    = LOCAL
eof
fi
