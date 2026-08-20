import sunpy.map
from sunpy.coordinates import propagate_with_solar_surface
from sunpy.physics.differential_rotation import differential_rotate
from reproject import reproject_interp
import matplotlib.pyplot as plt

suit_file= '/run/media/sarkar/Elements/SUIT/sftp_drive/suit_data/level2fits/2025/04/02/normal_4k/SUT_T25_0588_000821_Lev2.0_2025-04-02T18.45.41.957_0971NB01.fits'
hmi_file='/run/media/sarkar/Elements/HMI/blos/hmi.m_45s.20250402_161245_TAI.2.magnetogram.fits'
suit_map= sunpy.map.Map(suit_file)
hmi_map = sunpy.map.Map(hmi_file)

'''
with propagate_with_solar_surface():
    aligned_hmi_data, _ = reproject_interp(
        hmi_map,
        suit_map.wcs,
        shape_out=suit_map.data.shape
    )
'''    

hmi_map = sunpy.map.Map(hmi_file)
    
# 1. Differentially rotate HMI map to SUIT observation time
hmi_rotated = differential_rotate(hmi_map, time=suit_map.date)

# 2. Reproject rotated HMI map to SUIT pixel grid
aligned_hmi_data, _ = reproject_interp(hmi_rotated,suit_map.wcs)
hmi_suit, _= reproject_interp(hmi_map, suit_map.wcs)

plt.figure()
plt.subplot(1,2,1)
plt.imshow(suit_map.data, origin='lower')
plt.imshow(hmi_suit, origin='lower', alpha=0.5, cmap='gray')

plt.subplot(1,2,2)
plt.imshow(suit_map.data, origin='lower')
plt.imshow(aligned_hmi_data, origin='lower', alpha=0.5, cmap='gray')
plt.show()

