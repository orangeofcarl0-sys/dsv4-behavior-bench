#!/usr/bin/env python3
"""count_flaky.py -- how often each V5 test failed across all replicates."""
import collections, json, os, sys

W = os.path.dirname(os.path.abspath(__file__))
LEVELS = ["low", "medium", "high", "xhigh", "max"]
REPS = [int(x) for x in sys.argv[1:]] or [1, 2, 3, 4, 5]

cnt = collections.Counter()
by_level = collections.defaultdict(collections.Counter)
runs_total = 0
legacy = collections.defaultdict(list)
clean_runs = 0

for rep in REPS:
    d = os.path.join(W, "logs_v5" if rep == 1 else "logs_v5_r%d" % rep)
    for lv in LEVELS:
        p = os.path.join(d, "grade_%s.json" % lv)
        if not os.path.exists(p):
            continue
        runs_total += 1
        g = json.load(open(p, encoding="utf-8"))
        fs = [x.split("::")[-1] for ts in g["v5"]["suites"].values() for x in ts.get("failed_tests", [])]
        if not fs:
            clean_runs += 1
        for f in fs:
            cnt[f] += 1
            by_level[lv][f] += 1
        legacy[lv].append(g["legacy"]["raw"]["passed"])

print("V5 runs analysed: %d (5 levels x %d replicates)" % (runs_total, len(REPS)))
print("runs with a clean 66/66: %d/%d (%.0f%%)" % (clean_runs, runs_total, 100.0 * clean_runs / runs_total))
print("")
print("failing test frequency across all runs:")
for f, n in cnt.most_common():
    per_level = "  ".join("%s=%d" % (lv, by_level[lv][f]) for lv in LEVELS if by_level[lv][f])
    print("  %-45s %2d/%d   [%s]" % (f, n, runs_total, per_level))
print("")
print("legacy /81 per level:", {lv: legacy[lv] for lv in LEVELS})
