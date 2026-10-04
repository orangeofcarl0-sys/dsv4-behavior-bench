#!/usr/bin/env python3
"""inspect_dirty.py -- show what actually matched, so the exclusion rule is evidence-based."""
import json, os, re

W = os.path.dirname(os.path.abspath(__file__))
ERR_PAT = re.compile(
    r"rate.?limit|\b429\b|overload|temporarily unavailable|ECONNRESET|EPIPE|socket hang up|"
    r"fetch failed|network error|retry|aborted|connection (closed|reset)|Timeout|timed out",
    re.I)

def log_dir(rep):
    return os.path.join(W, "logs_v5" if rep == 1 else "logs_v5_r%d" % rep)

for rep, lv in ((1, "max"), (2, "max"), (1, "medium"), (3, "xhigh")):
    p = os.path.join(log_dir(rep), lv + ".ndjson")
    print("===== rep%d/%s =====" % (rep, lv))
    shown = 0
    with open(p, encoding="utf-8", errors="replace") as fh:
        for i, ln in enumerate(fh, 1):
            m = ERR_PAT.search(ln)
            if not m:
                continue
            try:
                o = json.loads(ln)
            except Exception:
                continue
            print("  line %-6d type=%-12s match=%r" % (i, o.get("type"), m.group(0)))
            snippet = json.dumps(o, ensure_ascii=False)
            print("     ", snippet[:260].replace("\n", " "))
            shown += 1
            if shown >= 4:
                break
    print()
