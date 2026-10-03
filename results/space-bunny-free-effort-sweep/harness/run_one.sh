#!/usr/bin/env bash
# run_one.sh <effort-level> -- one isolated one-shot dsh headless run
set -uo pipefail
W="<harness>"
LV="$1"
TASK=$(cat "$W/TASK_PROMPT.txt")
mkdir -p "$W/logs"
cd "$W/runs/$LV" || exit 9
date +%s > "$W/logs/$LV.start"
dsh --profile ef-dev --patch "$W/effort_$LV.yml" headless --json "$TASK" > "$W/logs/$LV.ndjson" 2> "$W/logs/$LV.err"
rc=$?
date +%s > "$W/logs/$LV.end"
echo "$rc" > "$W/logs/$LV.rc"
