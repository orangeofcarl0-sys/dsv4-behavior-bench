#!/usr/bin/env bash
# run_v5min.sh -- launch N concurrent one-shot headless runs on V5-Minimal.
#   usage: run_v5min.sh WORKSPACES_DIR LOGS_DIR [levels...]
# Each level directory holds a byte-identical candidate workspace.
set -uo pipefail
W="${1:?workspaces dir}"; LOG="${2:?logs dir}"; shift 2
LEVELS=("$@")
DSH="$HOME/AppData/Roaming/npm/node_modules/@deepseek-ai/dsh/lib/bin.js"
NODE="node"
mkdir -p "$LOG"
HARNESS="$(cd "$(dirname "$0")" && pwd)"

task="$(cat "$HARNESS/TASK_PROMPT_min.txt")"
echo "task prompt: ${#task} chars"

pids=()
for lv in "${LEVELS[@]}"; do
  wd="$W/$lv"
  [ -d "$wd" ] || { echo "MISSING $wd"; continue; }
  t0=$(date +%s)
  echo "$t0" > "$LOG/$lv.start"
  (
    cd "$wd"
    "$NODE" "$DSH" --profile ef-dev --patch "$HARNESS/effort_${lv%%_*}.yml" \
      headless --json "$task" > "$LOG/$lv.ndjson" 2> "$LOG/$lv.err"
    echo "$?" > "$LOG/$lv.rc"
    echo "$(date +%s)" > "$LOG/$lv.end"
  ) &
  pids+=($!)
  echo "launched $lv pid=${pids[-1]}"
done

for p in "${pids[@]}"; do wait "$p"; done
echo "ALL RUNS FINISHED"
for lv in "${LEVELS[@]}"; do
  rc=$(cat "$LOG/$lv.rc" 2>/dev/null || echo '?')
  s=$(cat "$LOG/$lv.start" 2>/dev/null || echo 0); e=$(cat "$LOG/$lv.end" 2>/dev/null || echo 0)
  echo "$lv rc=$rc wall=$((e-s))s ndjson=$(wc -c < "$LOG/$lv.ndjson" 2>/dev/null || echo 0)B"
done
