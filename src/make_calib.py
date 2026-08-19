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
from pathlib import Path
from sunpy.map import Map
from astropy.io import fits
from datetime import datetime
from ld_profiles import coeffs_dict
from datetime import datetime, timedelta
from concurrent.futures import ProcessPoolExecutor
from sunpy.map.maputils import all_coordinates_from_map, coordinate_is_on_solar_disk
import config
from config import mkCalib as c

def limb_darkening_mu(shape, center, radius, coeffs):
    ny, nx = shape
    x0, y0 = center
    y, x = np.indices(shape)
    r = np.sqrt((x - x0)**2 + (y - y0)**2) / radius
    mu = np.sqrt(np.clip(1 - r**2, 0, 1))
    ld = np.polyval(coeffs[::-1], mu)
    ld[r > 1] = np.nan
    return ld

def openfits(file):
    with fits.open(file) as hdu:
        data= hdu[0].data
        header= hdu[0].header
        return data, header

def parse_suit(f):
    # Extracts YYYY-MM-DDTHH.MM.SS from filename
    t_str = os.path.basename(f).split('_')[5][:10]
    return datetime.strptime(t_str, "%Y-%m-%d")

def dt_now():
    dt= datetime.now()
    return f"[{dt.strftime('%H:%M:%S')}]"

def get_files(available_dates, i, data_path, FTR_NAME):
    """
    DESCRIPTION: Get list of suitable filepaths based on target date.
    INPUT: available dates list and target date index
    RETURNS: List of files, date time obj for target date
    """
    date= available_dates[i]
    if i==0:
        selected_dates= available_dates[:i+2*n+1]
    elif i== len(available_dates) or i==-1:
        selected_dates= available_dates[i-2*n:]
    else:
        selected_dates= available_dates[i-n:i+n+1]
    files = []
    for d in selected_dates:
        date_str = d.strftime('%Y-%m-%d')
        matching_files = sorted(glob.glob(os.path.join(data_path, f"*{date_str}*{FTR_NAME}*")))
        files.extend(matching_files)
    return files, date

def make_calib_frame(files, date, flat_path, FTR_NAME, SAVE_CALIB=False, OVERWRITE=False):
    calib_frame_name= f"{date.strftime('%Y-%m-%d')}_{FTR_NAME}_calib.fits"
    savepath= os.path.join(proj_path, 'data/processed/', calib_frame_name)
    if not OVERWRITE and os.path.exists(savepath):
        print(calib_frame_name, "--- File already exists")
        return
    print(f'Using {[os.path.basename(file) for file in files]}')
    coeffs= coeffs_dict[FTR_NAME] #limb_dkr_coeff
    flat,_= openfits(flat_path)
    seq = Map(files, sequence=True)
    datas=[]
    for m in seq:
        h= m.meta
        ld= limb_darkening_mu((h['NAXIS1'],h['NAXIS2']), (h['CRPIX1'], h['CRPIX2']), h['R_SUN'], coeffs=coeffs)
        data= np.nan_to_num(m.data, nan=0.0)
        corrected_data=m.data/(ld*flat)
        datas.append(corrected_data)
    med= np.nanmedian(datas, axis=0)
    if SAVE_CALIB:
        header= fits.Header()
        header['DATE']=date.strftime("%Y-%m-%d")
        header['F_NAME']= FTR_NAME
        header['COMMENT1']="Contamination correction file"
        fits.writeto(savepath, med, header=header, overwrite=True)
        print(dt_now(), calib_frame_name)

if __name__=='__main__':
    proj_path= config.proj_path 
    n=c.n
    data_list=sorted(glob.glob(os.path.join(c.data_path)))
    available_dates= sorted({parse_suit(f) for f in data_list})
    for i in range(len(available_dates)):
        selected_files, date= get_files(available_dates, i, c.data_path, config.FTR_NAME)
        make_calib_frame(selected_files, date, c.flat_path, config.FTR_NAME, c.SAVE_CALIB, c.OVERWRITE)

