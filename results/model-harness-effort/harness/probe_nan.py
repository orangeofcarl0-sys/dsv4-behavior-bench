#!/usr/bin/env python3
"""probe_nan.py -- what does each candidate actually do with temp="nan" / "inf"?"""
import json, os, subprocess, sys, tempfile

W = os.path.dirname(os.path.abspath(__file__))
CASES = {"low": None, "medium": None, "high": None, "xhigh": None, "max": None}

rows = [{"device_id": "a", "timestamp": "2026-08-01T00:00:00Z", "temp": "nan"},
        {"device_id": "b", "timestamp": "2026-08-01T00:00:00Z", "temp": "inf"}]

for lv in CASES:
    repo = os.path.join(W, "runs_v5", lv)
    with tempfile.TemporaryDirectory() as td:
        src = os.path.join(td, "in.ndjson")
        out = os.path.join(td, "out.ndjson")
        with open(src, "w") as f:
            for r in rows:
                f.write(json.dumps(r) + "\n")
        code = (
            "import json,sys;sys.path.insert(0,%r);"
            "from datapipe import transform as t;"
            "print(json.dumps(t.transform(%r,%r)))" % (repo, src, out)
        )
        p = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
        res = p.stdout.strip() or p.stderr.strip().splitlines()[-1:] 
        body = ""
        if os.path.exists(out):
            body = open(out).read().strip()
        print("%-7s kept/skipped=%s" % (lv, res))
        print("         output=%s" % (body if body else "(no output file)"))
