#!/usr/bin/env python3
"""v7_pilot_analysis.py -- verdicts from the fresh V7 pilot (6 runs, 3 families).

This is the first measurement taken under the CORRECT task book (the two spec
gaps published), so it supersedes every earlier V7 number for those behaviours.
"""
import collections, json, os, statistics

W = os.path.dirname(os.path.abspath(__file__))
CANDS = ["deepseek-v4.1-flash", "hy4-preview-f", "minimax-m3"]
man = json.load(open(os.path.join(W, "bench", "v7", "behavior_manifest.json"), encoding="utf-8"))
IDS = [b["id"] for b in man["behaviours"]]
TIER = {b["id"]: b["tier"] for b in man["behaviours"]}

data = {}
for c in CANDS:
    for r in (1, 2):
        p = os.path.join(W, "v7_logs", c, "grade_r%d.json" % r)
        if os.path.exists(p):
            data[(c, r)] = json.load(open(p, encoding="utf-8"))

print("runs: %d" % len(data))
print()
print("%-34s %-9s %6s %10s %10s  %s" % ("behaviour", "tier", "p", "var_betw", "var_run", "per-run"))
rows = []
for bid in IDS:
    per = collections.defaultdict(list)
    for (c, r), d in data.items():
        per[c].append(0 if bid in [k for k, v in d["behaviours"].items() if not v["satisfied"]] else 1)
    allv = [v for vs in per.values() for v in vs]
    p = sum(allv) / len(allv)
    means = [sum(vs) / len(vs) for vs in per.values()]
    vbet = statistics.variance(means) if len(means) > 1 else 0.0
    within = [statistics.variance(vs) for vs in per.values() if len(vs) > 1]
    vrun = statistics.fmean(within) if within else 0.0
    rows.append((bid, TIER[bid], p, vbet, vrun, {c: "".join(map(str, vs)) for c, vs in per.items()}))

for bid, tier, p, vbet, vrun, per in sorted(rows, key=lambda r: -r[3]):
    lab = "ceiling" if p >= 0.95 else ("floor" if p <= 0.10 else ("live" if vbet > vrun else "noise"))
    print("%-34s %-9s %6.2f %10.3f %10.3f  %-8s %s" % (
        bid, tier, p, vbet, vrun, lab,
        " ".join("%s:%s" % (c.split("-")[0][:6], v) for c, v in per.items())))

print()
print("=== scores ===")
for c in CANDS:
    vs = [data[(c, r)]["score"] for r in (1, 2) if (c, r) in data]
    print("  %-22s %.3f  (%s)" % (c, statistics.fmean(vs), "/".join("%.2f" % v for v in vs)))

scored = [b["id"] for b in man["behaviours"] if b.get("scored")]
print()
print("scored behaviours:", len(scored))
for b in man["behaviours"]:
    if b["id"] in ("filter_unit_order", "md_table_escaping", "cli_full_chain"):
        per = collections.defaultdict(list)
        for (c, r), d in data.items():
            unmet = [k for k, v in d["behaviours"].items() if not v["satisfied"]]
            per[c].append(0 if b["id"] in unmet else 1)
        print("  formerly-UNMEASURED %-20s now: %s" % (
            b["id"], " ".join("%s:%s" % (c.split("-")[0][:6], "".join(map(str, vs))) for c, vs in per.items())))
