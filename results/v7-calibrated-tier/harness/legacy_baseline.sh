#!/usr/bin/env bash
# legacy_baseline.sh -- reproduce the documented legacy baselines
B="<harness>/bench"
REF="<harness>/ref_aa2d0a8"
SEED="<seed-root>/datapipe"
cd "$B" || exit 9
run() {
  label="$1"; repo="$2"
  out=$(DATAPIPE_REPO="$repo" PYTHONPATH="$repo" python3 -m pytest d10 d11 d12 t2 t3 t4 v4 -q --tb=no -p no:cacheprovider 2>&1)
  line=$(echo "$out" | grep -E 'passed|failed' | tail -1)
  echo "$label: $line"
}
run "seed  (expect 25/81)" "$SEED"
run "gold2 (expect 81/81)" "$REF/gold2"
run "gold  (expect 76/81)" "$REF/gold"
