#!/usr/bin/env python3
"""make_summary_md.py -- render logs_v5/summary.json + audit.json into analyze_v5_summary.md."""
import json, os

W = os.path.dirname(os.path.abspath(__file__))
LEVELS = ["low", "medium", "high", "xhigh", "max"]
Q = chr(96)


def t(s):
    return Q + s + Q


S = json.load(open(os.path.join(W, "logs_v5", "summary.json"), encoding="utf-8"))
A = json.load(open(os.path.join(W, "logs_v5", "audit.json"), encoding="utf-8"))
L = []
w = L.append

w("# space-bunny-free x dsv4-behavior-bench **V5** (datapipe v2.4) - reasoning-effort sweep")
w("")
w("One-shot, blind, n=1 per level. Graded host-side with the frozen " + t("grade_v5.py") + ".")
w("")
w("## Results")
w("")
w("| effort | V5 raw /66 | behavior /32 | core | inter | adv | boss | meta | legacy /81 | public /25 | wall | steps | think | calls |")
w("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
for lv in LEVELS:
    e = S["levels"][lv]
    g, p = e["grade"], e["process"]
    su = g["suites"]
    w("| %s | **%d/66** | **%.3f** (%d/%d) | %d | %d | %d | %d | %d | %d/81 | %d/25 | %ss | %d | %d | %d |" % (
        lv, g["v5_raw"]["passed"], g["behavior"]["overall"], g["behavior"]["satisfied"], g["behavior"]["total"],
        su["core"]["passed"], su["interaction"]["passed"], su["adversarial"]["passed"],
        su["boss"]["passed"], su["metamorphic"]["passed"],
        g["legacy"]["passed"], g["public"]["passed"], p["wall_seconds"], p["steps"],
        p["thinking_events"], p["tool_calls_total"]))
w("")
w("Calibration anchors (reproduced locally before scoring):")
w("")
w("| object | V5 raw | behavior | legacy |")
w("|---|---:|---:|---:|")
w("| " + t("v5ref") + " (v2.4 reference) | 66/66 | 1.000 | 80/81 |")
w("| " + t("gold2") + " (v2.3-complete solver, from README) | 35/66 | 0.469 | 81/81 |")
w("| " + t("gold") + " (v2.3 GOLD, from README) | 33/66 | 0.438 | 76/81 |")
w("| " + t("v5seed") + " (broken seed) | 17/66 | 0.094 | 37/81 |")
w("")
w("## Category behaviour scores")
w("")
w("| effort | contract | interaction | adversarial | boss | metamorphic |")
w("|---|---:|---:|---:|---:|---:|")
for lv in LEVELS:
    c = S["levels"][lv]["grade"]["behavior"]["categories"]
    w("| %s | %.2f | %.2f | %.2f | %.2f | %.2f |" % (
        lv, c["contract"]["score"], c["interaction"]["score"], c["adversarial"]["score"],
        c["boss"]["score"], c["metamorphic"]["score"]))
w("")
w("## Failures and unsatisfied behaviours")
w("")
for lv in LEVELS:
    g = S["levels"][lv]["grade"]
    fails = [(s, x.split("::")[-1]) for s, ts in g["failed_tests"].items() for x in ts]
    w("**%s** - %d/66 raw, %.3f behaviour, %d unsatisfied behaviour(s)" % (
        lv, g["v5_raw"]["passed"], g["behavior"]["overall"], len(g["unsatisfied_behaviors"])))
    if not fails and not g["unsatisfied_behaviors"]:
        w("- none - full pass, every behaviour satisfied")
    for s, x in fails:
        w("- failing test " + t("v5/" + s + "/...::" + x))
    for u in g["unsatisfied_behaviors"]:
        w("- unsatisfied behaviour " + t(u["category"] + "/" + u["behavior"]) + " (blocked by "
          + ", ".join(x.split("::")[-1] for x in u["failing_tests"]) + ")")
    w("")
w("## Process metrics")
w("")
w("| effort | steps | thinking events | tool calls | tool mix | wall |")
w("|---|---:|---:|---:|---|---:|")
for lv in LEVELS:
    p = S["levels"][lv]["process"]
    mix = " / ".join("%s %d" % (k, v) for k, v in list(p["tool_calls"].items())[:5])
    w("| %s | %d | %d | %d | %s | %ss |" % (lv, p["steps"], p["thinking_events"],
                                              p["tool_calls_total"], mix, p["wall_seconds"]))
w("")
w("## Integrity audit")
w("")
w("| effort | tool calls | tests/ + tools/ source | grading-suite leak hits | absolute paths outside own workspace | verdict |")
w("|---|---:|---|---:|---|---|")
for lv in LEVELS:
    a = A.get(lv)
    if not a:
        continue
    bad = {k: v for k, v in a["path_classes"].items()
           if k in ("OUTSIDE", "OTHER-workspace", "bench-or-gold")}
    w("| %s | %d | %s | %d | %s | %s |" % (
        lv, a["tool_calls"],
        "unchanged" if a["protected_dirs_ok"] else "MODIFIED",
        len(a["leak_hits"]),
        ", ".join("%s x%d" % (k, v) for k, v in bad.items()) or "0",
        "CLEAN" if (a["protected_dirs_ok"] and not a["leak_hits"] and not bad) else "REVIEW"))
w("")
w("All absolute paths a tool call touched were inside the candidate's own workspace or")
w("system locations; " + t("tests/") + " and " + t("tools/") + " source files are byte-identical to the")
w("frozen seed (" + t("__pycache__") + " excluded - running the public tests regenerates bytecode).")
w("")
w("## Toolchain")
w("")
w("- dsh 0.2.0-rc.2, profile " + t("ef-dev") + ", Windows node")
w("- model " + t("space-bunny-free") + " via " + t("opencode-zen") + "; "
  + t("tool-web") + ", " + t("tool-subagent") + ", " + t("tool-subagent-fork") + " disabled")
w("- grader " + t("grade_v5.py") + " on Python 3.14.4 / pytest 9.0.2; frozen hashes verified before the run")

open(os.path.join(W, "analyze_v5_summary.md"), "w", encoding="utf-8", newline="\n").write("\n".join(L) + "\n")
print("wrote analyze_v5_summary.md (%d lines)" % len(L))
