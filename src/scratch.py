#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Mon Aug  3 06:28:00 PM CEST 2026
@author: sarkar
@hostname: SARJA-TL26

DESCRIPTION
"""

import glob, os, sys
import numpy as np
from sunpy.map import Map
from astropy.io import fits
from datetime import datetime, timedelta
from concurrent.futures import ProcessPoolExecutor
from sunpy.map.maputils import all_coordinates_from_map, coordinate_is_on_solar_disk

def openfits(file):
    with fits.open(file) as hdu:
        data= hdu[0].data
        header= hdu[0].header
        return data, header

def parse_suit(f):
    # Extracts YYYY-MM-DDTHH.MM.SS from filename
    return os.path.basename(f).split('_')[5][:10]

def dt_now():
    dt= datetime.now()
    return f"[{dt.strftime('%H:%M:%S')}]"

if __name__=="__main__":
    FTR_NAME='NB06'
    OVERWRITE= True
    proj_path= os.path.abspath('..')
    data_path= '/run/media/sarkar/Elements/SUIT/sftp_drive/suit_data/level2fits/2025/*/*/normal_4k/'
    calib_path= os.path.join(proj_path, f'data/processed/')
    save_path= os.path.join(proj_path, 'products')

    data_files=sorted(glob.glob(os.path.join(data_path, f'*{FTR_NAME}*')))

    i= 50
    data_file= data_files[i]

    date= parse_suit(data_file)
    data, header= openfits(data_file)
    calib_file = sorted(glob.glob(os.path.join(calib_path, f"*{date}*{FTR_NAME}*.fits")))[0]
    calib_data, calib_header= openfits(calib_file)

    
    corrected_data= data/calib_data
    header['COMMENT']= "Limb darkening and contamination corrected"
    save_file= os.path.join(save_path, header['F_NAME'])
    if not OVERWRITE and os.path.exists(save_file):
        print(dt_now(), os.path.basename(save_file), "--- File already exists")
        sys.exit()
    else:
        fits.writeto(save_file, corrected_data, header=header, overwrite=OVERWRITE)
        print(dt_now(), os.path.basename(save_file), "---> File saved!")










