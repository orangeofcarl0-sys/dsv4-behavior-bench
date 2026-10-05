#!/usr/bin/env python3
"""grade_v7.py -- host-side scoring for the V7 calibrated discrimination tier.

usage: python3 grade_v7.py <candidate-repo-root> [--label NAME] [--json OUT.json]

Design (per the design brief):
  * ONE behaviour per file; a behaviour counts only when EVERY test in its file passes.
    This removes the legacy repetition weighting (7 tests for one behaviour -> 1).
  * Fixed expected test count per behaviour file: fewer tests run than expected marks
    the behaviour invalid and it counts as unmet, so the denominator never shrinks.
  * Three explicit weight tiers (basic 1 / inference 2 / hard 3), fixed and public.
  * Reports both the weighted behaviour score and the raw test counts for debugging.
"""
import argparse, json, os, re, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BENCH_ROOT = HERE
MANIFEST = json.load(open(HERE / "v7" / "behavior_manifest.json", encoding="utf-8"))
WEIGHTS = MANIFEST["weights"]


def run_behaviour(repo, behaviour):
    target = BENCH_ROOT / behaviour["file"]
    env = dict(os.environ)
    env["DATAPIPE_REPO"] = str(repo)
    env["PYTHONPATH"] = str(repo) + os.pathsep + str(BENCH_ROOT / "v7") + os.pathsep + env.get("PYTHONPATH", "")
    p = subprocess.run([sys.executable, "-m", "pytest", str(target), "-q", "--tb=no",
                        "-p", "no:cacheprovider", "-rf"],
                       cwd=str(BENCH_ROOT), env=env, capture_output=True, text=True)
    out = p.stdout + "\n" + p.stderr
    passed = sum(int(m) for m in re.findall(r"(\d+) passed", out))
    failed = sum(int(m) for m in re.findall(r"(\d+) failed", out))
    errors = sum(int(m) for m in re.findall(r"(\d+) error", out))
    names = re.findall(r"^FAILED \S+::(\S+)", out, re.M)
    collection_error = p.returncode in (2, 3, 4) or errors > 0
    return {"passed": passed, "failed": failed, "errors": errors,
            "invalid": collection_error, "failed_tests": names, "raw": out[-800:]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("repo")
    ap.add_argument("--label", default="")
    ap.add_argument("--json", default=None)
    args = ap.parse_args()

    report = {"label": args.label or os.path.basename(args.repo.rstrip("/")),
              "repo": args.repo, "tier": "V7", "behaviours": {}, "raw_passed": 0, "raw_total": 0}
    earned = possible = 0.0
    for b in MANIFEST["behaviours"]:
        res = run_behaviour(args.repo, b)
        w = WEIGHTS.get(b["tier"], 0)
        satisfied = (not res["invalid"]) and res["failed"] == 0 and res["passed"] > 0
        scored = b.get("scored", True)
        earner = w if (satisfied and scored) else 0
        if scored:
            earned += earner
            possible += w
        report["raw_passed"] += res["passed"]
        report["raw_total"] += res["passed"] + res["failed"]
        report["behaviours"][b["id"]] = {
            "tier": b["tier"], "weight": w, "satisfied": satisfied, "scored": b.get("scored", True),
            "passed": res["passed"], "failed": res["failed"], "invalid": res["invalid"],
            "failed_tests": res["failed_tests"], "anchor": b.get("anchor"),
            "source": b.get("source"), "note": b.get("note"),
        }
    report["weighted_earned"] = earned
    report["weighted_possible"] = possible
    report["score"] = earned / possible if possible else 0.0
    report["behaviours_satisfied"] = sum(1 for v in report["behaviours"].values() if v["satisfied"])
    report["behaviours_total"] = len(report["behaviours"])

    if args.json:
        json.dump(report, open(args.json, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(json.dumps({k: v for k, v in report.items() if k != "behaviours"}, ensure_ascii=False, indent=2))
    for bid, v in report["behaviours"].items():
        print("  %-34s %-9s w=%d %s%s" % (
            bid, v["tier"], v["weight"],
            "PASS" if v["satisfied"] else "fail",
            ("  " + ",".join(t.split("::")[-1] for t in v["failed_tests"])) if v["failed_tests"] else ""))


if __name__ == "__main__":
    main()
