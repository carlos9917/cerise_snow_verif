#%%
import xarray as xr
import pandas as pd
import datetime
import numpy as np
import re
#from scipy.spatial import KDTree
import pdb
import sys
#%%
model = xr.open_dataset("/ec/res4/scratch/nhd/CERISE/CRYO_SW/daily-avhrr-sce-nhl_ease-50_202205091200.nc",engine="netcdf4")
import pdb
pdb.set_trace()
# %%
model
# %%
