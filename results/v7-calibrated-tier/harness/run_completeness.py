#!/usr/bin/env python3
"""run_completeness.py -- did each Phase-2 run finish its turn normally?"""
import collections, json, os, sys

W = os.path.dirname(os.path.abspath(__file__))
base = os.path.join(W, "legacy_logs")
for cand in sorted(os.listdir(base)):
    d = os.path.join(base, cand)
    if not os.path.isdir(d) or cand.startswith("_"):
        continue
    for rep in (1, 2, 3):
        nd = os.path.join(d, "r%d.ndjson" % rep)
        rc_p = os.path.join(d, "r%d.rc" % rep)
        if not os.path.exists(nd):
            continue
        c = collections.Counter()
        for ln in open(nd, encoding="utf-8", errors="replace"):
            ln = ln.strip()
            if not ln:
                continue
            try:
                c[json.loads(ln).get("type")] += 1
            except Exception:
                pass
        rc = open(rc_p).read().strip() if os.path.exists(rc_p) else "?"
        print("%-22s r%d rc=%-20s final=%d steps=%-3d calls=%-3d size=%-7d %s" % (
            cand, rep, rc, c.get("final", 0), c.get("status", 0) // 2,
            c.get("tool_call", 0), os.path.getsize(nd),
            "COMPLETE" if c.get("final", 0) else "** INCOMPLETE **"))
