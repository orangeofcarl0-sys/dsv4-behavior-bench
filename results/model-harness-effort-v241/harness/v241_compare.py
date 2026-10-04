#!/usr/bin/env python3
"""v241_compare.py -- per-level v2.4.0 vs v2.4.1 comparison."""
import json, os, statistics

W = os.path.dirname(os.path.abspath(__file__))
old = json.load(open(os.path.join(W, "logs_v5", "summary_n5.json"), encoding="utf-8"))["levels"]
new = json.load(open(os.path.join(W, "logs_v241_summary_n5.json"), encoding="utf-8"))["levels"]
L = ["low", "medium", "high", "xhigh", "max"]

print("%-7s | %-22s | %-22s | %-13s | %-13s" % (
    "effort", "v2.4.0 /66 mean(sd)", "v2.4.1 /68 mean(sd)", "perfect 66/66", "perfect 68/68"))
for lv in L:
    o = [r["grade"]["raw"] for r in old[lv]["runs"]]
    n = new[lv]["raw"]
    op = sum(1 for v in o if v == 66)
    npf = sum(1 for v in n if v == 68)
    print("%-7s | %6.2f (%.2f) %-10s | %6.2f (%.2f) %-10s | %-13s | %-13s" % (
        lv, statistics.fmean(o), statistics.stdev(o), "", statistics.fmean(n),
        statistics.stdev(n), "", "%d/5" % op, "%d/5" % npf))
print()
print("%-7s | %-22s | %-22s" % ("effort", "v2.4.0 behavior", "v2.4.1 behavior"))
for lv in L:
    ob = [r["grade"]["behavior"] for r in old[lv]["runs"]]
    nb = new[lv]["behavior"]
    print("%-7s | %6.3f %-15s | %6.3f" % (lv, statistics.fmean(ob), "", statistics.fmean(nb)))
print()
print("%-7s | %-14s | %-14s" % ("effort", "legacy 240", "legacy 241"))
for lv in L:
    ol = [r["grade"]["legacy"] for r in old[lv]["runs"]]
    nl = new[lv]["legacy"]
    print("%-7s | %6.1f %-7s | %6.1f" % (lv, statistics.fmean(ol), "", statistics.fmean(nl)))
