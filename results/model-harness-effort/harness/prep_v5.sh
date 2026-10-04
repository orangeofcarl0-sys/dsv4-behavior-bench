#!/usr/bin/env bash
# prep_v5.sh -- build 5 byte-identical V5 candidate workspaces from the frozen seed
# (cp -a, never git clone: autocrlf would rewrite line endings)
set -euo pipefail
W="<harness>"
BENCH="$W/bench"
OUT="$W/runs_v5"
LEVELS="low medium high xhigh max"

rm -rf "$OUT"
mkdir -p "$OUT"
for lv in $LEVELS; do
  cp -a "$BENCH/v5seed" "$OUT/$lv"
done

echo "--- tree md5 per workspace (must all match the seed) ---"
ref=$(cd "$BENCH/v5seed" && find . -type f -not -path '*__pycache__*' -print0 | sort -z | xargs -0 md5sum | md5sum)
echo "seed  $ref"
for lv in $LEVELS; do
  cur=$(cd "$OUT/$lv" && find . -type f -not -path '*__pycache__*' -print0 | sort -z | xargs -0 md5sum | md5sum)
  if [ "$cur" = "$ref" ]; then
    echo "$lv  OK"
  else
    echo "$lv  MISMATCH  $cur"; exit 1
  fi
done

echo "--- task book byte-identity vs frozen spec ---"
for lv in $LEVELS; do
  cmp "$OUT/$lv/ONBOARDING_TODO.md" "$BENCH/spec/ONBOARDING_TODO_v2.4.md" \
    && echo "$lv  task book == spec/ONBOARDING_TODO_v2.4.md"
done

echo "--- blinding scan inside candidate workspaces (must print nothing) ---"
if grep -rlE 'dsv4-behavior-bench|v5ref|behavior_manifest|grade_v5|ablation-task' "$OUT" 2>/dev/null; then
  echo "BLINDING VIOLATION"; exit 1
else
  echo "(clean)"
fi
