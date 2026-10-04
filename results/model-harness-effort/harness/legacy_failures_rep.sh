#!/usr/bin/env bash
# legacy_failures_rep.sh <rep> <levels...>
W="<harness>"
REP="$1"; shift
for lv in "$@"; do
  echo "===== rep$REP $lv ====="
  DATAPIPE_REPO="$W/runs_v5_r$REP/$lv" PYTHONPATH="$W/runs_v5_r$REP/$lv" \
    python3 -m pytest d10 d11 d12 t2 t3 t4 v4 -q --tb=no -p no:cacheprovider -rf 2>&1 \
    | grep -E '^FAILED|passed|failed' | tail -6
done
