#!/usr/bin/env bash
# check_logmeta.sh -- every run must have consistent start < end, rc file present, non-empty ndjson
W="<harness>"
bad=0
for rep in 1 2 3 4 5; do
  case "$rep" in
    1) L="$W/logs_v5";;
    *) L="$W/logs_v5_r$rep";;
  esac
  for lv in low medium high xhigh max; do
    s=$(cat "$L/$lv.start" 2>/dev/null || echo "")
    e=$(cat "$L/$lv.end"   2>/dev/null || echo "")
    rc=$(cat "$L/$lv.rc"   2>/dev/null || echo "")
    sz=$(stat -c %s "$L/$lv.ndjson" 2>/dev/null || echo 0)
    flag=""
    [ -z "$s" ] && flag="$flag no_start"
    [ -z "$e" ] && flag="$flag no_end"
    [ -z "$rc" ] && flag="$flag no_rc"
    [ -n "$s" ] && [ -n "$e" ] && [ "$e" -le "$s" ] && flag="$flag end<=start"
    [ "$rc" != "0" ] && flag="$flag rc=$rc"
    [ "$sz" -lt 1000 ] && flag="$flag tiny_ndjson"
    if [ -n "$flag" ]; then echo "rep$rep/$lv:$flag (s=$s e=$e rc=$rc size=$sz)"; bad=$((bad+1)); fi
  done
done
echo "metadata problems: $bad / 25"
