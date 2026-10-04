#!/usr/bin/env bash
# prep_v5_rep.sh <rep> -- build 5 byte-identical candidate workspaces for replicate <rep>
set -euo pipefail
REP="$1"
W="<harness>"
BENCH="$W/bench"
OUT="$W/runs_v5_r$REP"
LEVELS="low medium high xhigh max"

rm -rf "$OUT"
mkdir -p "$OUT"
for lv in $LEVELS; do
  cp -a "$BENCH/v5seed" "$OUT/$lv"
done

echo "--- rep$REP tree md5 (must match the seed and each other) ---"
ref=$(cd "$BENCH/v5seed" && find . -type f -not -path '*__pycache__*' -print0 | sort -z | xargs -0 md5sum | md5sum)
echo "seed  $ref"
for lv in $LEVELS; do
  cur=$(cd "$OUT/$lv" && find . -type f -not -path '*__pycache__*' -print0 | sort -z | xargs -0 md5sum | md5sum)
  if [ "$cur" = "$ref" ]; then echo "$lv  OK"; else echo "$lv  MISMATCH $cur"; exit 1; fi
  cmp "$OUT/$lv/ONBOARDING_TODO.md" "$BENCH/spec/ONBOARDING_TODO_v2.4.md" \
    || { echo "$lv task book differs from frozen spec"; exit 1; }
done
echo "rep$REP ready: all 5 workspaces byte-identical to the frozen seed"
