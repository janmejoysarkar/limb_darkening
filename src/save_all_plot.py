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
import config

def readfits(file):
    with fits.open(file) as hdu:
        data= hdu[0].data
        return data

def run(file):
    filename= os.path.basename(file)
    data= readfits(file)
    fig, ax= plt.subplots(1, 1, dpi=300)
    im= ax.imshow(data, origin='lower', cmap='gray', vmin=VMN, vmax=VMX)
    del data
    ax.set_title(filename)
    fig.colorbar(im, ax= ax)
    fig.savefig(os.path.join(savepath, f'{filename}.png'), dpi=300)
    print(filename, '---> Saved!')
    fig.clf()
    plt.close(fig)
    gc.collect()

# GLOBAL #
proj_path= os.path.abspath('..')
savepath= os.path.join(config.proj_path, 'reports/processed_data_example/current')
VMN, VMX= 0.9, 1.1

if __name__=="__main__":
    datapath= os.path.join(config.proj_path, f'products/*{config.FTR_NAME}*.fits')
    files= sorted(glob.glob(datapath))
    RUN= True
    if RUN:
        with ProcessPoolExecutor(max_workers=12) as executor:
            executor.map(run, files)
