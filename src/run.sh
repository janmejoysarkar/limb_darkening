#!/bin/bash
set -e

echo "*** Initializing contamination correction ***"
echo "*** REMOVING ARs ***"
python3 remove_ar.py 
echo "*** MAKING CALIB FRAMES ***"
python3 make_calib.py 
echo "*** APPLY CORRECTION ***"
python3 apply_correction.py 
