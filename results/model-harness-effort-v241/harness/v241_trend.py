#!/usr/bin/env python3
"""v241_trend.py -- is the score monotone in effort? (trend test, not level-difference test)

Two views:
  a) Spearman rho over all 25 runs (effort rank vs V5 raw), exact permutation p
  b) level means vs rank -- perfectly monotone by construction of 5 points
  c) how big the trend is next to the noise: per-level sd and the step sizes
"""
import json, os, random, statistics
from itertools import permutations

W = os.path.dirname(os.path.abspath(__file__))
LEVELS = ["low", "medium", "high", "xhigh", "max"]
S = json.load(open(os.path.join(W, "logs_v241_summary_n5.json"), encoding="utf-8"))
raw = S["levels"]

xs, ys = [], []
for i, lv in enumerate(LEVELS, start=1):
    for v in raw[lv]["raw"]:
        xs.append(i)
        ys.append(v)


def rankdata(a):
    order = sorted(range(len(a)), key=lambda k: a[k])
    r = [0.0] * len(a)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and a[order[j + 1]] == a[order[i]]:
            j += 1
        avg = (i + j) / 2.0 + 1
        for k in range(i, j + 1):
            r[order[k]] = avg
        i = j + 1
    return r


def pearson(a, b):
    ma, mb = statistics.fmean(a), statistics.fmean(b)
    num = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    da = sum((x - ma) ** 2 for x in a) ** 0.5
    db = sum((y - mb) ** 2 for y in b) ** 0.5
    return num / (da * db) if da and db else float("nan")


rx, ry = rankdata(xs), rankdata(ys)
rho = pearson(rx, ry)
print("a) Spearman rho over all 25 runs (effort rank vs V5 raw): %.4f" % rho)

# exact permutation test on ranks
flat = list(ry)
rng = random.Random(23)
ge = 0
ITERS = 20000
for _ in range(ITERS):
    rng.shuffle(flat)
    if abs(pearson(rx, flat)) >= abs(rho) - 1e-12:
        ge += 1
print("   permutation p (two-sided, 20k): %.4f" % ((ge + 1) / (ITERS + 1)))

print()
print("b) level means vs effort rank:")
means = [statistics.fmean(raw[lv]["raw"]) for lv in LEVELS]
for lv, m in zip(LEVELS, means):
    print("   %-7s mean=%6.2f sd=%.2f" % (lv, m, statistics.stdev(raw[lv]["raw"])))
print("   monotone increasing: %s" % all(means[i] < means[i + 1] for i in range(len(means) - 1)))

print()
print("c) effect size next to noise:")
print("   max - low = %.2f points" % (means[-1] - means[0]))
print("   pooled within-level sd = %.2f" % statistics.stdev([v for lv in LEVELS for v in raw[lv]["raw"]]))
print("   perfect 68/68 runs: low %d/%d, max %d/%d" % (
    sum(1 for v in raw["low"]["raw"] if v == 68), len(raw["low"]["raw"]),
    sum(1 for v in raw["max"]["raw"] if v == 68), len(raw["max"]["raw"])))
print("   behavior: low %.3f -> max %.3f" % (
    statistics.fmean(raw["low"]["behavior"]), statistics.fmean(raw["max"]["behavior"])))
