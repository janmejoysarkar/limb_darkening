import config as c
from remove_ar import run_ar_masking
from make_calib import run_make_calib
from apply_correction import run_apply_correction

RUN_AR_MASKING= True
RUN_MAKE_CALIB= False
RUN_APPLY_CORR= False

if RUN_AR_MASKING:
    print ("---- Active Region Masking ----")
    run_ar_masking()
'''
if RUN_MAKE_CALIB:
    print ("--- Make calibration files ---")
    run_make_calib(
        FTR_NAME,
        proj_path,
        SAVE_CALIB= True,
        OVERWRITE= False,
        n=1, # Bracket of +- n days
        data_path= os.path.join(proj_path, 'data/interim/'),
        flat_path= os.path.join(proj_path, f'data/external/{FTR_NAME}_fft_flat.fits')
        )

if RUN_APPLY_CORR:
    print('--- Apply Correction ---')
    run_apply_correction(
        FTR_NAME,
        proj_path,
        max_workers=12,
        OVERWRITE= False,
        LD_CORR= True,
        data_path= '/run/media/sarkar/Elements/SUIT/sftp_drive/suit_data/level2fits/2025/*/*/normal_4k/',
        calib_path= os.path.join(proj_path, f'data/processed/'),
        flat_path= os.path.join(proj_path, f'data/external/{FTR_NAME}_fft_flat.fits'),
        save_path= os.path.join(proj_path, 'products'),
            )
'''            
