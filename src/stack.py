#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Wed Jul  8 03:30:34 PM CEST 2026
@author: sarkar
@hostname: SARJA-TL26

DESCRIPTION
"""
import matplotlib.pyplot as plt
import numpy as np
import glob, os
import astropy.units as u
from astropy.coordinates import SkyCoord
from sunpy.map import Map
from astropy.convolution import convolve, Box2DKernel
from astropy.io import fits

def openfits(file):
    with fits.open(file) as hdu:
        data= hdu[0].data
        header= hdu[0].header
        return data, header
def plot_img(img):
    plt.figure()
    plt.imshow(img, origin='lower')
    plt.show()

proj_path= os.path.abspath('..')
files= glob.glob(os.path.join(proj_path, 'data/raw/*.fits'))
flat_file= glob.glob(os.path.join(proj_path, 'data/external/NB06*.fits'))[0]
savepath= os.path.join(proj_path, 'data/interim/smooth_4k.fits')
flat,_= openfits(flat_file)
flat= np.nan_to_num(flat, nan=1.0)
seq = Map(files, sequence=True)
cropped_seq, cropped_data=[], []
s= int(1200/0.7)
for m in seq:
    cpx1, cpx2= int(m.meta['CRPIX1']), int(m.meta['CRPIX2'])
    cropped_flat= flat[cpx2-s:cpx2+s, cpx1-s:cpx1+s]
    cropped= m.data[cpx2-s:cpx2+s, cpx1-s:cpx1+s]
    cropped_data.append(cropped/cropped_flat)
med= np.nanmedian(cropped_data, axis=0)
kernel= Box2DKernel(15)
smooth= convolve(med, kernel, boundary='wrap')
_,header= openfits(files[0])
cpx1, cpx2= int(header['NAXIS1']/2), int(header['NAXIS2']/2)
smooth_4k= np.ones((header['NAXIS1'], header['NAXIS2']))
smooth_4k[cpx2-s:cpx2+s, cpx1-s:cpx1+s]= smooth
header['CRPIX1']= cpx1
header['CRPIX2']= cpx2
fits.writeto(savepath, smooth_4k, header=header, overwrite=True)




