import os, glob

# Global variables
FTR_NAME= 'NB06'
proj_path= os.path.abspath('..')

class arMask:
# --- AR_MASKING ---
    FTR_NAME= FTR_NAME
    proj_path=proj_path
    data_path= "/run/media/sarkar/Elements/SUIT/pradan1.issdc.gov.in/al1/protected/downloadData/suit/level1/2025/*/*/"
    hmi_filepath= "/run/media/sarkar/Elements/HMI/blos/*"
    savedir= os.path.join(proj_path, "data/interim")
    threshold_G = 75.0
    min_mu=0.3
    max_mu=1  # Limits maximum mu threshold
    dilate_arcsec=7
    max_workers=8
    OVERWRITE=False
    SAVE=True

class mkCalib:
# --- RUN_MAKE_CALIB ---
    SAVE_CALIB= True
    OVERWRITE= False
    n=1 # Bracket of +- n days
    data_path= os.path.join(proj_path, f'data/interim/')
    flat_path= os.path.join(proj_path, f'data/external/{FTR_NAME}_fft_flat.fits')
    savepath= os.path.join(proj_path, 'data/processed/')

class aplCorr:
# --- RUN_APPLY_CORR ---
    max_workers=12
    OVERWRITE= False
    LD_CORR= True
    data_path= "/run/media/sarkar/Elements/SUIT/pradan1.issdc.gov.in/al1/protected/downloadData/suit/level1/2025/*/*/"
    calib_path= os.path.join(proj_path, f'data/processed/')
    flat_path= os.path.join(proj_path, f'data/external/{FTR_NAME}_fft_flat.fits')
    save_path= os.path.join(proj_path, 'products')

