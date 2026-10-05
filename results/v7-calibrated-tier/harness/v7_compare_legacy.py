#!/usr/bin/env python3
"""v7_compare_legacy.py -- does the 10-behaviour V7 tier discriminate as well as
the 81-test legacy suite, on the SAME 18 artifacts?"""
import json, os, statistics

W = os.path.dirname(os.path.abspath(__file__))
pop = json.load(open(os.path.join(W, "v7_population.json"), encoding="utf-8"))

rows = []
for cand, reps in pop.items():
    for rep, d in reps.items():
        rows.append({"cand": cand, "rep": int(rep), "v7": d["v7_score"] * 100,
                     "legacy": d["legacy"], "beh": d["behaviours"]})

def report(metric, label):
    by = {}
    for r in rows:
        by.setdefault(r["cand"], []).append(r[metric])
    means = {c: statistics.fmean(v) for c, v in by.items()}
    within = [statistics.stdev(v) for v in by.values() if len(v) > 1]
    spread = max(means.values()) - min(means.values())
    overall_sd = statistics.stdev([r[metric] for r in rows])
    print("=== %s ===" % label)
    print("  between-model spread : %.1f" % spread)
    print("  mean within-model sd : %.1f" % statistics.fmean(within))
    print("  between/within ratio : %.2f" % (spread / statistics.fmean(within) if statistics.fmean(within) else float("nan")))
    print("  distribution sd      : %.1f" % overall_sd)
    for c, m in sorted(means.items(), key=lambda kv: -kv[1]):
        print("    %-22s %6.1f   (runs: %s)" % (c, m, "/".join("%.0f" % x for x in by[c])))
    print()
    return means

mv7 = report("v7", "V7 (10 behaviours, weighted, /100)")
mlg = report("legacy", "legacy (81 tests, raw)")

print("=== head-to-head ===")
print("  rank correlation between the two metrics:", end=" ")
a = sorted(mv7, key=lambda c: -mv7[c])
b = sorted(mlg, key=lambda c: -mlg[c])
inv = sum(1 for i in range(len(a)) for j in range(i + 1, len(a)) if b.index(a[i]) > b.index(a[j]))
pairs = len(a) * (len(a) - 1) / 2
print("%.2f (concordant %d/%d pairs)" % (1 - inv / pairs, int(pairs - inv), int(pairs)))

# per-run agreement of the two metrics
xs = [r["v7"] for r in rows]
ys = [r["legacy"] for r in rows]
mx, my = statistics.fmean(xs), statistics.fmean(ys)
num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
den = (sum((x - mx) ** 2 for x in xs) ** 0.5) * (sum((y - my) ** 2 for y in ys) ** 0.5)
print("  per-run Pearson r(V7, legacy) = %.3f over %d runs" % (num / den, len(rows)))

# which V7 behaviours separate the population
print()
print("=== per-behaviour separation (V7) ===")
allb = sorted({k for r in rows for k in []} or set().union(*[set() for _ in rows]))
