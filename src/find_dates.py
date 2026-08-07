import glob
from datetime import datetime
import os
from pathlib import Path
from datetime import datetime, timedelta

def files(target_date, n):
    before = [d for d in available_dates if d < target_date]
    after = [d for d in available_dates if d > target_date]
    selected_dates = []
    if target_date in available_dates:
        selected_dates.append(target_date)
    selected_dates += before[-n:]
    selected_dates += after[:n]
    selected_dates = sorted(selected_dates)
    files = []
    for d in selected_dates:
        folder = BASE / f"{d.year:04d}" / f"{d.month:02d}" / f"{d.day:02d}" / 'normal_4k'
        files.extend(sorted(folder.glob(f"*{FTR_NAME}*.fits")))
    return files

BASE=Path('/run/media/sarkar/Elements/SUIT/sftp_drive/suit_data/level2fits/')
FTR_NAME='NB06'
TARGET_DATE= datetime.strptime("2025-04-02", "%Y-%m-%d").date()
INTVL=1
available_dates = sorted(
    datetime.strptime(f"{y.name}/{m.name}/{d.name}", "%Y/%m/%d").date()
    for y in BASE.iterdir() if y.is_dir()
    for m in y.iterdir() if m.is_dir()
    for d in m.iterdir() if d.is_dir()
    )
filelist= files(TARGET_DATE, INTVL)
