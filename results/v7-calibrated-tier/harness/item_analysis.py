#!/usr/bin/env python3
"""item_analysis.py -- per-item discrimination statistics over a candidate response matrix.

Implements the Phase-5 measures from the task spec:
  p_i            pass rate of item i over all runs
  Var_model      variance of per-model mean pass rates   (between-model signal)
  Var_run        mean within-model variance              (run-to-run noise)
  D_i            Var_model / (Var_run + eps)             (discrimination ratio)
  r_it           item-total correlation (does the item track the overall score)

Labels:
  ceiling   p > 0.95
  floor     p < 0.10
  noise     between-model means are close but run flips are large
  high-value 0.15 < p < 0.90 and Var_model >> Var_run

usage: python3 item_analysis.py [--json OUT] [--set legacy|v5]
"""
import argparse, collections, json, os, statistics, sys

W = os.path.dirname(os.path.abspath(__file__))


def load_legacy_runs():
    """returns list of dicts: {candidate, rep, passed_set, total}"""
    base = os.path.join(W, "legacy_logs")
    runs = []
    for cand in sorted(os.listdir(base)):
        d = os.path.join(base, cand)
        if not os.path.isdir(d) or cand.startswith("_"):
            continue
        for rep in (1, 2, 3):
            p = os.path.join(d, "grade_r%d.json" % rep)
            if not os.path.exists(p):
                continue
            g = json.load(open(p, encoding="utf-8"))
            # a candidate that never got going is not a data point
            if g["total_passed"] == 0:
                continue
            failed = set(x.split("::")[-1] for x in g["failures"])
            runs.append({"candidate": cand, "rep": rep, "failed": failed,
                         "score": g["total_passed"], "total": g["total"],
                         "suites": g["suites"]})
    return runs


def all_items(runs):
    items = set()
    for r in runs:
        for s in r["suites"].values():
            for t in s.get("failed_tests", []):
                items.add(t.split("::")[-1])
    return items


def analyse(runs, label):
    items = all_items(runs)
    by_cand = collections.defaultdict(list)
    for r in runs:
        by_cand[r["candidate"]].append(r)

    scores = [r["score"] for r in runs]
    mean_score = statistics.fmean(scores)
    sd_score = statistics.stdev(scores) if len(scores) > 1 else 0.0

    rows = []
    for it in sorted(items):
        per_run = [1 if it not in r["failed"] else 0 for r in runs]
        p = statistics.fmean(per_run)
        per_model = {}
        for c, rs in by_cand.items():
            per_model[c] = statistics.fmean([1 if it not in r["failed"] else 0 for r in rs])
        model_means = list(per_model.values())
        var_model = statistics.variance(model_means) if len(model_means) > 1 else 0.0
        within = []
        for c, rs in by_cand.items():
            if len(rs) > 1:
                within.append(statistics.variance([1 if it not in r["failed"] else 0 for r in rs]))
        var_run = statistics.fmean(within) if within else 0.0
        disc = var_model / (var_run + 1e-9)
        # item-total correlation: point-biserial between item and total score
        if sd_score > 0 and len(set(per_run)) > 1:
            r_it = statistics.correlation(per_run, scores) if hasattr(statistics, "correlation") else float("nan")
        else:
            r_it = float("nan")
        if p > 0.95:
            lab = "ceiling"
        elif p < 0.10:
            lab = "floor"
        elif var_model <= var_run:
            lab = "noise"
        elif 0.15 < p < 0.90:
            lab = "high-value"
        else:
            lab = "mid"
        rows.append({"item": it, "suite": label, "pass_rate": p, "n_runs": len(runs),
                     "per_model": per_model, "var_model": var_model,
                     "var_run": var_run, "discrimination": disc,
                     "item_total_r": r_it, "label": lab})

    return rows, {"n_runs": len(runs), "n_candidates": len(by_cand),
                  "mean_score": mean_score, "sd_score": sd_score,
                  "score_min": min(scores), "score_max": max(scores),
                  "per_candidate_mean": {c: statistics.fmean([r["score"] for r in rs])
                                         for c, rs in by_cand.items()}}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", default=None)
    args = ap.parse_args()

    runs = load_legacy_runs()
    if not runs:
        print("no graded runs found")
        return
    rows, meta = analyse(runs, "legacy")

    counts = collections.Counter(r["label"] for r in rows)
    print("=== legacy item analysis ===")
    print("runs=%d candidates=%d  score mean=%.1f sd=%.1f range=%d..%d" % (
        meta["n_runs"], meta["n_candidates"], meta["mean_score"], meta["sd_score"],
        meta["score_min"], meta["score_max"]))
    print()
    print("per-candidate mean legacy score:")
    for c, m in sorted(meta["per_candidate_mean"].items(), key=lambda kv: -kv[1]):
        print("  %-22s %.1f" % (c, m))
    print()
    print("labels:", dict(counts))
    print()
    print("%-52s %6s %8s %8s %8s  %s" % ("item", "p", "Varmod", "Varrun", "D", "label"))
    for r in sorted(rows, key=lambda r: -r["discrimination"]):
        print("%-52s %6.2f %8.3f %8.3f %8.2f  %s" % (
            r["item"][:52], r["pass_rate"], r["var_model"], r["var_run"],
            r["discrimination"], r["label"]))

    if args.json:
        json.dump({"meta": meta, "items": rows, "label_counts": dict(counts)},
                  open(args.json, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        print("\nwrote", args.json)


if __name__ == "__main__":
    main()
