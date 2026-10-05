#!/usr/bin/env python3
"""build_probe_pool.py -- Phase 3 probe pool with provenance and Phase-2 evidence.

Design rules applied (from the brief):
  * provenance is recorded, but provenance is NOT a promise that the candidate can
    Ctrl-F the answer in a visible doc (brief 9);
  * every probe carries its Phase-2 verdict (live / noise / floor / ceiling) so that
    spec gaps are visible as such and are not promoted into the main score (brief 11);
  * no new feature surface is invented - probes come from behaviours that already
    showed signal, plus closure probes of the same high-level contracts (brief 13).
"""
import json, os

W = os.path.dirname(os.path.abspath(__file__))

# Phase-2 labels measured on 18 runs over 6 model families.
ITEM_VERDICT = json.load(open(os.path.join(W, "legacy_item_analysis.json"), encoding="utf-8"))
BMAP = json.load(open(os.path.join(W, "legacy_behavior_map.json"), encoding="utf-8"))

ITEM_LABEL = {i["item"]: i["label"] for i in ITEM_VERDICT["items"]}
ITEM_P = {i["item"]: i["pass_rate"] for i in ITEM_VERDICT["items"]}
ITEM_D = {i["item"]: i["discrimination"] for i in ITEM_VERDICT["items"]}


def behaviour_stats(tests):
    labs = [ITEM_LABEL.get(t, "ceiling") for t in tests]
    ps = [ITEM_P[t] for t in tests if t in ITEM_P]
    ds = [ITEM_D[t] for t in tests if t in ITEM_D]
    if not ps:
        return {"verdict": "ceiling", "mean_pass_rate": None, "mean_D": None, "labels": {}}
    counts = {}
    for l in labs:
        counts[l] = counts.get(l, 0) + 1
    mean_p = sum(ps) / len(ps)
    # verdict from the measured pass rate first: a behaviour everyone fails is a
    # floor spec-gap, not a ceiling, and the label counts alone can mislead when a
    # behaviour mixes floor/noise/high-value items.
    if mean_p <= 0.10:
        v = "floor-spec-gap"
    elif mean_p >= 0.95:
        v = "ceiling"
    elif counts.get("high-value"):
        v = "live"
    else:
        v = "noise"
    return {"verdict": v, "mean_pass_rate": sum(ps) / len(ps),
            "mean_D": (sum(ds) / len(ds)) if ds else None, "labels": counts}


def main():
    probes = []
    for bid, b in BMAP["behaviors"].items():
        st = behaviour_stats(b["tests"])
        probes.append({
            "probe_id": bid,
            "kind": "legacy-behaviour",
            "source": "calibrated-legacy",
            "description": b["description"],
            "legacy_tests": b["tests"],
            "n_legacy_tests": b["n_tests"],
            "phase2": st,
            "candidate_visible_basis": [
                "the v2.3 task book section that names the behaviour",
                "standard pipeline semantics (parse -> normalize -> validate -> dedupe -> filter -> unit -> emit)",
            ],
            "rationale": (
                "Kept because the legacy suite measured it; its Phase-2 verdict decides "
                "whether it belongs in the main score or the regression suite."
            ),
        })

    # behavioural families observed in this session's own traces, not yet covered
    extra = [
        ("stop_decision_depth", "cross-run-invariant",
         "The agent decides when the work is done; runs must not differ by an order of magnitude in effort for the same outcome",
         "measured, not specified - the task book does not mention a budget",
         "kimi-k2.6 used 516/57/77 steps across three identical runs; the tail is a failure mode",
         "candidate_visible_basis: none by design - this is an observe-only metric, never scored into V7"),
        ("order_sensitivity_of_mutation", "cross-module-invariant",
         "transform must not depend on dict iteration order or on the order rows arrive within one key",
         "closure of 'dedupe keeps last' + 'filter is per-record'",
         "legacy measured ordering only via one hard-coded scenario; a general probe is a stronger closure",
         "candidate_visible_basis: the frozen processing order line in the task book"),
        ("emit_ingest_roundtrip_law", "robustness-closure",
         "emit(csv) -> ingest must be a value-preserving round trip for every row emit can produce",
         "closure of the csv quoting rule and the ingest normalisation rule",
         "one legacy test covers a single happy row; the law covers all rows emit can emit",
         "candidate_visible_basis: csv quoting bullet + ingest normalization bullet"),
        ("skipped_accounting_invariant", "cross-module-invariant",
         "kept + skipped = input record count, for every path (malformed, out-of-range, duplicate, filtered)",
         "closure of 'skip and count' appearing in three separate spec bullets",
         "legacy has one test for this (a12); the invariant is stronger and cheap to check",
         "candidate_visible_basis: the three 'skip and count' bullets"),
    ]
    for pid, src, desc, basis, why, note in extra:
        probes.append({
            "probe_id": pid,
            "kind": "closure-probe" if pid != "stop_decision_depth" else "observe-only",
            "source": src,
            "description": desc,
            "legacy_tests": [],
            "n_legacy_tests": 0,
            "phase2": {"verdict": "unmeasured", "mean_pass_rate": None, "mean_D": None, "labels": {}},
            "candidate_visible_basis": [basis],
            "rationale": why,
            "note": note,
        })

    pool = {
        "generated_from": ["legacy_behavior_map.json", "legacy_item_analysis.json"],
        "n_probes": len(probes),
        "verdict_counts": {},
        "probes": probes,
    }
    c = {}
    for p in probes:
        v = p["phase2"]["verdict"]
        c[v] = c.get(v, 0) + 1
    pool["verdict_counts"] = c
    json.dump(pool, open(os.path.join(W, "probe_pool.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)

    print("probe pool: %d entries" % len(probes))
    print("verdicts:", c)
    print()
    print("%-36s %-14s %6s %8s %8s" % ("probe", "kind", "tests", "p", "D"))
    for p in sorted(probes, key=lambda x: (x["phase2"]["verdict"], -(x["phase2"]["mean_D"] or 0))):
        ph = p["phase2"]
        print("%-36s %-14s %6d %8s %8s  %s" % (
            p["probe_id"][:36], p["kind"], p["n_legacy_tests"],
            ("%.2f" % ph["mean_pass_rate"]) if ph["mean_pass_rate"] is not None else "-",
            ("%.2f" % ph["mean_D"]) if ph["mean_D"] is not None else "-",
            ph["verdict"]))
    print()
    print("wrote probe_pool.json")


if __name__ == "__main__":
    main()
