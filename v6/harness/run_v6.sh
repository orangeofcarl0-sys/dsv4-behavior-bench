#!/usr/bin/env bash
# run_v6.sh -- one-shot headless runs on a V6 task with a fixed work budget.
#   usage: run_v6.sh TASK WORKSPACES_DIR LOGS_DIR MAX_TOOL_CALLS [levels...]
#
# The budget is enforced by a watchdog: when a run's ndjson log shows more than
# MAX_TOOL_CALLS tool_call events, the run is killed. This bounds the work
# budget without relying on wall-clock (which provider latency would pollute).
set -uo pipefail
TASK="${1:?task}"; W="${2:?workspaces}"; LOG="${3:?logs}"; MAX="${4:?max tool calls}"; shift 4
LEVELS=("$@")
DSH="$HOME/AppData/Roaming/npm/node_modules/@deepseek-ai/dsh/lib/bin.js"
HARNESS="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "$LOG"
task="$(cat "$HARNESS/TASK_PROMPT_v6.txt")"
echo "task=$TASK prompt=${#task} chars budget=$MAX tool calls"

for lv in "${LEVELS[@]}"; do
  wd="$W/$lv"; [ -d "$wd" ] || { echo "MISSING $wd"; continue; }
  (
    cd "$wd"
    node "$DSH" --profile ef-dev --patch "$HARNESS/effort_${lv%%_*}.yml" \
      headless --json "$task" > "$LOG/$lv.ndjson" 2> "$LOG/$lv.err"
    echo "$?" > "$LOG/$lv.rc"
  ) &
  pid=$!
  # Watchdog: kill once the tool-call count exceeds the budget.
  (
    while kill -0 "$pid" 2>/dev/null; do
      n=$(grep -c '"type":"tool_call"' "$LOG/$lv.ndjson" 2>/dev/null | head -1)
      n=${n:-0}
      if [ "$n" -gt "$MAX" ] 2>/dev/null; then
        echo "BUDGET_EXCEEDED" > "$LOG/$lv.budget"
        kill "$pid" 2>/dev/null
        break
      fi
      sleep 3
    done
  ) &
  echo "launched $lv pid=$pid"
done
wait
echo "ALL RUNS FINISHED"
for lv in "${LEVELS[@]}"; do
  rc=$(cat "$LOG/$lv.rc" 2>/dev/null || echo '?')
  n=$(grep -c '"type":"tool_call"' "$LOG/$lv.ndjson" 2>/dev/null || echo 0)
  b=$(cat "$LOG/$lv.budget" 2>/dev/null || echo ok)
  echo "$lv rc=$rc tool_calls=$n budget=$b"
done
