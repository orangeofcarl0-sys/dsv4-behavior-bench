#!/usr/bin/env python3
"""anchor_profile.py -- how do seed / gold / gold2 score on each live behaviour?

Gives the V7 anchors: the tier must have seed low, gold2 high, and the live
behaviours must actually separate them.
"""
import json, os, re, subprocess, sys

W = os.path.dirname(os.path.abspath(__file__))
BENCH = os.path.join(W, "bench")
REF = os.path.join(W, "ref_aa2d0a8")
SEED = "<seed-root>/datapipe"

BM = json.load(open(os.path.join(W, "legacy_behavior_map.json"), encoding="utf-8"))
IA = json.load(open(os.path.join(W, "legacy_item_analysis.json"), encoding="utf-8"))
LIVE = [i["item"] for i in IA["items"] if i["label"] == "high-value"]
LIVE_SET = set(LIVE)

# behaviour -> which of its tests are live
def live_tests_of(bid):
    return [t for t in BM["behaviors"][bid]["tests"] if t in LIVE_SET]


def legacy_failures(repo):
    env = dict(os.environ, DATAPIPE_REPO=repo, PYTHONPATH=repo)
    p = subprocess.run([sys.executable, "-m", "pytest", "d10", "d11", "d12", "t2", "t3", "t4", "v4",
                        "-q", "--tb=no", "-p", "no:cacheprovider"],
                       cwd=BENCH, env=env, capture_output=True, text=True)
    out = p.stdout + p.stderr
    return set(m.split("::")[-1] for m in re.findall(r"^FAILED \S+::(\S+)", out, re.M)), out


print("%-34s %6s %6s %6s   %s" % ("behaviour", "seed", "gold", "gold2", "live tests"))
results = {}
for label, repo in (("seed", SEED), ("gold", REF + "/gold"), ("gold2", REF + "/gold2")):
    results[label] = legacy_failures(repo)

for bid, b in sorted(BM["behaviors"].items()):
    lt = live_tests_of(bid)
    if not lt:
        continue
    cells = []
    for label in ("seed", "gold", "gold2"):
        fails, _ = results[label]
        n_fail = sum(1 for t in lt if t in fails)
        cells.append("%d/%d" % (len(lt) - n_fail, len(lt)))
    print("%-34s %6s %6s %6s" % (bid, cells[0], cells[1], cells[2]))
