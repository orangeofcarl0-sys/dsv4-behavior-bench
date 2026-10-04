#!/usr/bin/env bash
# grade_all_v5_rep.sh <rep> -- host-side V5 scoring for one replicate (sequential)
set -uo pipefail
REP="$1"
W="<harness>"
LEVELS="low medium high xhigh max"
LOG="$W/logs_v5_r$REP"
mkdir -p "$LOG"
for lv in $LEVELS; do
  echo "=== rep$REP grading $lv ==="
  ( cd "$W/bench" && python3 grade_v5.py "$W/runs_v5_r$REP/$lv" \
      --label "space-bunny-free-effort-$lv-r$REP" --json "$LOG/grade_$lv.json" \
      > /dev/null 2> "$LOG/grade_$lv.err" )
  echo "  rc=$?"
done
