#!/usr/bin/env bash
# prep_v241_rep.sh <rep> -- byte-identical v2.4.1 candidate workspaces (68-test suite)
set -euo pipefail
REP="$1"
W="<harness>"
BENCH="$W/bench"
OUT="$W/runs_v241_r$REP"
LEVELS="low medium high xhigh max"

rm -rf "$OUT"
mkdir -p "$OUT"
for lv in $LEVELS; do cp -a "$BENCH/v5seed" "$OUT/$lv"; done

ref=$(cd "$BENCH/v5seed" && find . -type f -not -path '*__pycache__*' -print0 | sort -z | xargs -0 md5sum | md5sum)
echo "seed  $ref"
for lv in $LEVELS; do
  cur=$(cd "$OUT/$lv" && find . -type f -not -path '*__pycache__*' -print0 | sort -z | xargs -0 md5sum | md5sum)
  [ "$cur" = "$ref" ] && echo "$lv  OK" || { echo "$lv  MISMATCH"; exit 1; }
  cmp "$OUT/$lv/ONBOARDING_TODO.md" "$BENCH/spec/ONBOARDING_TODO_v2.4.md" \
    || { echo "$lv task book != frozen spec"; exit 1; }
done
if grep -rlE 'dsv4-behavior-bench|v5ref|grade_v5|behavior_manifest|v5minseed|v6' "$OUT" 2>/dev/null; then
  echo "BLINDING VIOLATION"; exit 1
fi
echo "rep$REP ready (blinding clean)"
