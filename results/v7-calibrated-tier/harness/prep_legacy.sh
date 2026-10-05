#!/usr/bin/env bash
# prep_legacy.sh <candidate> <rep> -- restore the old V1-V4 task conditions.
#
# Byte-identical copy of the historical datapipe v2.2.1 broken seed
# (<seed-root>/datapipe @ 61eff68) plus the v2.3 task book as ONBOARDING_TODO.md.
# cp -a, never git clone: autocrlf would rewrite the mixed CRLF/LF seed.
set -euo pipefail
CAND="$1"; REP="$2"
W="<harness>"
SEED="<seed-root>/datapipe"
BOOK="<seed-root>/ONBOARDING_TODO.md"
OUT="$W/legacy_runs/$CAND/r$REP"

rm -rf "$OUT"
mkdir -p "$(dirname "$OUT")"
cp -a "$SEED" "$OUT"
rm -rf "$OUT/.git"
cp "$BOOK" "$OUT/ONBOARDING_TODO.md"

# the workspace must contain nothing from the grading suite
if grep -rlE 'dsv4-behavior-bench|ablation-eval|test_v4|test_d1[0-2]|gold2?' "$OUT" 2>/dev/null | grep -v '__pycache__' | head -1; then
  echo "BLINDING VIOLATION in $OUT"; exit 1
fi
echo "prepared $CAND r$REP"
