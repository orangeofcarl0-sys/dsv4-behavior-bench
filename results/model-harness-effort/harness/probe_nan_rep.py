#!/usr/bin/env python3
"""probe_nan_rep.py -- NaN/Inf handling for every candidate of every replicate.

usage: python3 probe_nan_rep.py [rep ...]      (rep 1 -> runs_v5/, rep N -> runs_v5_rN/)
"""
import json, os, subprocess, sys, tempfile

W = os.path.dirname(os.path.abspath(__file__))
LEVELS = ["low", "medium", "high", "xhigh", "max"]
ROWS = [{"device_id": "a", "timestamp": "2026-08-01T00:00:00Z", "temp": "nan"},
        {"device_id": "b", "timestamp": "2026-08-01T00:00:00Z", "temp": "inf"}]


def ws(rep, lv):
    return os.path.join(W, "runs_v5" if rep == 1 else "runs_v5_r%d" % rep, lv)


def main():
    reps = [int(x) for x in sys.argv[1:]] or [1, 2, 3]
    print("replicate/level -> transform() result on temp=\"nan\" and temp=\"inf\"")
    for rep in reps:
        for lv in LEVELS:
            repo = ws(rep, lv)
            if not os.path.isdir(repo):
                continue
            with tempfile.TemporaryDirectory() as td:
                src, out = os.path.join(td, "in.ndjson"), os.path.join(td, "out.ndjson")
                with open(src, "w") as f:
                    for r in ROWS:
                        f.write(json.dumps(r) + "\n")
                code = ("import json,sys;sys.path.insert(0,%r);"
                        "from datapipe import transform as t;"
                        "print(json.dumps(t.transform(%r,%r)))" % (repo, src, out))
                p = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
                res = p.stdout.strip() or (p.stderr.strip().splitlines() or ["?"])[-1]
                body = open(out).read().strip() if os.path.exists(out) else ""
                kept_null = body.count('"temp": null')
                print("rep%d %-7s kept/skipped=%-10s emitted_rows=%d rows_with_null_temp=%d" % (
                    rep, lv, res.replace('"', ""), len(body.splitlines()) if body else 0, kept_null))


if __name__ == "__main__":
    main()
