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
from astropy.convolution import convolve, Box2DKernel, Gaussian2DKernel
from sunpy.map.maputils import all_coordinates_from_map, coordinate_is_on_solar_disk


def openfits(file):
    with fits.open(file) as hdu:
        data= hdu[0].data
        header= hdu[0].header
        return data, header
def plot_img(img, vmn= None, vmx= None):
    plt.figure()
    plt.imshow(img, origin='lower', vmin= vmn, vmax= vmx)
    plt.show()
def create_circular_mask(h, w, col, row, radius): 
    Y, X = np.ogrid[:h, :w]
    dist_from_center = np.sqrt((X - col)**2 + (Y-row)**2)
    mask = dist_from_center >= radius
    return mask #can be circular mask of any size

if __name__=="__main__":
    #Define paths
    PLOT= False
    proj_path= os.path.abspath('..')
    files= glob.glob(os.path.join(proj_path, 'data/raw/*.fits'))
    flat_file= glob.glob(os.path.join(proj_path, 'data/external/NB06*.fits'))[0]
    savepath= os.path.join(proj_path, 'data/interim/correction.fits')
    #Define values
    BLURSIZE=50
    # Open flat file
    flat,_= openfits(flat_file)
    flat= np.nan_to_num(flat, nan=1.0)
    # Open sun images
    seq = Map(files, sequence=True)
    cropped_data=[]
    s= int(1200/0.7) # Crop box in pixels (arcsec/platescale)
    # Centering sun and flat fielding all sun images
    for m in seq:
        cpx1, cpx2= int(m.meta['CRPIX1']), int(m.meta['CRPIX2'])
        cropped= m.data[cpx2-s:cpx2+s, cpx1-s:cpx1+s]
        cropped_data.append(cropped)
    # Removing small scale structures
    med= np.nanmedian(cropped_data, axis=0)
    kernel= Box2DKernel(BLURSIZE) # Smooting size (larger value >> More aggressive)
    smooth= convolve(med, kernel, boundary='wrap')
    # Generating headers for calib frame
    _,header= openfits(files[0])
    cpx1, cpx2= int(header['NAXIS1']/2), int(header['NAXIS2']/2)
    header['CRPIX1']= cpx1
    header['CRPIX2']= cpx2
    # Padding smooth sun to 4k
    smooth_4k= np.ones((header['NAXIS1'], header['NAXIS2']))
    smooth_4k[cpx2-s:cpx2+s, cpx1-s:cpx1+s]= smooth
    # Writing calib frame
    fits.writeto(savepath, smooth_4k, header=header, overwrite=True)
    
    #calibration
    for m in seq:
        header= m.meta
        cpx1, cpx2= int(m.meta['CRPIX1']), int(m.meta['CRPIX2'])
        cropped= m.data[cpx2-s:cpx2+s, cpx1-s:cpx1+s]
        cropped= cropped/smooth
        corr_frame= np.ones((header['NAXIS1'], header['NAXIS2']))
        corr_frame[cpx2-s:cpx2+s, cpx1-s:cpx1+s]= cropped
        hpc_coords= all_coordinates_from_map(m)
        mask= np.invert(coordinate_is_on_solar_disk(hpc_coords))
        corr_frame[mask]=np.nan
        savedata= os.path.join(proj_path, 'data/processed/', header['F_NAME'])
        sv_m= Map(corr_frame, header)
        sv_m.save(savedata, overwrite=True)
        print(header['F_NAME'])

    #### TESTING ####
    #visuals
    cropped_data= np.array(cropped_data)/smooth
    if PLOT:
        fig, ax= plt.subplots(2,4, sharex=True, sharey=True)
        ax=ax.ravel()
        ax[0].imshow(cropped_data[1], origin='lower', vmin= np.min(smooth), vmax= np.max(smooth), cmap='gray')
        ax[0].set_title(seq[1].meta['T_OBS'][:10])
        ax[1].imshow(smooth, origin='lower', cmap='gray')
        ax[1].set_title(f'gaussian= {BLURSIZE}px')
        for i in range(5):
            mask= create_circular_mask(2*s, 2*s, s, s, int(seq[i].meta['R_SUN']))
            corrected_data[i][mask]= np.nan
            ax[i+2].imshow(corrected_data[i], origin='lower', vmin=0.9, vmax=1.1, cmap='gray')
            ax[i+2].set_title(seq[i].meta['T_OBS'][:10])
        plt.tight_layout()
        plt.savefig(os.path.join(proj_path, f'reports/smooth_{BLURSIZE}.pdf'), dpi=600)
        plt.show()
