#!/usr/bin/env bash
# grade_v241_rep.sh <rep> -- host-side grading against the v2.4.1 / 68-test suite
set -uo pipefail
REP="$1"
W="<harness>"
LEVELS="low medium high xhigh max"
LOG="$W/logs_v241_r$REP"
mkdir -p "$LOG"
for lv in $LEVELS; do
  echo "=== v241 rep$REP grading $lv ==="
  ( cd "$W/bench" && python3 grade_v5.py "$W/runs_v241_r$REP/$lv" \
      --label "space-bunny-free-v241-effort-$lv-r$REP" --json "$LOG/grade_$lv.json" \
      > /dev/null 2> "$LOG/grade_$lv.err" )
  echo "  rc=$?"
done
