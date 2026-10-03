# grade.py -- host-side scoring for the dsv4 behavior bench (never shown to candidates)
# usage: python grade.py <datapipe-repo-root> <label>
import os, re, subprocess, sys, json

SUITES = ["d10", "d11", "d12", "t2", "t3", "t4", "v4"]
BENCH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bench")

def run_suite(repo, suite):
    env = dict(os.environ, DATAPIPE_REPO=repo, PYTHONPATH=repo)
    p = subprocess.run(
        [sys.executable, "-m", "pytest", suite, "-q", "--tb=no", "-p", "no:cacheprovider"],
        cwd=BENCH, env=env, capture_output=True, text=True,
    )
    passed = sum(int(m) for m in re.findall(r"(\d+) passed", p.stdout))
    failed = sum(int(m) for m in re.findall(r"(\d+) failed", p.stdout))
    names = re.findall(r"^FAILED ([^\s:]+)::(\S+)", p.stdout, re.M)
    return passed, failed, [f"{a}::{b}" for a, b in names]

def main():
    repo, label = sys.argv[1], sys.argv[2]
    out = {"label": label, "repo": repo, "suites": {}, "failures": []}
    tp = tf = 0
    for s in SUITES:
        p, f, fails = run_suite(repo, s)
        tp += p; tf += f
        out["suites"][s] = {"passed": p, "failed": f, "total": p + f}
        out["failures"] += fails
    # public suite (the insensitive control layer)
    env = dict(os.environ, PYTHONPATH=repo)
    p = subprocess.run([sys.executable, "-m", "pytest", "tests/public", "-q", "--tb=no",
                        "-p", "no:cacheprovider"], cwd=repo, env=env, capture_output=True, text=True)
    pub_pass = sum(int(m) for m in re.findall(r"(\d+) passed", p.stdout))
    pub_fail = sum(int(m) for m in re.findall(r"(\d+) failed", p.stdout))
    out["public"] = {"passed": pub_pass, "failed": pub_fail}
    out["total_passed"] = tp
    out["total_failed"] = tf
    out["total_tests"] = tp + tf
    print(json.dumps(out, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
