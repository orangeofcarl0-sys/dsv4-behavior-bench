#!/usr/bin/env python3
"""inspect_errors.py -- enumerate every non-completed tool_result and any unknown event type."""
import collections, json, os, sys

W = os.path.dirname(os.path.abspath(__file__))
LEVELS = ["low", "medium", "high", "xhigh", "max"]
REPS = [int(x) for x in sys.argv[1:]] or [1, 2, 3, 4, 5]
KNOWN = {"session", "status", "text", "thinking", "tool_call", "tool_result"}


def log_dir(rep):
    return os.path.join(W, "logs_v5" if rep == 1 else "logs_v5_r%d" % rep)


unknown = collections.Counter()
errs = []
statuses = collections.Counter()
for rep in REPS:
    for lv in LEVELS:
        p = os.path.join(log_dir(rep), lv + ".ndjson")
        if not os.path.exists(p):
            continue
        with open(p, encoding="utf-8", errors="replace") as fh:
            for ln in fh:
                ln = ln.strip()
                if not ln:
                    continue
                try:
                    o = json.loads(ln)
                except Exception:
                    unknown["UNPARSEABLE"] += 1
                    continue
                t = o.get("type")
                if t not in KNOWN:
                    unknown["%s:%s" % (t, o.get("phase") or o.get("phase") or "")] += 1
                if t == "tool_result":
                    st = o.get("status")
                    statuses[str(st)] += 1
                    if st not in ("completed", "ok", None):
                        msg = str(o.get("result") or "")[:150].replace("\n", " ")
                        errs.append(("rep%d/%s" % (rep, lv), st, msg))

print("tool_result status counts:", dict(statuses))
print("unknown/unparseable event types:", dict(unknown) or "none")
print("")
print("non-completed tool_results: %d" % len(errs))
for run, st, msg in errs:
    print("  %-12s %-8s %s" % (run, st, msg))
