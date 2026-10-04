#!/usr/bin/env bash
# prep_v6.sh -- build candidate workspaces for one V6 task.
#   usage: prep_v6.sh TASK OUTDIR [levels...]
# Each level dir is a copy of v6/<TASK>/seed plus the task's ISSUE.md as the
# visible prompt; hidden/ and ref/ are never copied.
set -euo pipefail
BENCH="$(cd "$(dirname "$0")/../.." && pwd)"
TASK="${1:?task}"; OUT="${2:?outdir}"; shift 2
LEVELS=("$@")

rm -rf "$OUT"; mkdir -p "$OUT"
for lv in "${LEVELS[@]}"; do
  cp -a "$BENCH/v6/$TASK/seed" "$OUT/$lv"
  rm -rf "$OUT/$lv/tests/public/__pycache__" "$OUT/$lv/cfgmerge/__pycache__" \
         "$OUT/$lv/framecodec/__pycache__" "$OUT/$lv/ledger/__pycache__" 2>/dev/null || true
done

echo "--- blinding scan (must print nothing) ---"
if grep -rlE 'dsv4-behavior-bench|CANDIDATE_REPO|behavior_manifest|grade_v6|v6/' "$OUT" 2>/dev/null; then
  echo "BLINDING VIOLATION"; exit 1
else
  echo "(clean)"
fi
