#!/usr/bin/env python3
"""v241_nan_probe.py -- do any v2.4.1 runs still emit temp:null for non-finite input?

The v2.4.1 errata makes non-finite values record-level invalid (must be rejected,
never normalised to null). Under v2.4.0, 4/25 runs emitted a null-temp row.
"""
import json, os, subprocess, sys, tempfile

W = os.path.dirname(os.path.abspath(__file__))
LEVELS = ["low", "medium", "high", "xhigh", "max"]
REPS = [int(x) for x in sys.argv[1:]] or [1, 2, 3, 4, 5]
ROWS = [{"device_id": "a", "timestamp": "2026-08-01T00:00:00Z", "temp": "nan"},
        {"device_id": "b", "timestamp": "2026-08-01T00:00:00Z", "temp": "inf"},
        {"device_id": "c", "timestamp": "2026-08-01T00:00:00Z", "temp": "-Infinity"}]

affected = 0
runs = 0
for rep in REPS:
    for lv in LEVELS:
        repo = os.path.join(W, "runs_v241_r%d" % rep, lv)
        if not os.path.isdir(repo):
            continue
        runs += 1
        with tempfile.TemporaryDirectory() as td:
            src, out = os.path.join(td, "in.ndjson"), os.path.join(td, "out.ndjson")
            with open(src, "w") as f:
                for r in ROWS:
                    f.write(json.dumps(r) + "\n")
            code = ("import json,sys;sys.path.insert(0,%r);from datapipe import transform as t;"
                    "print(json.dumps(t.transform(%r,%r)))" % (repo, src, out))
            p = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
            try:
                kept, skipped = json.loads(p.stdout.strip())
            except Exception:
                print("r%d/%-7s ERROR %s" % (rep, lv, p.stderr.strip().splitlines()[-1:]))
                continue
            body = open(out).read() if os.path.exists(out) else ""
            emitted = len([l for l in body.splitlines() if l.strip()])
            nulls = body.count('"temp": null')
            flag = ""
            if kept > 0 or emitted > 0:
                affected += 1
                flag = "  <-- AFFECTED"
            print("r%d/%-7s kept=%d skipped=%d emitted_rows=%d null_temp_rows=%d%s" % (
                rep, lv, kept, skipped, emitted, nulls, flag))
print()
print("runs emitting a non-finite-derived row: %d/%d" % (affected, runs))
print("(v2.4.0 baseline: 4/25 runs)")
