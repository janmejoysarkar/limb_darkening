#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Wed Jul  8 01:33:38 PM CEST 2026
@author: sarkar
@hostname: SARJA-TL26

DESCRIPTION
"""
import numpy as np
import matplotlib.pyplot as plt
import os
import glob
from sunpy.map import Map
from scipy.optimize import curve_fit
from astropy.io import fits

def ComputePixelDistances(image, center_x,center_y):
    num_rows, num_columns = image.shape
    distances = np.zeros((num_rows, num_columns))
    for y in range(num_rows):
        for x in range(num_columns):
            distances[y, x] = np.sqrt((x- center_x)**2 +(y - center_y)**2)
    return distances

def SuitMedianLimbDarkening(image,radius_in_pixel,distance_map,block_size,mu_limit=0.0000001):
    # this is mainly to calculate QS std from continuum 
    flat_image = image.flatten()
    flat_distances = distance_map.flatten()
    # Combine distances with pixel values
    pixel_data = np.column_stack((flat_distances,
    flat_image)) # taking the top left pixel and moving rightwards
    # Sort pixels by distance
    sorted_pixel_data = pixel_data[np.argsort(pixel_data[:,
    0])] 
    num_pixels = sorted_pixel_data.shape[0]
    blocks = []
    number_of_points_in_block=[]
    for start in range(0, num_pixels, block_size):
        end = min(start +
        block_size, num_pixels)
        block = sorted_pixel_data[start:end]
        blocks.append(block)
        number_of_points_in_block.append(len(block))
    final_mean_distance=[]
    final_value_signal=[]
    points_in_blocks_after_conver=[]
    for block in blocks:
        # Extract distances and values from the block
        distances_block = block[:, 0]
        values_block = block[:, 1]
        final_mean_distance.append(np.nanmedian(distances_block))
        final_value_signal.append(np.nanmedian(values_block))
    R_sun=radius_in_pixel*(np.ones(len(final_mean_distance)))
    mu=np.sqrt(((R_sun**2)-np.array(final_mean_distance)**2)/(R_sun**2))
    drop_low_mu_mask=mu>mu_limit
    mu_drop_last_bin=mu[drop_low_mu_mask]
    final_value_signal_drop_last_bin=np.array(final_value_signal)[drop_low_mu_mask]
    return mu_drop_last_bin, final_value_signal_drop_last_bin

def poly_5(x, a, b,c,d,e,f):
    return (a*(x**5)) + (b*(x**4)) + (c*(x**3)) + (d*(x**2)) + (e*x) + f

def ComputeMu(image,center_x,center_y,radius):
    distances=ComputePixelDistances(image, center_x,center_y)
    mu_image=np.sqrt(((radius**2)-(distances)**2)/(radius**2))
    return mu_image

def openfits(file):
    with fits.open(file) as hdu:
        data= hdu[0].data
        return data

if __name__=='__main__':
    PLOT= True 
    FLAT_CORR= True
    proj_path= os.path.abspath('..')
    file= glob.glob(os.path.join(proj_path, "data/raw/*.fits"))[0]
    m= Map(file)
    if FLAT_CORR:
        flat_file= glob.glob(os.path.join(proj_path, "data/external/NB06_fft*"))[0]
        patch_file= os.path.join(proj_path, "data/interim/correction.fits")
        flat= openfits(flat_file)
        patch= openfits(patch_file)
        data= m.data/(flat*patch)
    else:
        data= m.data
    crpix1, crpix2= m.meta['CRPIX1'], m.meta['CRPIX2']
    rad= m.meta['R_SUN']
    dist_map= ComputePixelDistances(data, crpix1, crpix2)
    mu, last_bin= SuitMedianLimbDarkening(data, rad, dist_map, 2500, mu_limit= 0.01)
    coeff, covar= curve_fit(poly_5, mu, last_bin)
    mu_vals= ComputeMu(data, crpix1, crpix2, rad)
    fit_surface= poly_5(mu_vals, *coeff)
    limb_dkr_corrected= data/fit_surface

    #VISUALS
    if PLOT:
        plt.figure()
        plt.imshow(limb_dkr_corrected, origin='lower', vmin=0.9, vmax=1.1)
        plt.show()
