#!/usr/bin/env bash
# prep_v5min.sh -- build byte-identical V5-Minimal candidate workspaces.
#
# Control guarantee: the *code* under datapipe/ (plus tests/, tools/,
# sample_data/) is byte-identical to v5seed, which is what the full-spec V5 runs
# used. Only the candidate-visible information differs (task book + evidence).
set -euo pipefail
BENCH="$(cd "$(dirname "$0")/../../.." && pwd)"
OUT="${1:?usage: prep_v5min.sh OUTDIR}"
LEVELS="${LEVELS:-low medium high}"

rm -rf "$OUT"; mkdir -p "$OUT"
for lv in $LEVELS; do
  cp -a "$BENCH/v5minseed" "$OUT/$lv"
  find "$OUT/$lv" -name '__pycache__' -type d -prune -exec rm -rf {} + 2>/dev/null || true
  find "$OUT/$lv" -name '.pytest_cache' -type d -prune -exec rm -rf {} + 2>/dev/null || true
done

echo "--- datapipe/ code byte-identity vs v5seed (must be identical) ---"
for lv in $LEVELS; do
  if diff -r -x '__pycache__' -x '.pytest_cache' "$BENCH/v5seed/datapipe" "$OUT/$lv/datapipe" >/dev/null; then
    echo "$lv  code IDENTICAL to v5seed"
  else
    echo "$lv  CODE DIFFERS FROM SEED"; exit 1
  fi
done

echo "--- tests/ tools/ sample_data byte-identity vs v5seed ---"
for lv in $LEVELS; do
  diff -r -x '__pycache__' -x '.pytest_cache' "$BENCH/v5seed/tests" "$OUT/$lv/tests" >/dev/null \
    && diff -r -x '__pycache__' "$BENCH/v5seed/tools" "$OUT/$lv/tools" >/dev/null \
    && diff -r "$BENCH/v5seed/sample_data" "$OUT/$lv/sample_data" >/dev/null \
    && echo "$lv  OK" || { echo "$lv  MISMATCH"; exit 1; }
done

echo "--- evidence layer present ---"
for lv in $LEVELS; do
  for f in ONBOARDING_TODO.md README.md CHANGELOG.md docs/architecture.md \
           docs/error-policy.md docs/data-model.md docs/filters.md docs/emit.md \
           docs/api.md examples/README.md; do
    [ -f "$OUT/$lv/$f" ] || { echo "$lv  MISSING $f"; exit 1; }
  done
  echo "$lv  evidence OK"
done

echo "--- blinding scan (must print nothing) ---"
if grep -rlE 'dsv4-behavior-bench|v5ref|v5seed|behavior_manifest|grade_v5|v5minseed' "$OUT" 2>/dev/null; then
  echo "BLINDING VIOLATION"; exit 1
else
  echo "(clean)"
fi
