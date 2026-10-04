#!/usr/bin/env python3
"""V6 grader — score a candidate workspace against one V6 task's hidden suite.

Usage:
    python grade_v6.py <task> <candidate-repo-root> [--json OUT.json]

<task> is one of: taskA_ledger, taskB_framecodec, taskC_cfgmerge.

Same integrity rules as grade_v5.py: the hidden suite has a fixed expected test
count; a collection/import error marks the task invalid and the missing tests
count as failures, so the denominator never shrinks. Output is machine-readable
JSON, and each task also reports its behavior score from behavior_manifest.json.
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
V6 = HERE / "v6"

# Fixed expected hidden-test counts per task.
EXPECTED = {
    "taskA_ledger": 13,
    "taskB_framecodec": 17,
    "taskC_cfgmerge": 17,
}
PUBLIC_EXPECTED = {
    "taskA_ledger": 5,
    "taskB_framecodec": 6,
    "taskC_cfgmerge": 6,
}


def _run_pytest(repo, target, expected_public=False):
    env = dict(os.environ)
    env["CANDIDATE_REPO"] = str(repo)
    env["PYTHONPATH"] = str(repo) + os.pathsep + env.get("PYTHONPATH", "")
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", str(target), "-q", "--tb=no",
         "-p", "no:cacheprovider", "-rA"],
        cwd=str(HERE), env=env, capture_output=True, text=True,
    )
    out = proc.stdout + "\n" + proc.stderr
    passed = sum(int(m) for m in re.findall(r"(\d+) passed", out))
    failed = sum(int(m) for m in re.findall(r"(\d+) failed", out))
    errors = sum(int(m) for m in re.findall(r"(\d+) error", out))
    collection_error = proc.returncode in (2, 3, 4) or errors > 0
    passed_ids = set()
    for line in out.splitlines():
        if line.startswith("PASSED "):
            tid = line[len("PASSED "):].strip()
            # Normalize "v6/taskX/hidden/test_y.py::case" -> "test_y.py::case".
            if "::" in tid:
                path, case = tid.split("::", 1)
                tid = path.replace("\\", "/").split("/")[-1] + "::" + case
            passed_ids.add(tid)
    return {"passed": passed, "failed": failed, "errors": errors,
            "collection_error": collection_error, "returncode": proc.returncode,
            "passed_ids": passed_ids}


def _score(res, expected):
    if res["collection_error"]:
        return {"passed": 0, "failed": expected, "expected": expected, "invalid": True}
    observed = res["passed"] + res["failed"]
    shortfall = max(0, expected - observed)
    return {"passed": res["passed"], "failed": res["failed"] + shortfall,
            "expected": expected, "invalid": shortfall > 0}


def _behavior(suite_status, manifest):
    def _hit(tid):
        # A manifest entry may name a parametrized test without its [param];
        # treat any matching parametrization as the test.
        return tid in suite_status or any(p.startswith(tid + "[") for p in suite_status)

    categories = {}
    total = satisfied_all = 0
    for cat, cdef in manifest["categories"].items():
        sat = 0
        detail = {}
        for name, bdef in cdef["behaviors"].items():
            ok = True
            missing = []
            for tid in bdef["tests"]:
                if not _hit(tid):
                    ok = False
                    missing.append(tid)
            detail[name] = {"satisfied": ok, "failing": missing}
            if ok:
                sat += 1
        categories[cat] = {"satisfied": sat, "total": len(cdef["behaviors"]),
                           "score": sat / len(cdef["behaviors"]) if cdef["behaviors"] else 0.0,
                           "behaviors": detail}
        total += len(cdef["behaviors"])
        satisfied_all += sat
    return {"overall": satisfied_all / total if total else 0.0,
            "behaviors_satisfied": satisfied_all, "behaviors_total": total,
            "categories": categories}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("task")
    ap.add_argument("repo")
    ap.add_argument("--json", dest="json_out", default="")
    args = ap.parse_args()
    task = args.task
    repo = Path(args.repo).resolve()
    started = time.time()

    hidden_dir = V6 / task / "hidden"
    res = _run_pytest(repo, hidden_dir)
    score = _score(res, EXPECTED[task])

    manifest_path = V6 / task / "hidden" / "behavior_manifest.json"
    beh = None
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        beh = _behavior(res["passed_ids"], manifest)

    pub_dir = repo / "tests" / "public"
    pub = None
    if pub_dir.is_dir():
        pr = _run_pytest(repo, pub_dir)
        pub = _score(pr, PUBLIC_EXPECTED[task])

    report = {
        "task": task, "repo": str(repo), "benchmark": "datapipe-v6-prototype",
        "hidden": {**score, "collection_error": res["collection_error"]},
        "behavior": beh,
        "public": pub,
        "runtime_seconds": round(time.time() - started, 2),
    }
    text = json.dumps(report, ensure_ascii=False, indent=2)
    print(text)
    if args.json_out:
        Path(args.json_out).write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
