#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Wed Jul  8 03:30:34 PM CEST 2026
@author: sarkar
@hostname: SARJA-TL26

DESCRIPTION
- Generates large contamination patch and large scale
artefact removal flat field.
- 5-6 days sun continuum images are needed.
- 1 image per day.
- Saves correction image in data/interim.
- 5 days images > Make featureless sun > 
Remove small scale features > Remove limb darkening > Calib frame
"""
import glob, os
import numpy as np
from sunpy.map import Map
import astropy.units as u
from astropy.io import fits
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from astropy.coordinates import SkyCoord
from astropy.convolution import convolve, Box2DKernel

def openfits(file):
    with fits.open(file) as hdu:
        data= hdu[0].data
        header= hdu[0].header
        return data, header
def plot_img(img, vmn= None, vmx= None):
    plt.figure()
    plt.imshow(img, origin='lower', vmin= vmn, vmax= vmx)
    plt.show()

if __name__=="__main__":
    #Define paths
    proj_path= os.path.abspath('..')
    files= glob.glob(os.path.join(proj_path, 'data/raw/*.fits'))
    flat_file= glob.glob(os.path.join(proj_path, 'data/external/NB06*.fits'))[0]
    savepath= os.path.join(proj_path, 'data/interim/correction.fits')
    # Open flat file
    flat,_= openfits(flat_file)
    flat= np.nan_to_num(flat, nan=1.0)
    # Open sun images
    seq = Map(files, sequence=True)
    img_datas=[m.data for m in seq]
    # Removing small scale structures
    med= np.nanmedian(img_datas, axis=0)
    kernel= Box2DKernel(15) # Smooting size (larger value >> More aggressive)
    smooth= convolve(med, kernel, boundary='wrap')
    # Generating headers for calib frame
    _,header= openfits(files[0])
    cpx1, cpx2= int(header['NAXIS1']/2), int(header['NAXIS2']/2)
    header['CRPIX1']= cpx1
    header['CRPIX2']= cpx2
    # Writing calib frame
    fits.writeto(savepath, smooth, header=header, overwrite=True)
    #visuals
    fig, ax= plt.subplots(1,3, sharex=True, sharey=True)
    ax[0].imshow(img_datas[0], origin='lower')
    ax[1].imshow(smooth, origin='lower')
    ax[2].imshow(img_datas[0]/smooth, origin='lower', vmin=0.9, vmax=1.1)
    plt.show()


