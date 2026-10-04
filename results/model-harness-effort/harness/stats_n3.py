#!/usr/bin/env python3
"""stats_n3.py -- do the n=3 replicates show any effort effect at all?

1. permutation test on the between-group variance of V5 raw / behaviour score
2. Fisher exact test for the NaN/Inf silent-emission vs effort=max association
"""
import itertools, json, os, random, statistics

W = os.path.dirname(os.path.abspath(__file__))
LEVELS = ["low", "medium", "high", "xhigh", "max"]
REPS = [1, 2, 3]

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


def between_ss(groups):
    allv = [v for g in groups for v in g]
    gm = statistics.fmean(allv)
    return sum(len(g) * (statistics.fmean(g) - gm) ** 2 for g in groups)


def permutation_p(groups, iters=20000, seed=7):
    obs = between_ss(groups)
    flat = [(v, i) for i, g in enumerate(groups) for v in g]
    rng = random.Random(seed)
    ge = 0
    for _ in range(iters):
        rng.shuffle(flat)
        perm = [[v for v, gi in flat if gi == i] for i in range(len(groups))]
        if between_ss(perm) >= obs:
            ge += 1
    return obs, (ge + 1) / (iters + 1)


print("=== per-level scores (n=3) ===")
for lv in LEVELS:
    print("  %-7s raw=%s mean=%.2f sd=%s | behavior mean=%.3f | legacy mean=%.1f" % (
        lv, data["raw"][lv], statistics.fmean(data["raw"][lv]),
        ("%.2f" % statistics.stdev(data["raw"][lv])) if len(data["raw"][lv]) > 1 else "n/a",
        statistics.fmean(data["behavior"][lv]), statistics.fmean(legacy[lv])))

print()
print("=== permutation test: any effort effect? (20k label permutations) ===")
for metric in ("raw", "behavior"):
    groups = [data[metric][lv] for lv in LEVELS]
    obs, p = permutation_p(groups)
    spread = max(statistics.fmean(g) for g in groups) - min(statistics.fmean(g) for g in groups)
    print("  %-8s between-group SS=%.4f  mean spread=%.3f  p=%.3f" % (metric, obs, spread, p))

print()
print("=== Fisher exact: NaN/Inf silent emission vs effort=max ===")
# observed across the 15 runs: max 2/3 affected, every other level 1/12
a, b, c, d = 2, 1, 1, 11      # max affected/unaffected, others affected/unaffected
n = a + b + c + d


def hyper(a_, b_, c_, d_):
    from math import comb
    return comb(a_ + b_, a_) * comb(c_ + d_, c_) / comb(n, a_ + c_)


obs_p = hyper(a, b, c, d)
tot = 0.0
r1, c1 = a + c, b + d
for x in range(0, min(r1, c1) + 1):
    pp = hyper(x, r1 - x, a + c - x, d - (r1 - x))
    if pp <= obs_p + 1e-12:
        tot += pp
print("  max: 2/3 runs emitted null-temp rows; other 4 levels: 1/12")
print("  two-sided Fisher exact p = %.4f" % tot)
print("  (0.05 threshold: %s)" % ("SIGNIFICANT" if tot < 0.05 else "NOT significant"))
