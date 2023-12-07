#!/usr/bin/env bash

# Retrieves mars data for a whole month in a regular grid


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
    DATE       = 20221001/TO/20221031,
    TIME       = 0000/0300/0600/0900/1200/1500/1800/2100,
    STEP       = 00,
    ORIGIN     = NO-AR-CW,
    TARGET     = "/ec/res4/scratch/nhd/example_snow_cover_202210.grib2",
    PADDING    = 0,
    PROCESS    = LOCAL
eof
