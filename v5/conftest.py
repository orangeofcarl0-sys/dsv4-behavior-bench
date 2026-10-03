"""Shared fixtures/helpers for the V5 suites.

Resolves the candidate repo from DATAPIPE_REPO (same convention as the legacy
d10/d11/... suites) and exposes small helpers for building inputs and driving
the CLI.
"""
import csv
import io
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2] / "v5ref"
if "DATAPIPE_REPO" in os.environ:
    REPO = Path(os.environ["DATAPIPE_REPO"])
sys.path.insert(0, str(REPO))

from datapipe import ingest as ingest_mod
from datapipe import transform as transform_mod
from datapipe import emit as emit_mod

try:
    from datapipe import DataError
except ImportError:  # pre-v2.4 implementation: keep the suite collectible so the
    class DataError(Exception):  # gradient stays smooth; DataError tests fail.
        """Placeholder when the candidate does not export DataError."""


@pytest.fixture()
def workdir(tmp_path):
    return tmp_path


def write_jsonl(path, rows):
    path.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    return path


def write_text(path, text):
    path.write_text(text, encoding="utf-8")
    return path


def write_bytes(path, data):
    path.write_bytes(data)
    return path


def write_csv(path, rows, header=("device_id", "timestamp", "temp", "humidity"),
              bom=False):
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\n")
    writer.writerow(header)
    for r in rows:
        writer.writerow([r.get(c, "") for c in header])
    data = buf.getvalue().encode("utf-8")
    if bom:
        data = b"\xef\xbb\xbf" + data
    path.write_bytes(data)
    return path


def read_jsonl(path):
    return [
        json.loads(ln)
        for ln in Path(path).read_text(encoding="utf-8").splitlines()
        if ln.strip()
    ]


def run_cli(workdir, *args):
    env = dict(os.environ)
    env["PYTHONPATH"] = str(REPO) + os.pathsep + env.get("PYTHONPATH", "")
    return subprocess.run(
        [sys.executable, "-m", "datapipe.cli", *args],
        cwd=str(workdir), env=env, capture_output=True, text=True, timeout=60,
    )


def assert_clean_data_error(result):
    """A data error must be *reported* by the CLI (exit 1), not crash with a
    traceback. Spec §7: the CLI maps a data error to exit code 1."""
    assert result.returncode == 1, (result.returncode, result.stderr)
    assert "Traceback" not in result.stderr, result.stderr
    assert result.stderr.strip(), "data error must be reported on stderr"
