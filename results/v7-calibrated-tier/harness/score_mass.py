#!/usr/bin/env python3
"""score_mass.py -- did the old suite give HARD behaviours more score mass?

For each semantic behaviour: n_tests (its count in the 81) and the observed
failure rate over the current candidate pool. Effective score mass =
n_tests x fail_rate. If the old suite "amplified hard behaviours", the
behaviours with the highest fail rates should also carry the most tests.
"""
import json, os, statistics

W = os.path.dirname(os.path.abspath(__file__))
bm = json.load(open(os.path.join(W, "legacy_behavior_map.json"), encoding="utf-8"))
ia = json.load(open(os.path.join(W, "legacy_item_analysis.json"), encoding="utf-8"))

# item -> pass rate from the analysis
pr = {i["item"]: i["pass_rate"] for i in ia["items"]}

rows = []
for bid, b in bm["behaviors"].items():
    rates = [1 - pr[t] for t in b["tests"] if t in pr]   # fail rate where observed
    if not rates:
        continue
    rows.append((bid, b["n_tests"], statistics.fmean(rates), b["n_tests"] * statistics.fmean(rates)))

rows.sort(key=lambda r: -r[3])
print("%-36s %6s %10s %12s" % ("behaviour", "tests", "fail_rate", "score_mass"))
tot_mass = sum(r[3] for r in rows)
for bid, n, fr, mass in rows:
    print("%-36s %6d %10.2f %12.2f" % (bid, n, fr, mass))
print()
print("total effective score mass: %.1f of 81 tests" % tot_mass)
hi = [r for r in rows if r[2] >= 0.5]
lo = [r for r in rows if r[2] < 0.2]
print("behaviours failing in >=50%% of runs : n=%d, mean tests each %.1f" % (
    len(hi), statistics.fmean([r[1] for r in hi]) if hi else 0))
print("behaviours failing in  <20%% of runs : n=%d, mean tests each %.1f" % (
    len(lo), statistics.fmean([r[1] for r in lo]) if lo else 0))

# correlation between test count and fail rate
ns = [r[1] for r in rows]
frs = [r[2] for r in rows]
mn, mf = statistics.fmean(ns), statistics.fmean(frs)
num = sum((a - mn) * (b - mf) for a, b in zip(ns, frs))
den = (sum((a - mn) ** 2 for a in ns) ** 0.5) * (sum((b - mf) ** 2 for b in frs) ** 0.5)
print("correlation(n_tests, fail_rate) = %.3f" % (num / den if den else float("nan")))
