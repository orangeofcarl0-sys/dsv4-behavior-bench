"""V4 discriminative core: every test MUST separate GOLD from weak agents.

Design: each test targets one behavior that GOLD implements but some
agents omit (verified against real agent outputs). Tests that pass for
everyone are excluded by construction.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

from conftest import read_jsonl, write_jsonl, ingest_mod, transform_mod, emit_mod


# ── D1: NDJSON robustness (GOLD: per-line try/except, counts malformed) ──────

def test_d1_ndjson_malformed_line_skipped(workdir):
    """A malformed line must be skipped+counted; valid lines still ingested."""
    src = workdir / "in.ndjson"
    src.write_text(
        '{"device_id": "a", "timestamp": "2026-08-01T00:00:00Z", "temp": 22.0}\n'
        'NOT-JSON\n'
        '{"device_id": "b", "timestamp": "2026-08-01T00:00:01Z", "temp": 23.0}\n',
        encoding="utf-8",
    )
    out = workdir / "cat.jsonl"
    accepted, skipped = ingest_mod.ingest(str(src), str(out))
    assert accepted == 2, f"got accepted={accepted}"
    assert skipped == 1, f"got skipped={skipped}"


def test_d1_ndjson_truncated_line_skipped(workdir):
    """A truncated JSON line (unclosed brace) must be skipped, not crash."""
    src = workdir / "in.ndjson"
    src.write_text(
        '{"device_id": "a", "timestamp": "2026-08-01T00:00:00Z", "temp": 22.0}\n'
        '{"device_id": "b", "timestamp": "2026-08-01T00:00:01Z"\n'
        '{"device_id": "c", "timestamp": "2026-08-01T00:00:02Z", "temp": 24.0}\n',
        encoding="utf-8",
    )
    out = workdir / "cat.jsonl"
    accepted, skipped = ingest_mod.ingest(str(src), str(out))
    assert accepted == 2, f"got accepted={accepted}"
    assert skipped == 1, f"got skipped={skipped}"


# ── D2: field trimming (GOLD: str().strip() on device_id/timestamp) ─────────

def test_d2_device_id_whitespace_trimmed(workdir):
    src = workdir / "in.jsonl"
    write_jsonl(src, [{"device_id": "  ab-1  ", "timestamp": "2026-08-01T00:00:00Z", "temp": 22.0}])
    out = workdir / "cat.jsonl"
    accepted, _ = ingest_mod.ingest(str(src), str(out))
    rows = read_jsonl(out)
    assert rows[0]["device_id"] == "ab-1", f"got {rows[0]['device_id']!r}"


def test_d2_timestamp_whitespace_trimmed(workdir):
    src = workdir / "in.jsonl"
    write_jsonl(src, [{"device_id": "a", "timestamp": "  2026-08-01T00:00:00Z  ", "temp": 22.0}])
    out = workdir / "cat.jsonl"
    accepted, _ = ingest_mod.ingest(str(src), str(out))
    rows = read_jsonl(out)
    assert rows[0]["timestamp"] == "2026-08-01T00:00:00Z", f"got {rows[0]['timestamp']!r}"


# ── D3: legacy field normalization (GOLD: empty temp falls back to temperature) ──

def test_d3_legacy_temperature_when_temp_empty(workdir):
    """Spec: 'temperature' legacy name normalizes to temp. GOLD also falls
    back when temp is an EMPTY STRING, not just None."""
    src = workdir / "in.jsonl"
    write_jsonl(src, [{"device_id": "a", "timestamp": "2026-08-01T00:00:00Z", "temp": "", "temperature": 25.5}])
    out = workdir / "cat.jsonl"
    accepted, _ = ingest_mod.ingest(str(src), str(out))
    rows = read_jsonl(out)
    assert rows[0]["temp"] == 25.5, f"got {rows[0]['temp']!r}"


# ── D4: extensionless content sniffing (GOLD-only _read_rows) ────────────────

def test_d4_extless_json_object_sniffed(workdir):
    src = workdir / "data.raw"
    src.write_text(json.dumps({"device_id": "a", "timestamp": "2026-08-01T00:00:00Z", "temp": 22.0}), encoding="utf-8")
    out = workdir / "cat.jsonl"
    accepted, skipped = ingest_mod.ingest(str(src), str(out))
    assert accepted == 1 and skipped == 0, f"got ({accepted},{skipped})"


def test_d4_extless_json_array_sniffed(workdir):
    src = workdir / "data.raw"
    src.write_text(json.dumps([{"device_id": "a", "timestamp": "2026-08-01T00:00:00Z", "temp": 22.0}]), encoding="utf-8")
    out = workdir / "cat.jsonl"
    accepted, skipped = ingest_mod.ingest(str(src), str(out))
    assert accepted == 1 and skipped == 0, f"got ({accepted},{skipped})"


# ── D5: non-numeric temp -> null, row kept (GOLD: _to_number) ────────────────

def test_d5_nonnumeric_temp_null_row_kept(workdir):
    src = workdir / "in.jsonl"
    write_jsonl(src, [{"device_id": "a", "timestamp": "2026-08-01T00:00:00Z", "temp": "abc"}])
    out = workdir / "cat.jsonl"
    accepted, skipped = ingest_mod.ingest(str(src), str(out))
    assert accepted == 1 and skipped == 0, f"got ({accepted},{skipped})"
    rows = read_jsonl(out)
    assert rows[0]["temp"] is None


def test_d5_nonnumeric_humidity_null_row_kept(workdir):
    src = workdir / "in.jsonl"
    write_jsonl(src, [{"device_id": "a", "timestamp": "2026-08-01T00:00:00Z", "temp": 22.0, "humidity": "n/a"}])
    out = workdir / "cat.jsonl"
    accepted, skipped = ingest_mod.ingest(str(src), str(out))
    assert accepted == 1 and skipped == 0, f"got ({accepted},{skipped})"
    rows = read_jsonl(out)
    assert rows[0]["humidity"] is None


# ── D6: transform order semantics (dedupe->filter->unit) ─────────────────────

def test_d6_dedupe_then_filter(workdir):
    """Duplicate key with different temps: LAST wins, then filter applies."""
    src = workdir / "in.jsonl"
    write_jsonl(src, [
        {"device_id": "AB-1", "timestamp": "2026-08-01T00:00:00Z", "temp": 10.0},
        {"device_id": "ab-1", "timestamp": "2026-08-01T00:00:00Z", "temp": 30.0},
    ])
    out = workdir / "t.jsonl"
    kept, _ = transform_mod.transform(str(src), str(out), filter_expr="temp>20")
    rows = read_jsonl(out)
    assert kept == 1
    assert rows[0]["temp"] == 30.0, f"got {rows[0]['temp']!r} (must keep LAST after lowercase-dedupe)"


def test_d6_unit_after_filter(workdir):
    """Filter compares ORIGINAL celsius; unit=f converts AFTER filtering."""
    src = workdir / "in.jsonl"
    write_jsonl(src, [
        {"device_id": "a", "timestamp": "2026-08-01T00:00:00Z", "temp": 20.0},
        {"device_id": "b", "timestamp": "2026-08-01T00:01:00Z", "temp": 30.0},
    ])
    out = workdir / "t.jsonl"
    kept, _ = transform_mod.transform(str(src), str(out), filter_expr="temp>25", unit="f")
    rows = read_jsonl(out)
    assert kept == 1
    assert rows[0]["device_id"] == "b"
    assert abs(rows[0]["temp"] - 86.0) < 1e-9


# ── D7: emit semantics ───────────────────────────────────────────────────────

def test_d7_md_mean_arithmetic(workdir):
    src = workdir / "in.jsonl"
    write_jsonl(src, [
        {"device_id": "a", "timestamp": "2026-08-01T00:00:00Z", "temp": 10.0},
        {"device_id": "b", "timestamp": "2026-08-01T00:01:00Z", "temp": 20.0},
        {"device_id": "c", "timestamp": "2026-08-01T00:02:00Z", "temp": 60.0},
    ])
    text, _ = emit_mod.emit(str(src), "md")
    assert "- mean: 30.0" in text, [l for l in text.splitlines() if "mean" in l]


def test_d7_csv_quotes_comma_field(workdir):
    src = workdir / "in.jsonl"
    write_jsonl(src, [{"device_id": "a,1", "timestamp": "2026-08-01T00:00:00Z", "temp": 22.0}])
    text, _ = emit_mod.emit(str(src), "csv")
    assert '"a,1"' in text


# ── D8: CLI contract ─────────────────────────────────────────────────────────

def test_d8_cli_missing_input_exit1(workdir):
    r = run_cli(workdir, "ingest", str(workdir / "nope.csv"))
    assert r.returncode == 1, f"got {r.returncode}"


def test_d8_cli_output_flag_writes_file(workdir):
    src = workdir / "in.jsonl"
    write_jsonl(src, [{"device_id": "a", "timestamp": "2026-08-01T00:00:00Z", "temp": 22.0}])
    r = run_cli(workdir, "emit", "--input", str(src), "--format", "json", "--output", str(workdir / "out.json"))
    assert r.returncode == 0, r.stderr
    assert (workdir / "out.json").exists()


def test_d8_cli_summary_flag(workdir):
    src = workdir / "in.jsonl"
    write_jsonl(src, [{"device_id": "a", "timestamp": "2026-08-01T00:00:00Z", "temp": 22.0}])
    r = run_cli(workdir, "emit", "--input", str(src), "--format", "json", "--summary")
    assert r.returncode == 0, r.stderr
    assert "summary" in r.stdout


def run_cli(workdir, *args):
    env = dict(os.environ)
    repo = os.environ.get("DATAPIPE_REPO", "")
    env["PYTHONPATH"] = repo + os.pathsep + env.get("PYTHONPATH", "")
    return subprocess.run(
        [sys.executable, "-m", "datapipe.cli", *args],
        cwd=str(workdir), env=env, capture_output=True, text=True, timeout=60,
    )
