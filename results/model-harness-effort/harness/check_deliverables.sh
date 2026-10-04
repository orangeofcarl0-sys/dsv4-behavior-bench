#!/usr/bin/env bash
# check_deliverables.sh -- did each candidate fulfil the task-book deliverable?
# Task book 13.4: write diagnosis / changes / verification / risks into
# datapipe/PULL_REQUEST_TEMPLATE.md (the seed also ships a root-level copy).
W="<harness>"
SEED_PRT_MD5=$(md5sum "$W/bench/v5seed/PULL_REQUEST_TEMPLATE.md" | cut -d' ' -f1)
echo "seed root PULL_REQUEST_TEMPLATE.md md5: $SEED_PRT_MD5 (unmodified template)"
echo ""
for rep in 1 2 3; do
  case "$rep" in
    1) ROOT="$W/runs_v5"; L="$W/logs_v5";;
    *) ROOT="$W/runs_v5_r$rep"; L="$W/logs_v5_r$rep";;
  esac
  for lv in low medium high xhigh max; do
    inner="$ROOT/$lv/datapipe/PULL_REQUEST_TEMPLATE.md"
    root_p="$ROOT/$lv/PULL_REQUEST_TEMPLATE.md"
    inner_ok="no"; root_changed="no"
    [ -f "$inner" ] && inner_ok="yes"
    if [ -f "$root_p" ]; then
      m=$(md5sum "$root_p" | cut -d' ' -f1)
      [ "$m" != "$SEED_PRT_MD5" ] && root_changed="yes"
    fi
    score=$(python3 -c "
import json,sys
try:
    d=json.load(open('$L/grade_$lv.json'))
    print(d['v5']['raw']['passed'])
except Exception:
    print('?')
")
    printf 'rep%d/%-7s raw=%-3s datapipe/PULL_REQUEST_TEMPLATE.md=%-4s root-template-modified=%s\n' \
      "$rep" "$lv" "$score" "$inner_ok" "$root_changed"
  done
done
