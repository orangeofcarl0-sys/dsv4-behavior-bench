"""Behaviour: CLI exit-code contract (0 success / 1 data error / 2 usage error).

Anchor: seed 1/1, gold 1/1, gold2 1/1 -- for REFERENCES this is a ceiling item.
It is live for models (p=0.89) so it stays, but it is anchored as basic, not hard.
Source: legacy d118 / d119 / d8.
"""
import os
import subprocess
import sys

from conftest import REPO


def cli(args, cwd):
    # the repo entry point is datapipe.cli:main (pyproject [project.scripts]);
    # the legacy suites invoke it as `python -m datapipe.cli`.
    env = dict(os.environ, PYTHONPATH=str(REPO))
    p = subprocess.run([sys.executable, "-m", "datapipe.cli", *args],
                       cwd=str(cwd), env=env, capture_output=True, text=True)
    return p.returncode


def test_unknown_flag_is_usage_error(workdir):
    rc = cli(["transform", "--definitely-not-a-flag"], workdir)
    assert rc == 2, f"usage error must exit 2, got {rc}"


def test_missing_input_is_data_error(workdir):
    rc = cli(["ingest", "does-not-exist.csv"], workdir)
    assert rc == 1, f"missing input must exit 1, got {rc}"


def test_success_is_zero(workdir):
    src = workdir / "in.jsonl"
    src.write_text('{"device_id": "a", "timestamp": "2026-08-01T00:00:00Z", "temp": 20.0}\n',
                   encoding="utf-8")
    rc = cli(["ingest", str(src), "--output", str(workdir / "cat.jsonl")], workdir)
    assert rc == 0, f"success must exit 0, got {rc}"
