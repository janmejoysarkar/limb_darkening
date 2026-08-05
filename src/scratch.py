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
from sunpy.map import Map
import astropy.units as u
from astropy.io import fits
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from astropy.coordinates import SkyCoord
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


if __name__=="__main__":
    #Define paths
    PLOT= False
    proj_path= os.path.abspath('..')
    flat_path= os.path.join(proj_path, 'data/external/NB06_fft_flat.fits')
    files= glob.glob(os.path.join(proj_path, 'data/raw/*.fits'))
    #Define values
    coeffs=[2.319672491021010641e-01,
            -3.933296342033205661e-01,
            4.076824650615816559e+00,
            -6.980650525762820635e+00,
            6.478537717621083658e+00,
            -2.408857307324229868e+00]
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
    fits.writeto(os.path.join(proj_path, 'products/median_ld_corrected.fits'), med)

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

