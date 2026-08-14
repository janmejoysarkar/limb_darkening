import numpy as np
import matplotlib.pyplot as plt
from scipy.ndimage import binary_dilation
import sunpy.map
from reproject import reproject_interp

def get_suit_magnetic_mask(suit_file, hmi_file, threshold_G=10.0, min_mu=0.1, max_mu=0.95, dilate_arcsec=1.0):
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

    # Compute |B| / mu (masking out region outside valid mu bounds)
    with np.errstate(divide='ignore', invalid='ignore'):
        b_radial = np.abs(hmi_map.data) / mu
        # Mask out limb region where mu < min_mu OR mu > max_mu
        b_radial[(mu < min_mu) | (mu > max_mu)] = 0

    # Reproject HMI radial magnetic field to SUIT grid
    b_radial_map = sunpy.map.Map(b_radial, hmi_map.meta)
    reprojected_b, _ = reproject_interp(b_radial_map, suit_map.wcs)

    # Generate base binary mask
    mask = (reprojected_b > threshold_G)

    # Dilate mask by requested arcseconds
    if dilate_arcsec > 0:
        pix_scale = suit_map.meta['CDELT1']# arcsec / pixel
        radius_pix = max(1, int(round(dilate_arcsec / pix_scale)))
        
        # Disk-shaped structuring element
        y, x = np.ogrid[-radius_pix:radius_pix+1, -radius_pix:radius_pix+1]
        struct_elem = x**2 + y**2 <= radius_pix**2
        
        mask = binary_dilation(mask, structure=struct_elem)

    mask = mask.astype(np.uint8)
    suit_masked_data = np.where(mask == 0, suit_map.data, 0)

    return mask, suit_masked_data, suit_map


def plot_suit_magnetic_mask(suit_map, suit_masked, mask):
    """
    Plots SUIT map, masked data, and mask contour overlay sharing X and Y axes.
    """
    fig = plt.figure(figsize=(18, 6))

    # Panel 1: Original SUIT Map
    ax1 = fig.add_subplot(131, projection=suit_map)
    suit_map.plot(axes=ax1, title="SUIT Level-2 Map")

    # Panel 2: Masked SUIT Data
    ax2 = fig.add_subplot(132, projection=suit_map, sharex=ax1, sharey=ax1)
    suit_map.plot(axes=ax2, title="Masked SUIT (|B|/μ > 10G)")
    ax2.imshow(suit_masked, origin='lower', cmap=suit_map.cmap, norm=suit_map.plot_settings['norm'])

    # Panel 3: Mask Contour Overlay
    ax3 = fig.add_subplot(133, projection=suit_map, sharex=ax1, sharey=ax1)
    suit_map.plot(axes=ax3, title="Mask Contour Overlay")
    ax3.contour(mask, levels=[0.5], colors='red', linewidths=1.0)

    plt.tight_layout()
    plt.show()


# Example Usage:
suit_file = "/run/media/sarkar/Elements/SUIT/sftp_drive/suit_data/level2fits/2025/04/19/normal_4k/SUT_T25_0589_000869_Lev2.0_2025-04-19T20.13.47.875_0971NB06.fits"
hmi_file = "/run/media/sarkar/Elements/HMI/blos/hmi.m_45s.20250419_201330_TAI.2.magnetogram.fits"

# Get mask with max_mu limit set (e.g. max_mu=0.90 to cut off near limb)
mask, suit_masked, suit_map = get_suit_magnetic_mask(
    suit_file, 
    hmi_file, 
    threshold_G=50.0, 
    min_mu=0, 
    max_mu=1,  # Limits maximum mu threshold
    dilate_arcsec=1.5
)

# Render side-by-side visualization
plot_suit_magnetic_mask(suit_map, suit_masked, mask)
