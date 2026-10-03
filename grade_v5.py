#!/usr/bin/env python3
"""V5 grader — host-side scoring for the datapipe v2.4 benchmark.

Usage:
    python grade_v5.py <candidate-repo-root> [--label NAME] [--json OUT.json]

Design notes (see spec/V5_DESIGN.md):
  * Every suite has a FIXED expected test count. If pytest collects fewer tests
    than expected (import/collection error), the suite is marked INVALID and the
    missing tests count as failures — the denominator can never shrink.
  * Collection errors are detected explicitly (pytest exit code 2/3/4, or an
    "error" line in the summary), never inferred from a regex over "X passed".
  * Emits machine-readable JSON and computes the semantic behavior score from
    v5/behavior_manifest.json (a behavior counts only when ALL its tests pass).
  * Legacy suites (d10..v4) are scored separately and reported, but the V5
    behavior score is the primary signal.
  * Runs with plain stdlib + pytest; no network, no third-party deps.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
BENCH_ROOT = HERE  # the directory containing v5/, d10/, ...

# Fixed expected test counts — the frozen V5 suite.
V5_SUITES = {
    "core": 19,
    "interaction": 8,
    "adversarial": 19,
    "boss": 11,
    "metamorphic": 9,
}
V5_TOTAL_EXPECTED = sum(V5_SUITES.values())

# Legacy suites retained for historical comparability (frozen; not modified).
LEGACY_SUITES = {
    "d10": 11, "d11": 11, "d12": 10,
    "t2": 8, "t3": 6, "t4": 11, "v4": 24,
}
LEGACY_TOTAL_EXPECTED = sum(LEGACY_SUITES.values())


def _run_pytest(repo, target, extra_env=None):
    """Run pytest on one target and return a structured result."""
    env = dict(os.environ)
    env["DATAPIPE_REPO"] = str(repo)
    env["PYTHONPATH"] = str(repo) + os.pathsep + env.get("PYTHONPATH", "")
    if extra_env:
        env.update(extra_env)
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", str(target), "-q", "--tb=no",
         "-p", "no:cacheprovider", "-rA"],
        cwd=str(BENCH_ROOT), env=env, capture_output=True, text=True,
    )
    out = proc.stdout + "\n" + proc.stderr
    passed = _sum_counts(out, "passed")
    failed = _sum_counts(out, "failed")
    errors = _sum_counts(out, "error")
    # Collection/import errors: pytest exits 2 (interrupted) / 3 (internal) / 4
    # (usage), and prints "ERROR" lines or "errors" in the summary.
    collection_error = proc.returncode in (2, 3, 4) or errors > 0
    failed_tests = re.findall(r"^FAILED ([^\s]+)::(\S+)", out, re.M)
    error_tests = re.findall(r"^ERROR ([^\s]+)", out, re.M)
    passed_ids = set()
    for line in out.splitlines():
        if line.startswith("PASSED "):
            tid = line[len("PASSED "):].strip()
            if tid.startswith("v5/"):
                tid = tid[len("v5/"):]
            passed_ids.add(tid)
    return {
        "passed": passed,
        "failed": failed,
        "errors": errors,
        "collection_error": collection_error,
        "returncode": proc.returncode,
        "failed_tests": [f"{a}::{b}" for a, b in failed_tests],
        "error_targets": error_tests,
        "passed_ids": passed_ids,
    }


def _sum_counts(text, word):
    return sum(int(m) for m in re.findall(r"(\d+) " + word, text))


def _score_suite(result, expected):
    """Normalize a suite result against its fixed expected count.

    A collection error invalidates the suite: all expected tests count as
    failures so the denominator cannot shrink.
    """
    if result["collection_error"]:
        return {
            "passed": 0,
            "failed": expected,
            "errors": result["errors"],
            "expected": expected,
            "invalid": True,
        }
    # Trust pytest's own counts, but never let a shrunk denominator hide tests:
    # if fewer tests ran than expected, the shortfall is failed.
    observed = result["passed"] + result["failed"]
    shortfall = max(0, expected - observed)
    passed = result["passed"]
    failed = result["failed"] + shortfall
    return {
        "passed": passed,
        "failed": failed,
        "errors": result["errors"],
        "expected": expected,
        "invalid": shortfall > 0,
    }


def _behavior_score(suite_status, manifest):
    """Compute per-category and overall semantic behavior scores.

    suite_status: {"core": {"passed_ids": set(), ...}, ...}
    A behavior is satisfied only when every one of its tests passed.
    """
    categories = {}
    all_behaviors = 0
    all_satisfied = 0
    for cat, cdef in manifest["categories"].items():
        behaviors = cdef["behaviors"]
        satisfied = 0
        detail = {}
        for name, bdef in behaviors.items():
            ok = True
            missing = []
            for tid in bdef["tests"]:
                suite = tid.split("/", 1)[0]
                if tid not in suite_status.get(suite, {}).get("passed_ids", set()):
                    ok = False
                    missing.append(tid)
            detail[name] = {"satisfied": ok, "failing": missing}
            if ok:
                satisfied += 1
        total = len(behaviors)
        categories[cat] = {
            "satisfied": satisfied,
            "total": total,
            "score": satisfied / total if total else 0.0,
            "behaviors": detail,
        }
        all_behaviors += total
        all_satisfied += satisfied
    overall = all_satisfied / all_behaviors if all_behaviors else 0.0
    return {
        "overall": overall,
        "behaviors_satisfied": all_satisfied,
        "behaviors_total": all_behaviors,
        "categories": categories,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("repo")
    ap.add_argument("--label", default="")
    ap.add_argument("--json", dest="json_out", default="")
    args = ap.parse_args()

    repo = Path(args.repo).resolve()
    label = args.label or repo.name
    started = time.time()

    report = {
        "label": label,
        "repo": str(repo),
        "benchmark": "datapipe-v2.4-v5",
        "v5": {"suites": {}, "raw": {}, "behavior": {}},
        "legacy": {"suites": {}, "raw": {}},
        "public": {},
        "runtime_seconds": None,
    }

    suite_status = {}
    for suite, expected in V5_SUITES.items():
        target = BENCH_ROOT / "v5" / suite
        res = _run_pytest(repo, target)
        score = _score_suite(res, expected)
        report["v5"]["suites"][suite] = {
            **score,
            "collection_error": res["collection_error"],
            "failed_tests": res["failed_tests"],
            "error_targets": res["error_targets"],
        }
        suite_status[suite] = {
            "passed_ids": res["passed_ids"],
            "score": score,
        }

    v5_passed = sum(s["passed"] for s in report["v5"]["suites"].values())
    v5_expected = sum(s["expected"] for s in report["v5"]["suites"].values())
    report["v5"]["raw"] = {
        "passed": v5_passed,
        "total": v5_expected,
        "ratio": v5_passed / v5_expected if v5_expected else 0.0,
    }

    manifest = json.loads((BENCH_ROOT / "v5" / "behavior_manifest.json").read_text(encoding="utf-8"))
    report["v5"]["behavior"] = _behavior_score(suite_status, manifest)

    # Legacy suites (frozen; reported separately for historical comparability).
    for suite, expected in LEGACY_SUITES.items():
        res = _run_pytest(repo, BENCH_ROOT / suite)
        report["legacy"]["suites"][suite] = _score_suite(res, expected)
    lp = sum(s["passed"] for s in report["legacy"]["suites"].values())
    le = sum(s["expected"] for s in report["legacy"]["suites"].values())
    report["legacy"]["raw"] = {"passed": lp, "total": le, "ratio": lp / le if le else 0.0}

    # Public suite (control layer; inside the candidate repo).
    pub = _run_pytest(repo, repo / "tests" / "public") if (repo / "tests" / "public").is_dir() else None
    if pub is not None:
        report["public"] = {
            "passed": pub["passed"],
            "failed": pub["failed"],
            "errors": pub["errors"],
            "collection_error": pub["collection_error"],
        }

    report["runtime_seconds"] = round(time.time() - started, 2)

    text = json.dumps(report, ensure_ascii=False, indent=2)
    print(text)
    if args.json_out:
        Path(args.json_out).write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
