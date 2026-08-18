#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Mon Aug 17 03:21:34 PM CEST 2026
@author: sarkar
@hostname: SARJA-TL26

DESCRIPTION
"""
import matplotlib.pyplot as plt
from astropy.io import fits
import os, glob
from concurrent.futures import ProcessPoolExecutor 

def readfits(file):
    with fits.open(file) as hdu:
        data= hdu[0].data
        return data

def plot(data, filename, savepath, VMN= None, VMX= None):
    plt.figure(dpi=300)
    plt.imshow(data, origin='lower', cmap='gray', vmin=VMN, vmax=VMX)
    plt.title(filename)
    plt.colorbar()
    plt.savefig(os.path.join(savepath, f'{filename}.png'), dpi=300)
    plt.close()

def run(file):
    filename= os.path.basename(file)
    print(filename)
    img_data= readfits(file)
    plot(img_data, filename, savepath, VMN=0, VMX=2.5e4)

# GLOBAL #
savepath= '/home/sarkar/Documents/'
VMN, VMX= 0.9, 1.1

if __name__=="__main__":
    proj_path= os.path.abspath('../..')
    datapath= os.path.join(proj_path, 'products/*.fits')
    files= sorted(glob.glob(datapath))
    
    with ProcessPoolExecutor(max_workers=14) as executor:
        executor.map(run, files)
        

