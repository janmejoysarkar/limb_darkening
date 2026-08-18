#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Mon Aug  3 06:28:00 PM CEST 2026
@author: sarkar
@hostname: SARJA-TL26

DESCRIPTION
"""

import glob, os
import numpy as np
from astropy.io import fits
from ld_profiles import coeffs_dict
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

def limb_darkening_mu(shape, center, radius, coeffs):
    """
    Gives solar limb darkening profile based on image dimensions (shape)
    sun center (center), radius of sun (radius) and limb dkr coeffs (coeffs)
    """
    ny, nx = shape
    x0, y0 = center
    y, x = np.indices(shape)
    r = np.sqrt((x - x0)**2 + (y - y0)**2) / radius
    mu = np.sqrt(np.clip(1 - r**2, 0, 1))
    ld = np.polyval(coeffs[::-1], mu)
    ld[r > 1] = np.nan
    return ld

def process_img(data_file, calib_file, flat_path, save_path, FTR_NAME, LD_CORR=True):
    data, h= openfits(data_file)
    calib_data, calib_header= openfits(calib_file)
    flat_data, _= openfits(flat_path)
    with np.errstate(divide='ignore', invalid='ignore'):
        if LD_CORR:
            ld= limb_darkening_mu((h['NAXIS2'],h['NAXIS1']), (h['CRPIX1'], h['CRPIX2']), h['R_SUN'], coeffs=coeffs_dict[FTR_NAME])
            corrected_data= data/(calib_data*ld*flat_data)
        else:
            corrected_data= data/(calib_data*flat_data)
    h['COMMENT']= "Limb darkening and contamination corrected"
    return corrected_data, h

def run(task):
    data_file, FTR_NAME, calib_path, flat_path, save_path, LD_CORR, OVERWRITE= task
    date= parse_suit(data_file)
    calib_matches = sorted(glob.glob(os.path.join(calib_path, f"*{date}*{FTR_NAME}*.fits")))
    if not calib_matches:
        print (dt_now(), 'CAUTION! Calib File for', date, 'not found! ---> *** Aborting process ***' )
        return
    calib_file= calib_matches[0]
    save_file= os.path.join(save_path, os.path.basename(data_file))
    if not OVERWRITE and os.path.exists(save_file):
        print(dt_now(), os.path.basename(save_file), "---> File already exists")
        return
    corrected_img, h= process_img(data_file, calib_file, flat_path, save_path, FTR_NAME, LD_CORR=LD_CORR)
    fits.writeto(save_file, corrected_img, header=h, overwrite=OVERWRITE)
    print(dt_now(), os.path.basename(calib_file), os.path.basename(save_file), "---> File saved!")
    
if __name__=="__main__":
    FTR_NAME='NB06'
    OVERWRITE= False
    LD_CORR= True
    proj_path= os.path.abspath('..')
    data_path= '/run/media/sarkar/Elements/SUIT/sftp_drive/suit_data/level2fits/2025/*/*/normal_4k/'
    calib_path= os.path.join(proj_path, f'data/processed/')
    flat_path= os.path.join(proj_path, 'data/external/NB06_fft_flat.fits')
    save_path= os.path.join(proj_path, 'products')
    data_files=sorted(glob.glob(os.path.join(data_path, f'*{FTR_NAME}*')))

    tasks=[(data_file, FTR_NAME, calib_path, flat_path, save_path, LD_CORR, OVERWRITE) for data_file in data_files]
    with ProcessPoolExecutor(max_workers=14) as executor:
        executor.map(run, tasks)
