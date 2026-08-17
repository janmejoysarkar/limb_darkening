The SUIT data is in this format-
```
SUT_T25_0589_000866_Lev2.0_2025-04-18T07.13.23.926_0971NB06.fits  SUT_T25_0589_000866_Lev2.0_2025-04-18T14.21.20.836_0971NB06.fits  SUT_T25_0589_000866_Lev2.0_2025-04-18T21.29.38.800_0971NB06.fits
SUT_T25_0589_000866_Lev2.0_2025-04-18T09.36.02.245_0971NB06.fits  SUT_T25_0589_000866_Lev2.0_2025-04-18T16.43.58.707_0971NB06.fits
SUT_T25_0589_000866_Lev2.0_2025-04-18T11.58.42.996_0971NB06.fits  SUT_T25_0589_000866_Lev2.0_2025-04-18T19.06.43.746_0971NB06.fits
```
Notice the date and time mentioned in the filename.

The HMI data is present as such-
```
hmi.m_45s.20250319_033515_TAI.2.magnetogram.fits
hmi.m_45s.20250319_033600_TAI.2.magnetogram.fits
hmi.m_45s.20250319_033645_TAI.2.magnetogram.fits
hmi.m_45s.20250319_033730_TAI.2.magnetogram.fits
hmi.m_45s.20250319_033815_TAI.2.magnetogram.fits
hmi.m_45s.20250319_033900_TAI.2.magnetogram.fits
hmi.m_45s.20250319_033945_TAI.2.magnetogram.fits
hmi.m_45s.20250319_055915_TAI.2.magnetogram.fits
hmi.m_45s.20250319_060000_TAI.2.magnetogram.fits
hmi.m_45s.20250319_060045_TAI.2.magnetogram.fits
```
Notice the date and time present in this data too.

I want a function that will find the file closest in time to each individual SUIT image.
Give an alert whenever the time gap between the SUIT and HMI images are more than 1 hour.
