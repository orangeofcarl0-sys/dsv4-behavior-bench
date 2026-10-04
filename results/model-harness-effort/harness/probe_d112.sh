#!/usr/bin/env bash
W="<harness>"
for lv in max xhigh high; do
  echo "===== $lv d112 ====="
  DATAPIPE_REPO="$W/runs_v5/$lv" PYTHONPATH="$W/runs_v5/$lv" \
    python3 -m pytest d11/test_d11.py::test_d112_nan_temp_rejected -q --tb=line -p no:cacheprovider 2>&1 | tail -4
done
