#!/usr/bin/env python3
"""v241_analyze.py -- aggregate space-bunny-free on V5 v2.4.1 (68 tests) over n replicates."""
import collections, json, os, random, statistics, sys

W = os.path.dirname(os.path.abspath(__file__))
LEVELS = ["low", "medium", "high", "xhigh", "max"]
REPS = [int(x) for x in sys.argv[1:]] or [1, 2, 3, 4, 5]
DEN = 68

raw, beh, legacy = {lv: [] for lv in LEVELS}, {lv: [] for lv in LEVELS}, {lv: [] for lv in LEVELS}
calls, think, steps = {lv: [] for lv in LEVELS}, {lv: [] for lv in LEVELS}, {lv: [] for lv in LEVELS}
fails = collections.Counter()
fails_by_level = collections.defaultdict(collections.Counter)
clean = total = 0
a13a14 = 0

for rep in REPS:
    d = os.path.join(W, "logs_v241_r%d" % rep)
    for lv in LEVELS:
        p = os.path.join(d, "grade_%s.json" % lv)
        if not os.path.exists(p):
            continue
        g = json.load(open(p, encoding="utf-8"))
        total += 1
        raw[lv].append(g["v5"]["raw"]["passed"])
        beh[lv].append(g["v5"]["behavior"]["overall"])
        legacy[lv].append(g["legacy"]["raw"]["passed"])
        fs = [x.split("::")[-1] for ts in g["v5"]["suites"].values() for x in ts.get("failed_tests", [])]
        if not fs:
            clean += 1
        for f in fs:
            fails[f] += 1
            fails_by_level[lv][f] += 1
            if f.startswith("test_a13") or f.startswith("test_a14"):
                a13a14 += 1
        nd = os.path.join(d, lv + ".ndjson")
        c = collections.Counter()
        if os.path.exists(nd):
            for ln in open(nd, encoding="utf-8"):
                ln = ln.strip()
                if not ln:
                    continue
                try:
                    o = json.loads(ln)
                except Exception:
                    continue
                t = o.get("type")
                if t == "tool_call":
                    c["calls"] += 1
                elif t == "thinking":
                    c["think"] += 1
                elif t == "status" and o.get("phase") == "step_start":
                    c["steps"] += 1
        calls[lv].append(c["calls"]); think[lv].append(c["think"]); steps[lv].append(c["steps"])

print("=== space-bunny-free x V5 v2.4.1 (%d tests), n=%d ===" % (DEN, len(REPS)))
print("%-7s %-31s %-16s %-9s %-8s %s" % ("effort", "V5 raw per run", "mean +/- sd", "behavior", "legacy", "calls per run"))
for lv in LEVELS:
    sd = statistics.stdev(raw[lv]) if len(raw[lv]) > 1 else float("nan")
    print("%-7s %-31s %6.2f +/- %-4.2f %-9.3f %-8.1f %s" % (
        lv, "/".join(map(str, raw[lv])), statistics.fmean(raw[lv]), sd,
        statistics.fmean(beh[lv]), statistics.fmean(legacy[lv]), "/".join(map(str, calls[lv]))))
print()
print("clean 68/68: %d/%d (%.0f%%)" % (clean, total, 100.0 * clean / total))
print("new v2.4.1 tests a13/a14 failed in: %d/%d runs" % (a13a14, total))
print("failing test frequency:")
for f, n in fails.most_common():
    per = "  ".join("%s=%d" % (lv, fails_by_level[lv][f]) for lv in LEVELS if fails_by_level[lv][f])
    print("  %-46s %2d/%d  [%s]" % (f, n, total, per))
print()
print("process metrics (mean per level):")
for lv in LEVELS:
    print("  %-7s steps=%.0f  thinking=%.0f  calls=%.0f" % (
        lv, statistics.fmean(steps[lv]), statistics.fmean(think[lv]), statistics.fmean(calls[lv])))

print()
print("=== permutation test: any effort effect? (20k) ===")
def between_ss(groups):
    allv = [v for g in groups for v in g]
    gm = statistics.fmean(allv)
    return sum(len(g) * (statistics.fmean(g) - gm) ** 2 for g in groups)

def perm_p(groups, iters=20000, seed=13):
    obs = between_ss(groups)
    flat = [(v, i) for i, g in enumerate(groups) for v in g]
    rng = random.Random(seed)
    ge = 0
    for _ in range(iters):
        rng.shuffle(flat)
        if between_ss([[v for v, gi in flat if gi == i] for i in range(len(groups))]) >= obs:
            ge += 1
    return obs, (ge + 1) / (iters + 1)

for name, series in (("raw", raw), ("behavior", beh)):
    groups = [series[lv] for lv in LEVELS]
    obs, p = perm_p(groups)
    spread = max(statistics.fmean(g) for g in groups) - min(statistics.fmean(g) for g in groups)
    pooled = statistics.stdev([v for g in groups for v in g])
    print("  %-8s between-SS=%.4f spread=%.3f pooled-sd=%.2f p=%.3f" % (name, obs, spread, pooled, p))

out = {"levels": {lv: {"raw": raw[lv], "behavior": beh[lv], "legacy": legacy[lv],
                        "calls": calls[lv], "steps": steps[lv], "thinking": think[lv]} for lv in LEVELS},
       "fails": dict(fails), "clean": clean, "total": total}
json.dump(out, open(os.path.join(W, "logs_v241_summary_n%d.json" % len(REPS)), "w", encoding="utf-8"),
          ensure_ascii=False, indent=2)
print("\nwrote logs_v241_summary_n%d.json" % len(REPS))
