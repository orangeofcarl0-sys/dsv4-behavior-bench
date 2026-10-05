#!/usr/bin/env bash
# prep_v7.sh <candidate> <rep> -- V7 task conditions: legacy seed + V7 task book.
set -euo pipefail
CAND="$1"; REP="$2"
W="<harness>"
SEED="<seed-root>/datapipe"
BOOK="$W/bench/v7/ONBOARDING_TODO.md"
OUT="$W/v7_runs/$CAND/r$REP"

rm -rf "$OUT"
mkdir -p "$(dirname "$OUT")"
cp -a "$SEED" "$OUT"
rm -rf "$OUT/.git"
cp "$BOOK" "$OUT/ONBOARDING_TODO.md"

if grep -rlE 'dsv4-behavior-bench|ablation-eval|test_v7|test_d1[0-2]|gold2?' "$OUT" 2>/dev/null | grep -v '__pycache__' | head -1; then
  echo "BLINDING VIOLATION in $OUT"; exit 1
fi
echo "prepared v7 $CAND r$REP"
