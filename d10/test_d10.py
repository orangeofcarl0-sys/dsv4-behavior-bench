"""D10: pressure tests targeting GOLD/m1-router 8/8 blind spots.
Each test derives strictly from the v2.3 spec text; designed to be passable
only by a complete implementation.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

from conftest import read_jsonl, write_jsonl, ingest_mod, transform_mod, emit_mod


def run_cli(workdir, *args):
    env = dict(os.environ)
    repo = os.environ.get("DATAPIPE_REPO", "")
    env["PYTHONPATH"] = repo + os.pathsep + env.get("PYTHONPATH", "")
    return subprocess.run(
        [sys.executable, "-m", "datapipe.cli", *args],
        cwd=str(workdir), env=env, capture_output=True, text=True, timeout=60,
    )


# ── D10.1: extreme timezone offset crosses UTC day boundary ──────────────────
# spec: "全部归一为 UTC 且以 Z 结尾" — +14:00 is the legal ISO max offset.

def test_d101_extreme_offset_utc_normalization(workdir):
    src = workdir / "in.jsonl"
    write_jsonl(src, [{"device_id": "a", "timestamp": "2026-08-01T23:30:00+14:00", "temp": 22.0}])
    out = workdir / "t.jsonl"
    kept, skipped = transform_mod.transform(str(src), str(out))
    assert kept == 1 and skipped == 0
    rows = read_jsonl(out)
    # 2026-08-01T23:30+14:00 == 2026-08-01T09:30Z (crosses back a day? no: 23:30-14:00=09:30 same day)
    assert rows[0]["timestamp"] == "2026-08-01T09:30:00Z", f"got {rows[0]['timestamp']!r}"


def test_d102_negative_offset_utc_normalization(workdir):
    src = workdir / "in.jsonl"
    write_jsonl(src, [{"device_id": "a", "timestamp": "2026-08-01T00:30:00-12:00", "temp": 22.0}])
    out = workdir / "t.jsonl"
    kept, _ = transform_mod.transform(str(src), str(out))
    rows = read_jsonl(out)
    # 00:30-12:00 = 12:30Z same day
    assert rows[0]["timestamp"] == "2026-08-01T12:30:00Z", f"got {rows[0]['timestamp']!r}"


# ── D10.2: microsecond precision preserved ───────────────────────────────────

def test_d102_microseconds_preserved(workdir):
    src = workdir / "in.jsonl"
    write_jsonl(src, [{"device_id": "a", "timestamp": "2026-08-01T02:00:00.123456+08:00", "temp": 22.0}])
    out = workdir / "t.jsonl"
    kept, _ = transform_mod.transform(str(src), str(out))
    rows = read_jsonl(out)
    # 02:00:00.123456+08:00 = 2026-07-31T18:00:00.123456Z
    assert rows[0]["timestamp"] == "2026-07-31T18:00:00.123456Z", f"got {rows[0]['timestamp']!r}"


# ── D10.3: filter negative numbers and whitespace forms ─────────────────────

def test_d103_filter_negative_number(workdir):
    src = workdir / "in.jsonl"
    write_jsonl(src, [
        {"device_id": "a", "timestamp": "2026-08-01T00:00:00Z", "temp": -20.0},
        {"device_id": "b", "timestamp": "2026-08-01T00:00:01Z", "temp": 5.0},
    ])
    out = workdir / "t.jsonl"
    kept, _ = transform_mod.transform(str(src), str(out), filter_expr="temp>-15")
    rows = read_jsonl(out)
    assert kept == 1 and rows[0]["device_id"] == "b", f"got {rows}"


def test_d104_filter_whitespace_padded(workdir):
    src = workdir / "in.jsonl"
    write_jsonl(src, [{"device_id": "a", "timestamp": "2026-08-01T00:00:00Z", "temp": 30.0}])
    out = workdir / "t.jsonl"
    kept, _ = transform_mod.transform(str(src), str(out), filter_expr="  temp > 25  ")
    assert kept == 1


def test_d105_filter_negative_value_with_space(workdir):
    src = workdir / "in.jsonl"
    write_jsonl(src, [{"device_id": "a", "timestamp": "2026-08-01T00:00:00Z", "temp": -40.0}])
    out = workdir / "t.jsonl"
    kept, _ = transform_mod.transform(str(src), str(out), filter_expr="temp>= -40")
    assert kept == 1


# ── D10.4: empty catalog and all-skipped robustness ──────────────────────────

def test_d106_empty_catalog_transform(workdir):
    src = workdir / "empty.jsonl"
    src.write_text("", encoding="utf-8")
    out = workdir / "t.jsonl"
    kept, skipped = transform_mod.transform(str(src), str(out))
    assert kept == 0 and skipped == 0
    assert Path(out).exists() and Path(out).read_text(encoding="utf-8") == ""


def test_d107_all_skipped_emit_stats(workdir):
    src = workdir / "in.jsonl"
    write_jsonl(src, [{"device_id": "a", "timestamp": "2026-08-01T00:00:00Z", "temp": 999.0}])  # out of range
    out = workdir / "t.jsonl"
    kept, skipped = transform_mod.transform(str(src), str(out))
    assert kept == 0 and skipped == 1
    text, stats = emit_mod.emit(str(out), "json")
    assert stats["count"] == 0 and stats["min"] is None and stats["max"] is None and stats["mean"] is None


# ── D10.5: chain via CLI default file names ──────────────────────────────────

def test_d108_cli_chain_default_filenames(workdir):
    """Default outputs: ingest->catalog.jsonl, transform->transformed.jsonl,
    emit reads transformed.jsonl by default."""
    src = workdir / "in.csv"
    src.write_text("device_id,timestamp,temp,humidity\na,2026-08-01T00:00:00Z,20,45\n", encoding="utf-8")
    r1 = run_cli(workdir, "ingest", str(src))
    assert r1.returncode == 0 and (workdir / "catalog.jsonl").exists(), r1.stderr
    r2 = run_cli(workdir, "transform")
    assert r2.returncode == 0 and (workdir / "transformed.jsonl").exists(), r2.stderr
    r3 = run_cli(workdir, "emit", "--format", "json")
    assert r3.returncode == 0, r3.stderr
    doc = json.loads(r3.stdout)
    assert doc["stats"]["count"] == 1


# ── D10.6: unit=f boundary values exact ──────────────────────────────────────

def test_d109_unit_f_boundary_exact(workdir):
    src = workdir / "in.jsonl"
    write_jsonl(src, [{"device_id": "a", "timestamp": "2026-08-01T00:00:00Z", "temp": -40.0}])
    out = workdir / "t.jsonl"
    kept, _ = transform_mod.transform(str(src), str(out), unit="f")
    rows = read_jsonl(out)
    # -40C = -40F exactly
    assert abs(rows[0]["temp"] - (-40.0)) < 1e-9


def test_d1010_unit_f_85c(workdir):
    src = workdir / "in.jsonl"
    write_jsonl(src, [{"device_id": "a", "timestamp": "2026-08-01T00:00:00Z", "temp": 85.0}])
    out = workdir / "t.jsonl"
    kept, _ = transform_mod.transform(str(src), str(out), unit="f")
    rows = read_jsonl(out)
    assert abs(rows[0]["temp"] - 185.0) < 1e-9
