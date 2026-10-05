"""V7 tier conftest -- same DATAPIPE_REPO convention as the legacy suites.

V7 scores SEMANTIC BEHAVIOURS, not test counts: one file per behaviour, and the
grader requires every test in a behaviour file to pass before the behaviour
counts. That is what removes the legacy repetition weighting (7 tests for one
behaviour in the old suite).
"""
import json
import os
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1] / "ablation-task" / "datapipe"
if "DATAPIPE_REPO" in os.environ:
    REPO = Path(os.environ["DATAPIPE_REPO"])
sys.path.insert(0, str(REPO))

from datapipe import ingest as ingest_mod
from datapipe import transform as transform_mod
from datapipe import emit as emit_mod


@pytest.fixture()
def workdir(tmp_path):
    return tmp_path


def write_jsonl(path, rows):
    path.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")


def read_jsonl(path):
    return [json.loads(ln) for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]


def run_cli(args, cwd=None):
    """invoke the CLI entry point, returning (returncode, stdout, stderr)"""
    import subprocess
    env = dict(os.environ, PYTHONPATH=str(REPO))
    p = subprocess.run([sys.executable, "-m", "datapipe.cli", *args],
                       cwd=str(cwd or REPO), env=env, capture_output=True, text=True)
    return p.returncode, p.stdout, p.stderr
