#!/usr/bin/env bash
# run_v7_pilot.sh -- first V7 pilot: 3 candidates x 2 reps, strictly serial
# (the shared upstream account caps concurrency at 3 sessions).
set -uo pipefail
W="<harness>"
PS="F:\\<workspace-root>\\estest\\space-bunny\\behavebenchmark\\run_v7.ps1"
for c in deepseek-v4.1-flash hy4-preview-f minimax-m3; do
  for r in 1 2; do
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$PS" -Model "$c" -Rep "$r" 2>&1 | tail -1
    sleep 10
  done
done
echo "V7 PILOT FINISHED"
