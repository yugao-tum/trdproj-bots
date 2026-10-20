#!/bin/sh
# Reproduce the numbers quoted in quant-015 from the cached raw files.
set -e
python3 walkforward.py > walkforward.out 2>&1
python3 pm_histcheck.py > pm_histcheck.out 2>&1
python3 pm_count.py > pm_count.out 2>&1
python3 pm_model_market.py > pm_model_market.out 2>&1
python3 firstrelease_local.py > firstrelease_local.out 2>&1
echo 'done: walkforward.out pm_histcheck.out pm_count.out pm_model_market.out firstrelease_local.out'
