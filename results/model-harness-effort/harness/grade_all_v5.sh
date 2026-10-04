#!/usr/bin/env bash
# grade_all_v5.sh -- host-side V5 scoring, sequential (avoids pytest cache races in bench/)
set -uo pipefail
W="<harness>"
LEVELS="low medium high xhigh max"
mkdir -p "$W/logs_v5"
for lv in $LEVELS; do
  echo "=== grading $lv ==="
  ( cd "$W/bench" && python3 grade_v5.py "$W/runs_v5/$lv" \
      --label "space-bunny-free-effort-$lv" --json "$W/logs_v5/grade_$lv.json" \
      > /dev/null 2> "$W/logs_v5/grade_$lv.err" )
  echo "  rc=$?"
done
