#!/usr/bin/env python3
"""analyze_rep.py -- aggregate all replicates into per-level mean / spread.

rep 1 lives in logs_v5/ (the original sweep); rep N lives in logs_v5_rN/.
usage: python3 analyze_rep.py [--reps 1 2 3]
"""
import argparse, collections, json, os, statistics

W = os.path.dirname(os.path.abspath(__file__))
LEVELS = ["low", "medium", "high", "xhigh", "max"]
SUITES = ["core", "interaction", "adversarial", "boss", "metamorphic"]
CATS = ["contract", "interaction", "adversarial", "boss", "metamorphic"]


def log_dir(rep):
    return os.path.join(W, "logs_v5" if rep == 1 else "logs_v5_r%d" % rep)


def process_metrics(rep, level):
    d = log_dir(rep)
    nd = os.path.join(d, level + ".ndjson")
    steps = thinking = 0
    tools = collections.Counter()
    if os.path.exists(nd):
        with open(nd, encoding="utf-8") as fh:
            for ln in fh:
                ln = ln.strip()
                if not ln:
                    continue
                try:
                    o = json.loads(ln)
                except Exception:
                    continue
                if o.get("type") == "status" and o.get("phase") == "step_start":
                    steps += 1
                elif o.get("type") == "thinking":
                    thinking += 1
                elif o.get("type") == "tool_call":
                    tools[o.get("name") or o.get("tool") or "?"] += 1
    wall = None
    s, e = os.path.join(d, level + ".start"), os.path.join(d, level + ".end")
    if os.path.exists(s) and os.path.exists(e):
        wall = int(open(e).read().strip()) - int(open(s).read().strip())
    return {"steps": steps, "thinking_events": thinking,
            "tool_calls_total": sum(tools.values()), "tools": dict(tools), "wall_seconds": wall}


def load_grade(rep, level):
    p = os.path.join(log_dir(rep), "grade_" + level + ".json")
    if not os.path.exists(p):
        return None
    d = json.load(open(p, encoding="utf-8"))
    v5 = d["v5"]
    unsat = []
    for cat, cv in v5["behavior"]["categories"].items():
        for name, bv in cv.get("behaviors", {}).items():
            if not bv["satisfied"]:
                unsat.append(cat + "/" + name)
    fails = [x.split("::")[-1] for ts in v5["suites"].values() for x in ts.get("failed_tests", [])]
    return {
        "raw": v5["raw"]["passed"], "behavior": v5["behavior"]["overall"],
        "behaviors_satisfied": v5["behavior"]["behaviors_satisfied"],
        "categories": {c: v5["behavior"]["categories"][c]["score"] for c in v5["behavior"]["categories"]},
        "suites": {s: v5["suites"][s]["passed"] for s in v5["suites"]},
        "legacy": d["legacy"]["raw"]["passed"], "public": d["public"]["passed"],
        "unsat": unsat, "failed_tests": fails,
    }


def stat(xs):
    if not xs:
        return {"n": 0}
    out = {"n": len(xs), "mean": statistics.fmean(xs), "min": min(xs), "max": max(xs),
           "values": list(xs)}
    if len(xs) > 1:
        out["sd"] = statistics.stdev(xs)
        out["sem"] = out["sd"] / (len(xs) ** 0.5)
    else:
        out["sd"] = None
        out["sem"] = None
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, nargs="+", default=[1, 2, 3])
    args = ap.parse_args()
    reps = args.reps

    data = {"reps": reps, "levels": {}}
    for lv in LEVELS:
        rows = []
        for rep in reps:
            g = load_grade(rep, lv)
            if g is None:
                continue
            p = process_metrics(rep, lv)
            rows.append({"rep": rep, "grade": g, "process": p})
        data["levels"][lv] = {
            "runs": rows,
            "raw": stat([r["grade"]["raw"] for r in rows]),
            "behavior": stat([r["grade"]["behavior"] for r in rows]),
            "legacy": stat([r["grade"]["legacy"] for r in rows]),
            "steps": stat([r["process"]["steps"] for r in rows]),
            "tool_calls": stat([r["process"]["tool_calls_total"] for r in rows]),
            "wall": stat([r["process"]["wall_seconds"] for r in rows if r["process"]["wall_seconds"]]),
            "category_means": {c: statistics.fmean([r["grade"]["categories"][c] for r in rows])
                               for c in rows[0]["grade"]["categories"]} if rows else {},
        }

    out_json = os.path.join(W, "logs_v5", "summary_n%d.json" % len(reps))
    json.dump(data, open(out_json, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    L = []
    w = L.append
    Q = chr(96)
    t = lambda s: Q + s + Q
    w("# V5 effort sweep - aggregate over n=%d replicates" % len(reps))
    w("")
    w("Per-run values in rep order. Mean +/- sample sd.")
    w("")
    w("| effort | V5 raw per run | raw mean +/- sd | behavior per run | behavior mean | legacy per run | steps per run | wall per run |")
    w("|---|---|---:|---|---:|---|---|---|")
    for lv in LEVELS:
        d = data["levels"][lv]
        if not d["runs"]:
            continue
        raw = "/".join(str(r["grade"]["raw"]) for r in d["runs"])
        beh = "/".join("%.3f" % r["grade"]["behavior"] for r in d["runs"])
        leg = "/".join(str(r["grade"]["legacy"]) for r in d["runs"])
        stp = "/".join(str(r["process"]["steps"]) for r in d["runs"])
        wal = "/".join("%ss" % r["process"]["wall_seconds"] for r in d["runs"])
        sd = d["raw"]["sd"]
        w("| %s | %s | %.1f %s %.1f | %s | %.3f | %s | %s | %s |" % (
            lv, raw, d["raw"]["mean"], "+/-", sd if sd is not None else float("nan"),
            beh, d["behavior"]["mean"], leg, stp, wal))
    w("")
    w("## Failing tests per replicate")
    w("")
    for lv in LEVELS:
        d = data["levels"][lv]
        if not d["runs"]:
            continue
        w("**%s**" % lv)
        for r in d["runs"]:
            g = r["grade"]
            if g["failed_tests"]:
                w("- rep%d: %s" % (r["rep"], ", ".join(t(x) for x in g["failed_tests"])))
            else:
                w("- rep%d: none (66/66)" % r["rep"])
        w("")
    w("## Behaviour category means over replicates")
    w("")
    w("| effort | " + " | ".join(CATS) + " |")
    w("|---|" + "---:|" * len(CATS))
    for lv in LEVELS:
        d = data["levels"][lv]
        if not d["runs"]:
            continue
        w("| %s | %s |" % (lv, " | ".join("%.2f" % d["category_means"][c] for c in CATS)))
    w("")

    open(os.path.join(W, "analyze_v5_n%d.md" % len(reps)), "w", encoding="utf-8", newline="\n").write("\n".join(L) + "\n")
    print("\n".join(L))
    print("\nwrote", out_json)


if __name__ == "__main__":
    main()
