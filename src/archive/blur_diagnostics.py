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
import matplotlib.pyplot as plt
import numpy as np
import glob, os
import astropy.units as u
from astropy.coordinates import SkyCoord
from sunpy.map import Map
from astropy.convolution import convolve, Box2DKernel
from astropy.io import fits
from scipy.optimize import curve_fit

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
    proj_path= os.path.abspath('..')
    files= glob.glob(os.path.join(proj_path, 'data/raw/*.fits'))
    flat_file= glob.glob(os.path.join(proj_path, 'data/external/NB06*.fits'))[0]
    # Open flat file
    flat,_= openfits(flat_file)
    flat= np.nan_to_num(flat, nan=1.0)
    # Open sun images
    seq = Map(files, sequence=True)
    cropped_seq, cropped_data=[], []
    s= int(1200/0.7) # Crop box in pixels (arcsec/platescale)
    # Centering sun and flat fielding all sun images
    for m in seq:
        cpx1, cpx2= int(m.meta['CRPIX1']), int(m.meta['CRPIX2'])
        cropped_flat= flat[cpx2-s:cpx2+s, cpx1-s:cpx1+s]
        cropped= m.data[cpx2-s:cpx2+s, cpx1-s:cpx1+s]
        cropped_data.append(cropped/cropped_flat)
    # Removing small scale structures
    med= np.nanmedian(cropped_data, axis=0)
    blur_rads= [5,10,15,25,50,75,100]
    frames= []
    for blur_rad in blur_rads:
        kernel= Box2DKernel(blur_rad) # Smooting size (larger value >> More aggressive)
        smooth= convolve(med, kernel, boundary='wrap')
        # Generating headers for calib frame
        _,header= openfits(files[0])
        cpx1, cpx2= int(header['NAXIS1']/2), int(header['NAXIS2']/2)
        header['CRPIX1']= cpx1
        header['CRPIX2']= cpx2
        # Padding smooth sun to 4k
        smooth_4k= np.ones((header['NAXIS1'], header['NAXIS2']))
        smooth_4k[cpx2-s:cpx2+s, cpx1-s:cpx1+s]= smooth
        # Removing limb darkening from smooth sun 
        rad=header['R_SUN']
        dist_map= ComputePixelDistances(smooth_4k, cpx1, cpx2)
        mu, last_bin= SuitMedianLimbDarkening(smooth_4k, rad, dist_map, 2500, mu_limit= 0.01)
        coeff, covar= curve_fit(poly_5, mu, last_bin)
        mu_vals= ComputeMu(smooth_4k, cpx1, cpx2, rad)
        fit_surface= poly_5(mu_vals, *coeff)
        limb_dkr_corrected= smooth_4k/fit_surface
        # Writing calib frame
        savepath= os.path.join(proj_path, f'data/interim/correction_{blur_rad}.fits')
        fits.writeto(savepath, limb_dkr_corrected, header=header, overwrite=True)
        frames.append(limb_dkr_corrected)

    for frame, blur_rad in zip(frames, blur_rads):
        plt.figure()
        plt.imshow(frame, cmap='gray', vmin=0.9, vmax=1.1, origin='lower')
        plt.title(f'boxcar={blur_rad}')
        plt.tight_layout()
        plt.savefig(os.path.join(proj_path,f'reports/ldc_{blur_rad}.pdf'), dpi=600)
        plt.close()

    stdevs, means=[], []
    r,c,sz= 2500, 1200, 200
    fig, ax= plt.subplots(2,4, sharex=True, sharey=True)
    ax=ax.ravel()
    for i in range(7):
        frame_crop= frames[i][r:r+sz, c:c+sz]
        ax[i].imshow(frame_crop)
        ax[i].set_title(f'boxcar={blur_rads[i]}')
        stdev= np.std(frame_crop)
        mean= np.mean(frame_crop)
        stdevs.append(stdev)
        means.append(mean)
    plt.savefig(os.path.join(proj_path,f'reports/st_devs.pdf'), dpi=600)
    plt.show()
    plt.figure('stats')
    plt.plot(blur_rads, stdevs)
    plt.xlabel('Blur radius')
    plt.ylabel('Stdev')
    plt.savefig(os.path.join(proj_path,f'reports/st_dev_curve.pdf'), dpi=600)
    plt.show()

    #Line profile
    y, xmn, xmx= 2540, 850, 1200
    plt.figure('line_profiles', figsize=(10,4))
    plt.subplot(1,2,1)
    plt.imshow(frames[0], origin='lower', vmin=0.9, vmax= 1.1)
    plt.hlines(y, xmn, xmx, color='red')
    plt.subplot(1,2,2)
    for frame, blur_rad in zip(frames, blur_rads):
        plt.plot(frame[y, xmn:xmx], label= blur_rad)
    plt.legend()
    plt.xlabel('Pixels')
    plt.title('Line profiles for varying blur radii')
    plt.savefig(os.path.join(proj_path,f'reports/line_profile_2.pdf'), dpi=600)
    plt.show()
