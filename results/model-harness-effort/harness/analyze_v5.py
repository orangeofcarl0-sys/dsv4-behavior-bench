#!/usr/bin/env python3
"""analyze_v5.py -- aggregate V5 grades + per-run process metrics into one JSON + markdown table.

usage: python3 analyze_v5.py [--out FILE]
"""
import argparse, collections, json, os, sys

W = os.path.dirname(os.path.abspath(__file__))
LEVELS = ["low", "medium", "high", "xhigh", "max"]
SUITES = ["core", "interaction", "adversarial", "boss", "metamorphic"]
CATS = ["contract", "interaction", "adversarial", "boss", "metamorphic"]


def process_metrics(level):
    """steps / thinking events / tool calls / wall seconds from one headless run."""
    nd = os.path.join(W, "logs_v5", level + ".ndjson")
    steps = thinking = text_chars = 0
    tool_calls = collections.Counter()
    final_text = ""
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
                t = o.get("type")
                if t == "status" and o.get("phase") == "step_start":
                    steps += 1
                elif t == "thinking":
                    thinking += 1
                elif t == "text":
                    c = o.get("text") or ""
                    text_chars += len(c)
                    final_text = c
                elif t == "tool_call":
                    tool_calls[o.get("name") or o.get("tool") or "?"] += 1
    wall = None
    s, e = os.path.join(W, "logs_v5", level + ".start"), os.path.join(W, "logs_v5", level + ".end")
    if os.path.exists(s) and os.path.exists(e):
        wall = int(open(e).read().strip()) - int(open(s).read().strip())
    return {
        "steps": steps,
        "thinking_events": thinking,
        "tool_calls_total": sum(tool_calls.values()),
        "tool_calls": dict(tool_calls.most_common()),
        "text_chars": text_chars,
        "wall_seconds": wall,
        "final_message_tail": final_text[-1500:],
    }


def grade(level):
    p = os.path.join(W, "logs_v5", "grade_" + level + ".json")
    if not os.path.exists(p):
        return None
    d = json.load(open(p, encoding="utf-8"))
    v5, leg, beh = d["v5"], d["legacy"], d["v5"]["behavior"]
    unsat = []
    for cat, cv in beh["categories"].items():
        for name, bv in cv.get("behaviors", {}).items():
            if not bv["satisfied"]:
                unsat.append({
                    "category": cat, "behavior": name,
                    "failing_tests": bv.get("failing", []),
                })
    return {
        "v5_raw": v5["raw"],
        "suites": {s: {k: v5["suites"][s][k] for k in ("passed", "failed", "expected", "invalid", "collection_error")}
                   for s in v5["suites"]},
        "failed_tests": {s: v5["suites"][s].get("failed_tests", []) for s in v5["suites"]},
        "behavior": {
            "overall": beh["overall"],
            "satisfied": beh["behaviors_satisfied"],
            "total": beh["behaviors_total"],
            "categories": {c: {"satisfied": beh["categories"][c]["satisfied"],
                               "total": beh["categories"][c]["total"],
                               "score": beh["categories"][c]["score"]} for c in beh["categories"]},
        },
        "unsatisfied_behaviors": unsat,
        "legacy": leg["raw"],
        "public": {k: d["public"][k] for k in ("passed", "failed")},
        "grade_runtime_seconds": d.get("runtime_seconds"),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(W, "logs_v5", "summary.json"))
    args = ap.parse_args()

    out = {"benchmark": "datapipe-v2.4-v5", "levels": {}}
    for lv in LEVELS:
        g = grade(lv)
        out["levels"][lv] = {"grade": g, "process": process_metrics(lv)}
    json.dump(out, open(args.out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    rows = []
    for lv in LEVELS:
        e = out["levels"][lv]
        g, pr = e["grade"], e["process"]
        if g is None:
            rows.append((lv, "—", "—", "—", "—", "—", "—", "—", "—", pr["wall_seconds"], "—", "—"))
            continue
        rows.append((
            lv,
            "%d/%d" % (g["v5_raw"]["passed"], g["v5_raw"]["total"]),
            "%.3f" % g["behavior"]["overall"],
            "%d/%d" % (g["behavior"]["satisfied"], g["behavior"]["total"]),
            " ".join("%s=%d" % (s[:4], g["suites"][s]["passed"]) for s in SUITES),
            " ".join("%s=%.2f" % (c[:4], g["behavior"]["categories"][c]["score"]) for c in CATS),
            "%d/%d" % (g["legacy"]["passed"], g["legacy"]["total"]),
            "%d/%d" % (g["public"]["passed"], g["public"]["passed"] + g["public"]["failed"]),
            len(g["unsatisfied_behaviors"]),
            pr["wall_seconds"], pr["steps"], "%d/%d" % (pr["thinking_events"], pr["tool_calls_total"]),
        ))

    hdr = ("effort", "v5raw", "behav", "beh#", "suite passes", "category scores",
           "legacy", "public", "unsat", "wall_s", "steps", "think/calls")
    widths = [max(len(str(hdr[i])), *(len(str(r[i])) for r in rows)) for i in range(len(hdr))]
    def line(r):
        return " | ".join(str(r[i]).ljust(widths[i]) for i in range(len(hdr)))
    print(line(hdr))
    print("-+-".join("-" * w for w in widths))
    for r in rows:
        print(line(r))
    print("\nwrote", args.out)


if __name__ == "__main__":
    main()
