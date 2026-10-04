#!/usr/bin/env python3
"""stats.py -- significance tests over N replicates.

1. permutation test: is there ANY effort effect on V5 raw / behaviour score?
2. Fisher exact: is the NaN/Inf silent-emission defect associated with effort=max?
usage: python3 stats.py [reps...]      (default 1 2 3 4 5)
"""
import json, os, random, statistics, sys
from math import comb

W = os.path.dirname(os.path.abspath(__file__))
LEVELS = ["low", "medium", "high", "xhigh", "max"]
REPS = [int(x) for x in sys.argv[1:]] or [1, 2, 3, 4, 5]

data = {k: {lv: [] for lv in LEVELS} for k in ("raw", "behavior")}
legacy = {lv: [] for lv in LEVELS}
for rep in REPS:
    d = os.path.join(W, "logs_v5" if rep == 1 else "logs_v5_r%d" % rep)
    for lv in LEVELS:
        p = os.path.join(d, "grade_%s.json" % lv)
        if not os.path.exists(p):
            continue
        g = json.load(open(p, encoding="utf-8"))
        data["raw"][lv].append(g["v5"]["raw"]["passed"])
        data["behavior"][lv].append(g["v5"]["behavior"]["overall"])
        legacy[lv].append(g["legacy"]["raw"]["passed"])

n = len(data["raw"][LEVELS[0]])
print("=== n=%d per level ===" % n)
for lv in LEVELS:
    r = data["raw"][lv]
    print("  %-7s raw=%-28s mean=%5.2f sd=%.2f | behavior mean=%.3f | legacy mean=%.1f" % (
        lv, "/".join(map(str, r)), statistics.fmean(r), statistics.stdev(r) if len(r) > 1 else float("nan"),
        statistics.fmean(data["behavior"][lv]), statistics.fmean(legacy[lv])))


def between_ss(groups):
    allv = [v for g in groups for v in g]
    gm = statistics.fmean(allv)
    return sum(len(g) * (statistics.fmean(g) - gm) ** 2 for g in groups)


def perm_p(groups, iters=20000, seed=7):
    obs = between_ss(groups)
    flat = [(v, i) for i, g in enumerate(groups) for v in g]
    rng = random.Random(seed)
    ge = 0
    for _ in range(iters):
        rng.shuffle(flat)
        if between_ss([[v for v, gi in flat if gi == i] for i in range(len(groups))]) >= obs:
            ge += 1
    return obs, (ge + 1) / (iters + 1)


print()
print("=== permutation test: any effort effect? (20k permutations) ===")
for metric in ("raw", "behavior"):
    groups = [data[metric][lv] for lv in LEVELS]
    obs, p = perm_p(groups)
    spread = max(statistics.fmean(g) for g in groups) - min(statistics.fmean(g) for g in groups)
    pooled = statistics.stdev([v for g in groups for v in g])
    print("  %-8s between-SS=%.4f  mean spread=%.3f  pooled within sd=%.2f  p=%.3f" % (
        metric, obs, spread, pooled, p))

print()
print("=== Fisher exact: NaN/Inf silent emission vs effort=max ===")
import subprocess, tempfile, json as _json
affected = {lv: 0 for lv in LEVELS}
total = {lv: 0 for lv in LEVELS}
ROWS = [{"device_id": "a", "timestamp": "2026-08-01T00:00:00Z", "temp": "nan"},
        {"device_id": "b", "timestamp": "2026-08-01T00:00:00Z", "temp": "inf"}]
for rep in REPS:
    for lv in LEVELS:
        repo = os.path.join(W, "runs_v5" if rep == 1 else "runs_v5_r%d" % rep, lv)
        if not os.path.isdir(repo):
            continue
        total[lv] += 1
        with tempfile.TemporaryDirectory() as td:
            src, out = os.path.join(td, "in.ndjson"), os.path.join(td, "out.ndjson")
            with open(src, "w") as f:
                for row in ROWS:
                    f.write(_json.dumps(row) + "\n")
            code = ("import json,sys;sys.path.insert(0,%r);from datapipe import transform as t;"
                    "print(json.dumps(t.transform(%r,%r)))" % (repo, src, out))
            pr = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
            res = pr.stdout.strip()
            try:
                kept, skipped = _json.loads(res)
            except Exception:
                continue
            if kept > 0:
                affected[lv] += 1
print("  affected runs per level:", {lv: "%d/%d" % (affected[lv], total[lv]) for lv in LEVELS})
a, tmax = affected["max"], total["max"]
c, toth = sum(affected[lv] for lv in LEVELS if lv != "max"), sum(total[lv] for lv in LEVELS if lv != "max")
b, d = tmax - a, toth - c
N = a + b + c + d


def hyper(x, y, z, w):
    return comb(x + y, x) * comb(z + w, z) / comb(N, x + z)


obs = hyper(a, b, c, d)
r1, c1 = a + c, b + d
p_two = sum(hyper(x, r1 - x, a + c - x, d - (r1 - x)) for x in range(0, min(r1, c1) + 1)
            if hyper(x, r1 - x, a + c - x, d - (r1 - x)) <= obs + 1e-12)
print("  max: %d/%d affected; other levels: %d/%d" % (a, tmax, c, toth))
print("  two-sided Fisher exact p = %.4f  -> %s" % (p_two, "SIGNIFICANT" if p_two < 0.05 else "NOT significant"))
