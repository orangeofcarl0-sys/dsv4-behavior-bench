#!/usr/bin/env python3
"""finalize_v7.py -- apply the pilot verdicts to the manifest.

The pilot is the first measurement under the correct task book, so it decides.
Ceiling behaviours are demoted to regression regardless of how they were chosen;
noise behaviours stay scored but flagged, because they still separate some models
while carrying high run variance.
"""
import json, os, shutil

W = os.path.dirname(os.path.abspath(__file__))
P = os.path.join(W, "bench", "v7", "behavior_manifest.json")
shutil.copy(P, P + ".pre-pilot")
m = json.load(open(P, encoding="utf-8"))

PILOT = {
    "whitespace_trimming":              {"p": 0.67, "vb": 0.333, "vr": 0.000, "verdict": "live"},
    "timestamp_microseconds_preserved": {"p": 0.50, "vb": 0.250, "vr": 0.167, "verdict": "live"},
    "bool_is_not_numeric":              {"p": 0.50, "vb": 0.250, "vr": 0.167, "verdict": "live"},
    "legacy_temperature_fallback":      {"p": 0.33, "vb": 0.083, "vr": 0.333, "verdict": "noise"},
    "nonfinite_rejected":               {"p": 0.50, "vb": 0.000, "vr": 0.500, "verdict": "noise"},
    "cli_exit_codes":                   {"p": 1.00, "vb": 0.000, "vr": 0.000, "verdict": "ceiling"},
    "csv_dialect_robustness":           {"p": 1.00, "vb": 0.000, "vr": 0.000, "verdict": "ceiling"},
    "cli_full_chain":                   {"p": 1.00, "vb": 0.000, "vr": 0.000, "verdict": "ceiling"},
    "filter_unit_order":                {"p": 1.00, "vb": 0.000, "vr": 0.000, "verdict": "ceiling"},
    "md_table_escaping":                {"p": 1.00, "vb": 0.000, "vr": 0.000, "verdict": "ceiling"},
}

for b in m["behaviours"]:
    v = PILOT[b["id"]]
    b["pilot"] = v
    b["phase2"]["v7_measured"] = {
        "pass_rate": v["p"], "var_between": v["vb"], "var_run": v["vr"], "verdict": v["verdict"],
        "n_runs": 6,
    }
    if v["verdict"] == "ceiling":
        b["tier"] = "regression"
        b["scored"] = False
    else:
        b["scored"] = True
        if v["verdict"] == "noise":
            b["note"] = (b.get("note", "") + " | pilot: scored but high run-to-run variance").strip(" |")

m["revision"] = "v7-r2 (post-pilot)"
m["weights"] = {"basic": 1, "inference": 2, "hard": 3, "regression": 0}
m["scored_behaviours"] = [b["id"] for b in m["behaviours"] if b.get("scored")]
m["regression_behaviours"] = [b["id"] for b in m["behaviours"] if not b.get("scored")]
m["pilot_summary"] = {
    "runs": 6, "candidates": 3,
    "key_finding": ("the three behaviours whose rule was unpublished went from p=0.06 "
                    "(floor, zero between-model variance) to p=1.00 (ceiling) once the rule "
                    "was stated -- they measured guessing, not difficulty, in both states"),
    "live": [b["id"] for b in m["behaviours"] if b.get("pilot", {}).get("verdict") == "live"],
    "noise": [b["id"] for b in m["behaviours"] if b.get("pilot", {}).get("verdict") == "noise"],
    "ceiling": [b["id"] for b in m["behaviours"] if b.get("pilot", {}).get("verdict") == "ceiling"],
}
json.dump(m, open(P, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

print("scored (%d): %s" % (len(m["scored_behaviours"]), m["scored_behaviours"]))
print("regression (%d): %s" % (len(m["regression_behaviours"]), m["regression_behaviours"]))
print()
print("verdicts:", {k: len(v) for k, v in
                    (("live", m["pilot_summary"]["live"]),
                     ("noise", m["pilot_summary"]["noise"]),
                     ("ceiling", m["pilot_summary"]["ceiling"]))})
