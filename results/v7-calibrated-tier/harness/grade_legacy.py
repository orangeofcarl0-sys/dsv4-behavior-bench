#!/usr/bin/env python3
"""grade_legacy.py -- host-side legacy d10..v4 scoring for Phase 2.

usage: python3 grade_legacy.py <candidate> [rep ...]

Fixed expected counts: a collection error marks the suite invalid and the
missing tests count as failures, so the denominator never shrinks.
"""
import json, os, re, subprocess, sys

W = os.path.dirname(os.path.abspath(__file__))
BENCH = os.path.join(W, "bench")
SUITES = ["d10", "d11", "d12", "t2", "t3", "t4", "v4"]
EXPECTED = {"d10": 11, "d11": 11, "d12": 10, "t2": 8, "t3": 6, "t4": 11, "v4": 24}


def run_suite(repo, suite, verbose=False):
    env = dict(os.environ, DATAPIPE_REPO=repo, PYTHONPATH=repo)
    p = subprocess.run([sys.executable, "-m", "pytest", suite, "-q", "--tb=no",
                        "-p", "no:cacheprovider", "-rf"],
                       cwd=BENCH, env=env, capture_output=True, text=True)
    out = p.stdout + "\n" + p.stderr
    if verbose:
        sys.stderr.write("[%s] rc=%s\n%s\n" % (suite, p.returncode, out[-600:]))
    passed = sum(int(m) for m in re.findall(r"(\d+) passed", out))
    failed = sum(int(m) for m in re.findall(r"(\d+) failed", out))
    errors = sum(int(m) for m in re.findall(r"(\d+) error", out))
    names = re.findall(r"^FAILED ([^\s:]+)::(\S+)", out, re.M)
    collection_error = p.returncode in (2, 3, 4) or errors > 0
    return passed, failed, errors, ["%s::%s" % ab for ab in names], collection_error, out


def main():
    cand = sys.argv[1]
    reps = [int(x) for x in sys.argv[2:]] or [1, 2, 3]
    outdir = os.path.join(W, "legacy_logs", cand)
    os.makedirs(outdir, exist_ok=True)

    for rep in reps:
        repo = os.path.join(W, "legacy_runs", cand, "r%d" % rep)
        if not os.path.isdir(repo):
            print("missing", repo)
            continue
        res = {"candidate": cand, "rep": rep, "repo": repo, "suites": {}, "failures": []}
        tp = tf = 0
        for s in SUITES:
            passed, failed, errors, names, cerr, raw = run_suite(repo, s)
            obs = passed + failed
            short = max(0, EXPECTED[s] - obs)
            if cerr:
                passed, failed, short = 0, EXPECTED[s], 0
            res["suites"][s] = {"passed": passed, "failed": failed + short,
                                "expected": EXPECTED[s], "errors": errors,
                                "invalid": cerr or short > 0, "failed_tests": names}
            tp += passed
            tf += failed + short
            res["failures"] += names
            if cerr and len(res["failures"]) == len(names):
                res.setdefault("diagnostics", {})[s] = raw[-400:]
        res["total_passed"] = tp
        res["total_failed"] = tf
        res["total"] = tp + tf
        with open(os.path.join(outdir, "grade_r%d.json" % rep), "w", encoding="utf-8") as f:
            json.dump(res, f, ensure_ascii=False, indent=2)
        print("  %-22s r%d legacy %d/%d" % (cand, rep, tp, tp + tf))


if __name__ == "__main__":
    main()
