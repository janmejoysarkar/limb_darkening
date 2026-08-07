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
from pathlib import Path
from sunpy.map import Map
from astropy.io import fits
from datetime import datetime
import matplotlib.pyplot as plt
from ld_profiles import coeffs_dict
from datetime import datetime, timedelta
from astropy.convolution import convolve, Box2DKernel, Gaussian2DKernel
from sunpy.map.maputils import all_coordinates_from_map, coordinate_is_on_solar_disk

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

def plot_img(img, vmn= None, vmx= None, name=None):
    plt.figure()
    plt.imshow(img, origin='lower', cmap='gray', vmin= vmn, vmax= vmx)
    plt.colorbar()
    if name:
        plt.title(name)
    plt.show()

def savefits(data, filename, header=None):
    fits.writeto(os.path.join(proj_path,'products', filename), data)

def getfilelist(target_date, n):
    before = [d for d in available_dates if d < target_date]
    after = [d for d in available_dates if d > target_date]
    selected_dates = []
    if target_date in available_dates:
        selected_dates.append(target_date)
    if not before:
        selected_dates += after[:2*n]
        print(f"{FTR_NAME} observations unavailable before {target_date}.")
    elif not after:
        selected_dates += before[-2*n:]
        print(f"{FTR_NAME} observations unavailable after {target_date}.")
    else:
        selected_dates += before[-n:]
        selected_dates += after[:n]
    selected_dates = sorted(selected_dates)
    print(f"Using {FTR_NAME} data for {[date.strftime('%Y-%m-%d') for date in selected_dates]}.")
    files = []
    for d in selected_dates:
        folder = BASE / f"{d.year:04d}" / f"{d.month:02d}" / f"{d.day:02d}" / 'normal_4k'
        files.extend(sorted(folder.glob(f"*{FTR_NAME}*.fits")))
    return files

if __name__=="__main__":
    #Define paths
    proj_path= os.path.abspath('..')
    flat_path= os.path.join(proj_path, 'data/external/NB06_fft_flat.fits')
    BASE=Path('/run/media/sarkar/Elements/SUIT/sftp_drive/suit_data/level2fits/')
    FTR_NAME='NB06'
    TARGET_DATE= datetime.strptime("2025-03-19", "%Y-%m-%d").date()
    INTVL=1
    PLOT= False
    SAVE_CALIB=True
    # Get image filelist
    available_dates = sorted(
        datetime.strptime(f"{y.name}/{m.name}/{d.name}", "%Y/%m/%d").date()
        for y in BASE.iterdir() if y.is_dir()
        for m in y.iterdir() if m.is_dir()
        for d in m.iterdir() if d.is_dir()
        )
    files= getfilelist(TARGET_DATE, INTVL)
    # Limb darkening coefficients
    coeffs= coeffs_dict[FTR_NAME]
    # Open sun images
    flat,_= openfits(flat_path)
    # Make median
    seq = Map(files, sequence=True)
    datas=[]
    for m in seq:
        h= m.meta
        ld= limb_darkening_mu((h['NAXIS1'],h['NAXIS2']), (h['CRPIX1'], h['CRPIX2']), h['R_SUN'], coeffs=coeffs)
        corrected_data=m.data/(ld*flat)
        datas.append(corrected_data)
    datas= np.array(datas)
    med= np.nanmedian(datas, axis=0)
    # Save calib frame
    if SAVE_CALIB:
        calib_frame_name= f"{TARGET_DATE.strftime("%Y-%m-%d")}_{FTR_NAME}_calib.fits"
        header= fits.Header()
        header['DATE']=TARGET_DATE.strftime("%Y-%m-%d")
        header['F_NAME']= FTR_NAME
        header['COMMENT1']="Contamination correction file"
        fits.writeto(os.path.join(proj_path, 'data/interim/', calib_frame_name), med, header=header, overwrite=True)
        print(calib_frame_name)
    '''
    for i in range(len(datas)):
        corr_frame= datas[i]/med
        m= seq[i]
        h= m.meta
        hpc_coords= all_coordinates_from_map(m)
        mask= np.invert(coordinate_is_on_solar_disk(hpc_coords))
        corr_frame[mask]=np.nan
        _m= Map(corr_frame, m.meta)
        filename= h['F_NAME']
        _m.save(os.path.join(proj_path,'data/processed',filename), overwrite=True)
        print(filename)
    '''
