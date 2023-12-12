#!/usr/bin/env bash

# Retrieves mars data for a whole month in a regular grid
OUTDIR=/ec/res4/scratch/nhd/CERISE/MODEL_DATA
PERIOD=201505
INI=20150501
END=20150531
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
    TARGET     = "$OUTDIR/snow_cover_${PERIOD}_ll_grid.grib2",
    PADDING    = 0,
    PROCESS    = LOCAL
eof
