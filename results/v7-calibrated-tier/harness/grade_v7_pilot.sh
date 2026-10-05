#!/usr/bin/env bash
W="<harness>"
B="$W/bench"
cd "$B" || exit 9
for c in deepseek-v4.1-flash hy4-preview-f minimax-m3; do
  for r in 1 2; do
    python3 grade_v7.py "$W/v7_runs/$c/r$r" --label "$c-r$r" \
      --json "$W/v7_logs/$c/grade_r$r.json" > /dev/null 2>&1
    python3 - "$W/v7_logs/$c/grade_r$r.json" "$c" "$r" <<'PY'
import json, sys
d = json.load(open(sys.argv[1], encoding="utf-8"))
print("%-22s r%s  V7=%.3f  behaviours %d/%d  unmet: %s" % (
    sys.argv[2], sys.argv[3], d["score"], d["behaviours_satisfied"], d["behaviours_total"],
    ", ".join(k for k, v in d["behaviours"].items() if not v["satisfied"]) or "none"))
PY
  done
done
