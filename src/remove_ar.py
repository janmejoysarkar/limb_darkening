#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Fri Aug 14 05:58:31 PM CEST 2026
@author: sarkar
@hostname: SARJA-TL26

DESCRIPTION
To remove active regions from SUIT images using HMI as reference.
"""

import numpy as np
from scipy.ndimage import binary_dilation
import sunpy.map
from reproject import reproject_interp
from skimage.morphology import disk
from astropy.convolution import convolve, Gaussian2DKernel
import os, glob
from datetime import datetime, timezone
from sunpy.physics.differential_rotation import differential_rotate
from concurrent.futures import ProcessPoolExecutor
import config
from config import arMask as c

def pair_suit_and_hmi(suit_files, hmi_files):
    """Pairs each SUIT file with the closest HMI file by timestamp."""
    
    def parse_suit(f):
        # Extracts YYYY-MM-DDTHH.MM.SS from filename
        t_str = os.path.basename(f).split('_')[5][:19]
        return datetime.strptime(t_str, "%Y-%m-%dT%H.%M.%S").replace(tzinfo=timezone.utc)

    def parse_hmi(f):
        # Extracts YYYYMMDD_HHMMSS from filename
        t_str = os.path.basename(f).split('.')[2][:15]
        return datetime.strptime(t_str, "%Y%m%d_%H%M%S").replace(tzinfo=timezone.utc)

    hmi_times = [(parse_hmi(hf), hf) for hf in hmi_files]
    pairs = {}

    for sf in suit_files:
        st = parse_suit(sf)
        diff_sec, best_hmi = min((abs((ht - st).total_seconds()), hf) for ht, hf in hmi_times)
        if diff_sec > 3600:
            print(f"Alert: Time gap > 1 hour ({diff_sec / 3600:.2f} hrs) for {os.path.basename(sf)}")
        pairs[sf] = best_hmi
    return pairs

def get_suit_magnetic_mask(suit_file, hmi_file, threshold_G=10.0, min_mu=0, max_mu=1, dilate_arcsec=0):
    """
    Creates and optionally dilates a binary mask for SUIT data based on HMI radial magnetic field (|B|/mu > threshold).
    Applies cutoffs to min_mu (div-by-zero protection) and max_mu (limb-effect rejection).
    """
    suit_map = sunpy.map.Map(suit_file)
    hmi_map = sunpy.map.Map(hmi_file)
    # Compute mu = cos(theta) on the HMI grid
    coords = sunpy.map.all_coordinates_from_map(hmi_map)
    r_rsun = np.sqrt(coords.Tx**2 + coords.Ty**2) / hmi_map.rsun_obs
    mu = np.sqrt(np.clip(1.0 - r_rsun**2, 0, 1))
    # Calculate mu corrected B
    with np.errstate(divide='ignore', invalid='ignore'):
        b_radial = np.abs(hmi_map.data) / mu
        # Mask out limb region where mu < min_mu OR mu > max_mu
        b_radial[(mu < min_mu) | (mu > max_mu)] = np.nan
        del mu
        b_radial_map = sunpy.map.Map(b_radial, hmi_map.meta)
        del hmi_map
        del b_radial
        # Differential rotation correction
        b_radial_map = differential_rotate(b_radial_map, time=suit_map.date)
        # Reproject HMI radial magnetic field to SUIT grid
        reprojected_b, _ = reproject_interp(b_radial_map, suit_map.wcs)
        del _
        del b_radial_map
        reprojected_b= convolve(reprojected_b, Gaussian2DKernel(x_stddev=5))
        mask = (reprojected_b > threshold_G)
        del reprojected_b
    # Dilate mask by requested arcseconds
    pix_scale = suit_map.meta['CDELT1']# arcsec / pixel
    radius_pix = int(round(dilate_arcsec / pix_scale))
    if radius_pix > 0:
        struct_elem=disk(radius_pix)
        mask = binary_dilation(mask, structure=struct_elem)
    suit_masked_data = np.where(mask == 0, suit_map.data, np.nan)
    return mask, suit_masked_data, suit_map

def run(filepair):
    suit_file, hmi_file = filepair
    savepath= os.path.join(c.savedir, os.path.basename(suit_file))
    # Skip processing immediately if the file already exists
    if not c.OVERWRITE and os.path.exists(savepath):
        print(f"Skipping {os.path.basename(suit_file)} - already exists.")
        return
    print (os.path.basename(suit_file), os.path.basename(hmi_file), "---> Files loaded")
    mask, suit_masked, suit_map = get_suit_magnetic_mask(
        suit_file, 
        hmi_file, 
        c.threshold_G, 
        c.min_mu, 
        c.max_mu,  # Limits maximum mu threshold
        c.dilate_arcsec)
    if c.SAVE:
        print('File processed')
        m= sunpy.map.Map(suit_file)
        save_map= sunpy.map.Map(suit_masked, m.meta)
        save_map.save(savepath, overwrite=True)
        print (os.path.basename(suit_file), "---> File saved")

if __name__=='__main__':
    suit_files= sorted(glob.glob(c.suit_filepath))
    hmi_files= sorted(glob.glob(c.hmi_filepath))
    filepairs= pair_suit_and_hmi(suit_files, hmi_files)
    with ProcessPoolExecutor(max_workers=c.max_workers) as executor:
        executor.map(run, filepairs.items())

