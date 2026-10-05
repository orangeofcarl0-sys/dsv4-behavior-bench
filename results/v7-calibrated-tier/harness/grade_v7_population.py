#!/usr/bin/env python3
"""grade_v7_population.py -- score every saved Phase-2 workspace with V7.

Reuses the 18 agent workspaces already produced for the legacy re-evaluation, so
this is a like-for-like comparison on identical artifacts: same run, legacy /81
score vs V7 weighted behaviour score.
"""
import json, os, subprocess, sys

W = os.path.dirname(os.path.abspath(__file__))
BENCH = os.path.join(W, "bench")
CANDS = ["hy4-preview-f", "deepseek-v4.1-flash", "grok-4.7", "gemini-3.5-flash",
         "minimax-m3", "kimi-k2.6"]

out = {}
for cand in CANDS:
    out[cand] = {}
    for rep in (1, 2, 3):
        repo = os.path.join(W, "legacy_runs", cand, "r%d" % rep)
        if not os.path.isdir(repo):
            continue
        jf = os.path.join(W, "v7_pop_%s_r%d.json" % (cand, rep))
        p = subprocess.run([sys.executable, "grade_v7.py", repo, "--label",
                            "%s-r%d" % (cand, rep), "--json", jf],
                           cwd=BENCH, capture_output=True, text=True)
        if not os.path.exists(jf):
            print("FAILED %s r%d: %s" % (cand, rep, p.stderr[-300:]))
            continue
        d = json.load(open(jf, encoding="utf-8"))
        lg = os.path.join(W, "legacy_logs", cand, "grade_r%d.json" % rep)
        legacy = json.load(open(lg, encoding="utf-8"))["total_passed"] if os.path.exists(lg) else None
        out[cand][rep] = {"v7_score": d["score"], "behaviours": d["behaviours_satisfied"],
                          "weighted": d["weighted_earned"], "legacy": legacy,
                          "unmet": [k for k, v in d["behaviours"].items() if not v["satisfied"]]}
        print("%-22s r%d  V7=%.3f (%d/10, w=%.0f)  legacy=%s" % (
            cand, rep, d["score"], d["behaviours_satisfied"], d["weighted_earned"], legacy))

json.dump(out, open(os.path.join(W, "v7_population.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=2)
print("\nwrote v7_population.json")
