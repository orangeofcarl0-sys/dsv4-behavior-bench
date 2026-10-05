#!/usr/bin/env python3
"""v7_flip_analysis.py -- which behaviours drive V7's within-model variance?"""
import collections, json, os

W = os.path.dirname(os.path.abspath(__file__))
pop = json.load(open(os.path.join(W, "v7_population.json"), encoding="utf-8"))

# behaviour -> per-candidate pass counts
per = collections.defaultdict(lambda: collections.defaultdict(list))
for cand, reps in pop.items():
    for rep, d in reps.items():
        allb = set(d["unmet"]) | set()
        # reconstruct satisfied set: manifest ids minus unmet
        import json as _j
        man = _j.load(open(os.path.join(W, "bench", "v7", "behavior_manifest.json"), encoding="utf-8"))
        ids = [b["id"] for b in man["behaviours"]]
        for bid in ids:
            per[bid][cand].append(0 if bid in d["unmet"] else 1)

print("%-34s %6s %8s %8s  %s" % ("behaviour", "p", "var_betw", "var_run", "per-candidate pass counts"))
rows = []
for bid, byc in per.items():
    allv = [v for vs in byc.values() for v in vs]
    p = sum(allv) / len(allv)
    means = [sum(vs) / len(vs) for vs in byc.values()]
    import statistics
    vbet = statistics.variance(means) if len(means) > 1 else 0
    within = [statistics.variance(vs) for vs in byc.values() if len(vs) > 1]
    vrun = statistics.fmean(within) if within else 0
    rows.append((bid, p, vbet, vrun, {c: "".join(map(str, vs)) for c, vs in byc.items()}))

for bid, p, vbet, vrun, counts in sorted(rows, key=lambda r: -r[2]):
    print("%-34s %6.2f %8.3f %8.3f  %s" % (bid, p, vbet, vrun,
          " ".join("%s:%s" % (c.split("-")[0][:6], v) for c, v in counts.items())))
