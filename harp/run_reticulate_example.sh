#!/usr/bin/env bash

ml python3
ml ecmwf-toolbox
ml R/4.2.2

Rscript example_reticulate.R
