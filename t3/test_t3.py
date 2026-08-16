"""T3 hidden-semantics tests: public tests are blind to these by construction.

These check the v2.3 SPEC, not the public test suite:
  - md mean must be ARITHMETIC MEAN (spec), not mid-range (min+max)/2.
    Public ROWS = [20, 30] make both equal (25); asymmetric data separates them.
  - CLI --output must actually write the file (seed ignores it).
  - CLI --summary flag must exist (seed lacks it entirely).
  - dedupe key must lowercase device_id (spec: "device_id 转小写").
  - unit=f conversion must use exact c*9/5+32.
  - CSV emit must quote fields containing commas.
"""
import json
import subprocess
import sys
from pathlib import Path

from conftest import read_jsonl, write_jsonl, ingest_mod, transform_mod, emit_mod


def run_cli(workdir, *args):
    import os
    env = dict(os.environ)
    repo = os.environ.get("DATAPIPE_REPO", "")
    env["PYTHONPATH"] = repo + os.pathsep + env.get("PYTHONPATH", "")
    return subprocess.run(
        [sys.executable, "-m", "datapipe.cli", *args],
        cwd=str(workdir), env=env, capture_output=True, text=True, timeout=60,
    )


def test_t3_md_mean_is_arithmetic_not_midrange(workdir):
    # [10, 20, 60]: arithmetic mean = 30, mid-range (10+60)/2 = 35
    src = workdir / "in.jsonl"
    write_jsonl(src, [
        {"device_id": "a", "timestamp": "2026-08-01T00:00:00Z", "temp": 10.0, "humidity": 10},
        {"device_id": "b", "timestamp": "2026-08-01T00:00:01Z", "temp": 20.0, "humidity": 20},
        {"device_id": "c", "timestamp": "2026-08-01T00:00:02Z", "temp": 60.0, "humidity": 30},
    ])
    text, stats = emit_mod.emit(str(src), "md")
    assert "- mean: 30.0" in text, f"got md mean line: {[l for l in text.splitlines() if 'mean' in l]}"


def test_t3_cli_output_writes_file(workdir):
    src = workdir / "in.jsonl"
    write_jsonl(src, [{"device_id": "a", "timestamp": "2026-08-01T00:00:00Z", "temp": 22.0}])
    r = run_cli(workdir, "emit", "--input", str(src), "--format", "json", "--output", str(workdir / "out.json"))
    assert r.returncode == 0, r.stderr
    assert (workdir / "out.json").exists(), "CLI --output did not write the file"


def test_t3_cli_summary_flag_exists(workdir):
    src = workdir / "in.jsonl"
    write_jsonl(src, [{"device_id": "a", "timestamp": "2026-08-01T00:00:00Z", "temp": 22.0}])
    r = run_cli(workdir, "emit", "--input", str(src), "--format", "json", "--summary")
    assert r.returncode == 0, r.stderr
    assert "summary" in r.stdout


def test_t3_dedupe_lowercases_device_id(workdir):
    src = workdir / "in.jsonl"
    write_jsonl(src, [
        {"device_id": "AB-1", "timestamp": "2026-08-01T00:00:00Z", "temp": 10.0},
        {"device_id": "ab-1", "timestamp": "2026-08-01T00:00:00Z", "temp": 25.0},
    ])
    out = workdir / "t.jsonl"
    kept, _ = transform_mod.transform(str(src), str(out), dedupe=True)
    assert kept == 1, "dedupe must treat AB-1 == ab-1"
    rows = read_jsonl(out)
    assert rows[0]["temp"] == 25.0  # keeps LAST


def test_t3_unit_f_exact(workdir):
    src = workdir / "in.jsonl"
    write_jsonl(src, [{"device_id": "a", "timestamp": "2026-08-01T00:00:00Z", "temp": 20.0}])
    out = workdir / "t.jsonl"
    kept, _ = transform_mod.transform(str(src), str(out), unit="f")
    rows = read_jsonl(out)
    assert rows[0]["temp"] == 68.0  # 20 * 9/5 + 32 exactly


def test_t3_csv_emit_quotes_commas(workdir):
    src = workdir / "in.jsonl"
    write_jsonl(src, [{"device_id": "a,1", "timestamp": "2026-08-01T00:00:00Z", "temp": 22.0, "humidity": 45}])
    text, _ = emit_mod.emit(str(src), "csv")
    assert '"a,1"' in text, "CSV must quote device_id containing a comma"
