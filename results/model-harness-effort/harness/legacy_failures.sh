#!/usr/bin/env bash
# legacy_failures.sh -- legacy 81-suite failure names (grade_v5.py records counts only)
W="<harness>"
for lv in "$@"; do
  echo "===== $lv ====="
  DATAPIPE_REPO="$W/runs_v5/$lv" PYTHONPATH="$W/runs_v5/$lv" \
    python3 -m pytest d10 d11 d12 t2 t3 t4 v4 -q --tb=no -p no:cacheprovider -rf 2>&1 \
    | grep -E '^FAILED|passed|failed' | tail -8
done
echo "===== v5ref (reference) ====="
DATAPIPE_REPO="$W/bench/v5ref" PYTHONPATH="$W/bench/v5ref" \
  python3 -m pytest d10 d11 d12 t2 t3 t4 v4 -q --tb=no -p no:cacheprovider -rf 2>&1 \
  | grep -E '^FAILED|passed|failed' | tail -8
