"""V5 adversarial: error classification, atomicity, and representation edges.

These target the failure modes a plausible-but-wrong implementation exhibits:
swallowing bugs with a broad `except`, miscounting skipped records, writing
partial output, or conflating data vs usage errors.
"""
import json
from pathlib import Path

import pytest

from conftest import (
    ingest_mod, transform_mod, emit_mod, DataError,
    write_jsonl, write_text, write_csv, read_jsonl, run_cli, assert_clean_data_error,
)


# ── A1: skip counts exactly the malformed records, valid rows preserved ──────

def test_a1_skip_count_and_valid_rows(workdir):
    """§6: skip counts each bad record once; every valid record survives."""
    src = write_text(workdir / "in.ndjson",
                     '{"device_id": "a", "timestamp": "2026-08-01T00:00:00Z", "temp": 22}\n'
                     '{broken}\n'
                     '{"device_id": "b", "timestamp": "2026-08-01T00:00:01Z", "temp": 23}\n'
                     '{"device_id": "c", "timestamp": "2026-08-01T00:00:02Z"\n'  # truncated
                     '{"device_id": "d", "timestamp": "2026-08-01T00:00:03Z", "temp": 24}\n')
    accepted, skipped = ingest_mod.ingest(str(src), str(workdir / "cat.jsonl"))
    assert (accepted, skipped) == (3, 2), (accepted, skipped)
    assert [r["device_id"] for r in read_jsonl(workdir / "cat.jsonl")] == ["a", "b", "d"]


# ── A2: fail stops at the FIRST bad record (no partial rows written) ─────────

def test_a2_fail_stops_at_first_bad(workdir):
    """§6: fail raises at the first malformed record; nothing is written."""
    src = write_text(workdir / "in.ndjson",
                     '{"device_id": "a", "timestamp": "2026-08-01T00:00:00Z", "temp": 22}\n'
                     '{"device_id": "b", "timestamp": "2026-08-01T00:00:01Z", "temp": 23}\n'
                     'BAD\n'
                     '{"device_id": "d", "timestamp": "2026-08-01T00:00:03Z", "temp": 24}\n')
    out = workdir / "cat.jsonl"
    with pytest.raises(DataError):
        ingest_mod.ingest(str(src), str(out), on_error="fail")
    assert not out.exists()


# ── A3: fail and skip are duals — every record skip drops, fail stops on ─────

def test_a3_fail_skip_duality_missing_fields(workdir):
    """§6: records skip drops for missing required fields are exactly the ones
    fail stops on (not just unparseable JSON)."""
    rows = [
        {"device_id": "", "timestamp": "2026-08-01T00:00:00Z", "temp": 22},   # missing id
        {"device_id": "b", "temp": 23},                                        # missing ts
    ]
    src = write_jsonl(workdir / "in.jsonl", rows)
    accepted, skipped = ingest_mod.ingest(str(src), str(workdir / "s.jsonl"))
    assert (accepted, skipped) == (0, 2), (accepted, skipped)
    with pytest.raises(DataError):
        ingest_mod.ingest(str(src), str(workdir / "f.jsonl"), on_error="fail")
    assert not (workdir / "f.jsonl").exists()


def test_a3_fail_skip_duality_unparseable_ts(workdir):
    """§6: an unparseable timestamp is a record-level data error under fail."""
    src = write_jsonl(workdir / "in.jsonl", [
        {"device_id": "a", "timestamp": "not-a-time", "temp": 22},
    ])
    kept, skipped = transform_mod.transform(str(src), str(workdir / "s.jsonl"))
    assert (kept, skipped) == (0, 1)
    with pytest.raises(DataError):
        transform_mod.transform(str(src), str(workdir / "f.jsonl"), on_error="fail")
    assert not (workdir / "f.jsonl").exists()


def test_a3_fail_skip_duality_out_of_range(workdir):
    """§6: an out-of-range value is a record-level data error under fail."""
    src = write_jsonl(workdir / "in.jsonl", [
        {"device_id": "a", "timestamp": "2026-08-01T00:00:00Z", "temp": 999},
    ])
    kept, skipped = transform_mod.transform(str(src), str(workdir / "s.jsonl"))
    assert (kept, skipped) == (0, 1)
    with pytest.raises(DataError):
        transform_mod.transform(str(src), str(workdir / "f.jsonl"), on_error="fail")
    assert not (workdir / "f.jsonl").exists()


# ── A4: non-object records are malformed (skip counts, fail stops) ───────────

def test_a4_non_object_record_malformed(workdir):
    """§10: a non-object record is malformed, not silently kept."""
    src = write_text(workdir / "in.ndjson",
                     '[1, 2, 3]\n'
                     '{"device_id": "a", "timestamp": "2026-08-01T00:00:00Z", "temp": 22}\n')
    accepted, skipped = ingest_mod.ingest(str(src), str(workdir / "cat.jsonl"))
    assert (accepted, skipped) == (1, 1), (accepted, skipped)


# ── A5: non-numeric temp/humidity is NOT malformed (row kept, null) ──────────

def test_a5_nonnumeric_metric_row_kept_null(workdir):
    """§6/§10: unparseable metric values are normalized to null, not skipped."""
    src = write_jsonl(workdir / "in.jsonl", [
        {"device_id": "a", "timestamp": "2026-08-01T00:00:00Z", "temp": "abc", "humidity": "n/a"},
    ])
    accepted, skipped = ingest_mod.ingest(str(src), str(workdir / "cat.jsonl"))
    assert (accepted, skipped) == (1, 0)
    row = read_jsonl(workdir / "cat.jsonl")[0]
    assert row["temp"] is None and row["humidity"] is None


def test_a5_bool_temp_not_numeric(workdir):
    """§10: JSON booleans are not numbers -> null."""
    src = write_jsonl(workdir / "in.jsonl", [
        {"device_id": "a", "timestamp": "2026-08-01T00:00:00Z", "temp": True},
    ])
    ingest_mod.ingest(str(src), str(workdir / "cat.jsonl"))
    assert read_jsonl(workdir / "cat.jsonl")[0]["temp"] is None


# ── A6: legacy temperature fallback — 0 vs empty vs null vs bool ─────────────

def test_a6_temp_zero_does_not_fall_back(workdir):
    """§10: temp=0 is a real value; it must NOT fall back to `temperature`."""
    src = write_jsonl(workdir / "in.jsonl", [
        {"device_id": "a", "timestamp": "2026-08-01T00:00:00Z", "temp": 0, "temperature": 25},
    ])
    ingest_mod.ingest(str(src), str(workdir / "cat.jsonl"))
    assert read_jsonl(workdir / "cat.jsonl")[0]["temp"] == 0.0


def test_a6_temp_empty_falls_back(workdir):
    """§10: temp="" falls back to `temperature`."""
    src = write_jsonl(workdir / "in.jsonl", [
        {"device_id": "a", "timestamp": "2026-08-01T00:00:00Z", "temp": "", "temperature": 25},
    ])
    ingest_mod.ingest(str(src), str(workdir / "cat.jsonl"))
    assert read_jsonl(workdir / "cat.jsonl")[0]["temp"] == 25.0


def test_a6_temp_null_falls_back(workdir):
    """§10: temp=null falls back to `temperature`."""
    src = write_jsonl(workdir / "in.jsonl", [
        {"device_id": "a", "timestamp": "2026-08-01T00:00:00Z", "temp": None, "temperature": 25},
    ])
    ingest_mod.ingest(str(src), str(workdir / "cat.jsonl"))
    assert read_jsonl(workdir / "cat.jsonl")[0]["temp"] == 25.0


def test_a6_temp_bool_does_not_fall_back(workdir):
    """§10: temp=false is present (not missing) -> null, no fallback."""
    src = write_jsonl(workdir / "in.jsonl", [
        {"device_id": "a", "timestamp": "2026-08-01T00:00:00Z", "temp": False, "temperature": 25},
    ])
    ingest_mod.ingest(str(src), str(workdir / "cat.jsonl"))
    assert read_jsonl(workdir / "cat.jsonl")[0]["temp"] is None


# ── A7: bad flag value is a usage error (exit 2) ─────────────────────────────

def test_a7_invalid_on_error_exit2(workdir):
    """§7: an invalid --on-error value is a usage error -> exit 2."""
    src = write_jsonl(workdir / "in.jsonl", [
        {"device_id": "a", "timestamp": "2026-08-01T00:00:00Z", "temp": 22},
    ])
    r = run_cli(workdir, "transform", "--input", str(src), "--on-error", "bogus")
    assert r.returncode == 2, (r.returncode, r.stderr)


def test_a7_bad_format_exit2(workdir):
    r = run_cli(workdir, "emit", "--format", "xml")
    assert r.returncode == 2


# ── A8: a broad `except Exception` must not turn a real bug into a skip ──────

def test_a8_program_error_not_swallowed(workdir):
    """§6/§12: a malformed FILTER is a usage error, not a record to skip; it must
    surface as exit 2 even when there are bad records present too."""
    src = write_text(workdir / "in.jsonl", 'BAD\n')
    r = run_cli(workdir, "transform", "--input", str(src), "--output",
                str(workdir / "t.jsonl"), "--filter", "temp>")
    assert r.returncode == 2, (r.returncode, r.stderr, r.stdout)


# ── A9: atomicity under fail for transform with pre-existing output ──────────

def test_a9_transform_fail_preserves_existing(workdir):
    """§8: transform fail leaves the previous transformed.jsonl intact."""
    src = write_text(workdir / "in.jsonl",
                     '{"device_id": "a", "timestamp": "2026-08-01T00:00:00Z", "temp": 22}\n'
                     'BAD\n')
    out = workdir / "t.jsonl"
    out.write_text('{"old": true}\n', encoding="utf-8")
    r = run_cli(workdir, "transform", "--input", str(src), "--output", str(out),
                "--on-error", "fail")
    assert_clean_data_error(r)
    assert out.read_text(encoding="utf-8") == '{"old": true}\n'


# ── A10: library and CLI agree on the same data error ───────────────────────

def test_a10_library_cli_agree(workdir):
    """§5: same input, same on_error -> library raises and CLI exits 1; under
    skip both succeed and report the same skipped count."""
    src = write_text(workdir / "in.ndjson",
                     '{"device_id": "a", "timestamp": "2026-08-01T00:00:00Z", "temp": 22}\n'
                     'BAD\n'
                     '{"device_id": "b", "timestamp": "2026-08-01T00:00:01Z", "temp": 23}\n')
    # skip: library and CLI agree on 1 skipped, 2 accepted
    acc, sk = ingest_mod.ingest(str(src), str(workdir / "lib.jsonl"), on_error="skip")
    assert (acc, sk) == (2, 1)
    r = run_cli(workdir, "ingest", str(src), "--output", str(workdir / "cli.jsonl"),
                "--on-error", "skip")
    assert r.returncode == 0
    assert "accepted=2" in r.stdout and "skipped=1" in r.stdout
    assert read_jsonl(workdir / "lib.jsonl") == read_jsonl(workdir / "cli.jsonl")
    # fail: library raises, CLI exits 1
    with pytest.raises(DataError):
        ingest_mod.ingest(str(src), str(workdir / "lib2.jsonl"), on_error="fail")
    r2 = run_cli(workdir, "ingest", str(src), "--output", str(workdir / "cli2.jsonl"),
                 "--on-error", "fail")
    assert r2.returncode == 1
    assert not (workdir / "cli2.jsonl").exists()


# ── A11: emit fail counts malformed lines as data errors (not skipped) ───────

def test_a11_emit_fail_on_malformed(workdir):
    src = write_text(workdir / "in.jsonl",
                     '{"device_id": "a", "timestamp": "2026-08-01T00:00:00Z", "temp": 22}\n'
                     '{oops}\n')
    with pytest.raises(DataError):
        emit_mod.emit(str(src), "json", on_error="fail")
    # skip still tolerates it
    text, stats = emit_mod.emit(str(src), "json", on_error="skip")
    assert stats["count"] == 1


# ── A12: skipped counter is not double-counted across dedupe/validation ──────

def test_a12_skipped_not_double_counted(workdir):
    """§6: skipped reflects malformed/invalid records once each, not inflated by
    downstream stages."""
    src = write_jsonl(workdir / "in.jsonl", [
        {"device_id": "a", "timestamp": "2026-08-01T00:00:00Z", "temp": 999},  # 1 skip
        {"device_id": "b", "timestamp": "bad-time", "temp": 20},               # 1 skip
        {"device_id": "c", "timestamp": "2026-08-01T00:00:02Z", "temp": 20},   # kept
    ])
    kept, skipped = transform_mod.transform(str(src), str(workdir / "t.jsonl"))
    assert (kept, skipped) == (1, 2), (kept, skipped)


# ── A13: non-finite metrics are record-level invalid, never null ─────────────

def test_a13_non_finite_metrics_rejected(workdir):
    """§6/§10 (v2.4.1): NaN / ±Infinity are not valid numbers. They are
    record-level invalid -- skipped and counted, never normalized to null and
    kept. Same input under fail stops with DataError and leaves no output."""
    src = write_jsonl(workdir / "in.jsonl", [
        {"device_id": "a", "timestamp": "2026-08-01T00:00:00Z", "temp": "nan"},
        {"device_id": "b", "timestamp": "2026-08-01T00:00:01Z", "temp": "inf"},
        {"device_id": "c", "timestamp": "2026-08-01T00:00:02Z", "temp": "-inf"},
        {"device_id": "d", "timestamp": "2026-08-01T00:00:03Z", "humidity": "nan"},
        {"device_id": "e", "timestamp": "2026-08-01T00:00:04Z", "temp": 20},
    ])
    out = workdir / "t.jsonl"
    kept, skipped = transform_mod.transform(str(src), str(out))
    rows = read_jsonl(out)
    assert (kept, skipped) == (1, 4), (kept, skipped, rows)
    assert rows[0]["device_id"] == "e" and rows[0]["temp"] == 20.0, rows

    with pytest.raises(DataError):
        transform_mod.transform(str(src), str(workdir / "fail.jsonl"), on_error="fail")
    assert not (workdir / "fail.jsonl").exists()


def test_a14_non_finite_not_nulled_by_ingest(workdir):
    """§10 (v2.4.1): the full ingest -> transform chain must not turn a
    non-finite metric into `null` and keep the row (observed real-model failure
    mode); the record must be gone from the cleaned output either way."""
    src = write_jsonl(workdir / "in.jsonl", [
        {"device_id": "a", "timestamp": "2026-08-01T00:00:00Z", "temp": "nan"},
        {"device_id": "b", "timestamp": "2026-08-01T00:00:01Z", "temp": 20},
    ])
    cat = workdir / "cat.jsonl"
    ingest_mod.ingest(str(src), str(cat))
    tr = workdir / "tr.jsonl"
    kept, _ = transform_mod.transform(str(cat), str(tr))
    rows = read_jsonl(tr)
    assert kept == 1 and rows[0]["device_id"] == "b", rows
    assert all(r.get("temp") is not None for r in rows), rows
