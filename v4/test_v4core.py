"""V4-CORE: only tests that discriminate real agents (verified).
D1/D2/D3 separate; plus new D9/D10 probes targeting GOLD-only semantics
that even m1-router may miss.
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


# D1: NDJSON robustness
def test_d1_ndjson_malformed_line_skipped(workdir):
    src = workdir / "in.ndjson"
    src.write_text(
        '{"device_id": "a", "timestamp": "2026-08-01T00:00:00Z", "temp": 22.0}\n'
        'NOT-JSON\n'
        '{"device_id": "b", "timestamp": "2026-08-01T00:00:01Z", "temp": 23.0}\n',
        encoding="utf-8",
    )
    out = workdir / "cat.jsonl"
    accepted, skipped = ingest_mod.ingest(str(src), str(out))
    assert accepted == 2 and skipped == 1, f"got ({accepted},{skipped})"


def test_d1_ndjson_truncated_line_skipped(workdir):
    src = workdir / "in.ndjson"
    src.write_text(
        '{"device_id": "a", "timestamp": "2026-08-01T00:00:00Z", "temp": 22.0}\n'
        '{"device_id": "b", "timestamp": "2026-08-01T00:00:01Z"\n'
        '{"device_id": "c", "timestamp": "2026-08-01T00:00:02Z", "temp": 24.0}\n',
        encoding="utf-8",
    )
    out = workdir / "cat.jsonl"
    accepted, skipped = ingest_mod.ingest(str(src), str(out))
    assert accepted == 2 and skipped == 1, f"got ({accepted},{skipped})"


# D2: field trimming
def test_d2_device_id_whitespace_trimmed(workdir):
    src = workdir / "in.jsonl"
    write_jsonl(src, [{"device_id": "  ab-1  ", "timestamp": "2026-08-01T00:00:00Z", "temp": 22.0}])
    out = workdir / "cat.jsonl"
    ingest_mod.ingest(str(src), str(out))
    rows = read_jsonl(out)
    assert rows[0]["device_id"] == "ab-1", f"got {rows[0]['device_id']!r}"


def test_d2_timestamp_whitespace_trimmed(workdir):
    src = workdir / "in.jsonl"
    write_jsonl(src, [{"device_id": "a", "timestamp": "  2026-08-01T00:00:00Z  ", "temp": 22.0}])
    out = workdir / "cat.jsonl"
    ingest_mod.ingest(str(src), str(out))
    rows = read_jsonl(out)
    assert rows[0]["timestamp"] == "2026-08-01T00:00:00Z", f"got {rows[0]['timestamp']!r}"


# D3: legacy temperature fallback on EMPTY temp
def test_d3_legacy_temperature_when_temp_empty(workdir):
    src = workdir / "in.jsonl"
    write_jsonl(src, [{"device_id": "a", "timestamp": "2026-08-01T00:00:00Z", "temp": "", "temperature": 25.5}])
    out = workdir / "cat.jsonl"
    ingest_mod.ingest(str(src), str(out))
    rows = read_jsonl(out)
    assert rows[0]["temp"] == 25.5, f"got {rows[0]['temp']!r}"


# ── D9: deep spec inference (probes even GOLD-matching agents) ───────────────



def test_d9_bom_ndjson(workdir):
    """NDJSON file with UTF-8 BOM: must not corrupt first key."""
    src = workdir / "in.ndjson"
    data = '{"device_id": "a", "timestamp": "2026-08-01T00:00:00Z", "temp": 22.0}'
    src.write_bytes(b"\xef\xbb\xbf" + data.encode("utf-8"))
    out = workdir / "cat.jsonl"
    accepted, skipped = ingest_mod.ingest(str(src), str(out))
    assert accepted == 1 and skipped == 0, f"got ({accepted},{skipped})"
    rows = read_jsonl(out)
    assert rows[0]["device_id"] == "a", f"got {rows[0]['device_id']!r}"


def test_d9_duplicate_device_diff_case_keeps_last(workdir):
    """Dedupe by lowercase key keeps LAST row's ORIGINAL device_id case."""
    src = workdir / "in.jsonl"
    write_jsonl(src, [
        {"device_id": "AB-1", "timestamp": "2026-08-01T00:00:00Z", "temp": 10.0},
        {"device_id": "ab-1", "timestamp": "2026-08-01T00:00:00Z", "temp": 30.0},
    ])
    out = workdir / "t.jsonl"
    kept, _ = transform_mod.transform(str(src), str(out))
    rows = read_jsonl(out)
    assert kept == 1
    assert rows[0]["temp"] == 30.0, f"got {rows[0]['temp']!r}"


def test_d9_filter_numeric_vs_string(workdir):
    """Filter 'temp=20' must match numeric 20.0 (numeric semantics), and
    'device_id=a' must match only exact string."""
    src = workdir / "in.jsonl"
    write_jsonl(src, [
        {"device_id": "a", "timestamp": "2026-08-01T00:00:00Z", "temp": 20.0},
        {"device_id": "a1", "timestamp": "2026-08-01T00:00:01Z", "temp": 20.0},
    ])
    out = workdir / "t.jsonl"
    kept, _ = transform_mod.transform(str(src), str(out), filter_expr="device_id=a")
    rows = read_jsonl(out)
    assert kept == 1 and rows[0]["device_id"] == "a", f"got {rows}"
