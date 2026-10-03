"""V5 interaction: cross-module consistency and operator ordering.

These tests deliberately combine several contract clauses at once (the
"non-local" behaviors from the design doc §6). Each test names the clauses it
composes. A model that only implemented isolated features fails here even when
every core clause passes in isolation.
"""
import json
from pathlib import Path

from conftest import (
    ingest_mod, transform_mod, emit_mod,
    write_jsonl, write_text, write_csv, read_jsonl, run_cli,
)


# ── I1: timezone + microseconds + case-insensitive dedupe + keep-last ─────────

def test_i1_tz_micros_case_dedupe_keep_last(workdir):
    """Composes: offset normalization, microsecond preservation, lowercase
    dedupe key, same-instant collapse, keep-LAST (design §6 example)."""
    src = write_jsonl(workdir / "in.jsonl", [
        {"device_id": "AB-1", "timestamp": "2026-08-01T02:00:00.123456+08:00", "temp": 20},
        {"device_id": "ab-1", "timestamp": "2026-07-31T18:00:00.123456Z", "temp": 30},
    ])
    kept, _ = transform_mod.transform(str(src), str(workdir / "t.jsonl"))
    rows = read_jsonl(workdir / "t.jsonl")
    assert kept == 1, f"same instant must collapse, got {kept}: {rows}"
    assert rows[0]["timestamp"] == "2026-07-31T18:00:00.123456Z", rows[0]["timestamp"]
    assert rows[0]["temp"] == 30.0, "must keep LAST value across the collapsed key"


# ── I2: dedupe + repeated filters + unit conversion ordering ─────────────────

def test_i2_dedupe_filters_unit_ordering(workdir):
    """Composes: validation-before-dedupe, dedupe keep-last, AND filters on
    canonical celsius, unit conversion last."""
    src = write_jsonl(workdir / "in.jsonl", [
        # a: dup key; last value 10C fails temp>=20 -> 'a' disappears entirely
        {"device_id": "a", "timestamp": "2026-08-01T00:00:00Z", "temp": 50, "humidity": 40},
        {"device_id": "a", "timestamp": "2026-08-01T00:00:00Z", "temp": 10, "humidity": 40},
        # b: passes both filters
        {"device_id": "b", "timestamp": "2026-08-01T00:01:00Z", "temp": 30, "humidity": 50},
        # c: temp ok but humidity fails second filter
        {"device_id": "c", "timestamp": "2026-08-01T00:02:00Z", "temp": 30, "humidity": 95},
    ])
    kept, _ = transform_mod.transform(
        str(src), str(workdir / "t.jsonl"),
        filters=["temp>=20", "humidity<80"], unit="f",
    )
    rows = read_jsonl(workdir / "t.jsonl")
    assert kept == 1 and rows[0]["device_id"] == "b", rows
    assert abs(rows[0]["temp"] - 86.0) < 1e-9, rows[0]["temp"]


# ── I3: validation happens before dedupe (out-of-range last dup, no fallback) ─

def test_i3_validation_before_dedupe(workdir):
    """Composes: range validation THEN dedupe (frozen order). The out-of-range
    LAST duplicate is dropped as invalid before dedupe runs, so the earlier
    in-range duplicate survives and is kept. An implementation that deduped
    first would keep the 999 and then drop the whole key (kept=0)."""
    src = write_jsonl(workdir / "in.jsonl", [
        {"device_id": "a", "timestamp": "2026-08-01T00:00:00Z", "temp": 20},
        {"device_id": "a", "timestamp": "2026-08-01T00:00:00Z", "temp": 999},  # invalid last
    ])
    kept, skipped = transform_mod.transform(str(src), str(workdir / "t.jsonl"))
    rows = read_jsonl(workdir / "t.jsonl")
    assert (kept, skipped) == (1, 1), (kept, skipped, rows)
    assert rows[0]["temp"] == 20.0, rows


# ── I4: ingest legacy field + transform dedupe + emit stats end-to-end ───────

def test_i4_ingest_legacy_then_transform_emit(workdir):
    """Composes: legacy `temperature` fallback at ingest, dedupe/keep-last at
    transform, stats at emit — across all three modules."""
    src = write_jsonl(workdir / "in.jsonl", [
        {"device_id": "a", "timestamp": "2026-08-01T00:00:00Z", "temperature": 20},
        {"device_id": "a", "timestamp": "2026-08-01T00:00:00Z", "temperature": 30},
    ])
    cat = workdir / "cat.jsonl"
    accepted, _ = ingest_mod.ingest(str(src), str(cat))
    assert accepted == 2
    assert read_jsonl(cat)[0]["temp"] == 20.0

    tr = workdir / "tr.jsonl"
    kept, _ = transform_mod.transform(str(cat), str(tr))
    assert kept == 1
    assert read_jsonl(tr)[0]["temp"] == 30.0

    text, stats = emit_mod.emit(str(tr), "json")
    assert stats["count"] == 1 and stats["mean"] == 30.0


# ── I5: full CLI chain with filters + unit + summary ─────────────────────────

def test_i5_cli_full_chain(workdir):
    """Composes: ingest (CSV) -> transform (2 filters + unit) -> emit (json,
    summary), verifying exit codes and the final stats."""
    src = write_csv(workdir / "in.csv", [
        {"device_id": "a", "timestamp": "2026-08-01T00:00:00Z", "temp": "20", "humidity": "45"},
        {"device_id": "b", "timestamp": "2026-08-01T00:00:01Z", "temp": "30", "humidity": "50"},
        {"device_id": "c", "timestamp": "2026-08-01T00:00:02Z", "temp": "30", "humidity": "95"},
    ])
    r1 = run_cli(workdir, "ingest", str(src), "--output", str(workdir / "cat.jsonl"))
    assert r1.returncode == 0, r1.stderr
    r2 = run_cli(workdir, "transform", "--input", str(workdir / "cat.jsonl"),
                 "--output", str(workdir / "tr.jsonl"),
                 "--filter", "temp>=25", "--filter", "humidity<80", "--unit", "f")
    assert r2.returncode == 0, r2.stderr
    r3 = run_cli(workdir, "emit", "--input", str(workdir / "tr.jsonl"),
                 "--format", "json", "--summary")
    assert r3.returncode == 0, r3.stderr
    doc = json.loads(r3.stdout)
    assert doc["stats"]["count"] == 1
    assert abs(doc["stats"]["mean"] - 86.0) < 1e-9
    assert "summary" in doc


# ── I6: CSV roundtrip through emit -> ingest preserves canonical records ─────

def test_i6_csv_roundtrip_preserves_records(workdir):
    """Composes: emit(csv) then ingest(csv) yields equivalent canonical rows."""
    rows = [
        {"device_id": "ab,1", "timestamp": "2026-08-01T00:00:00Z", "temp": 22.5, "humidity": 45},
        {"device_id": "cd-2", "timestamp": "2026-08-01T00:01:00Z", "temp": 23.0, "humidity": None},
    ]
    src = write_jsonl(workdir / "in.jsonl", rows)
    csv_text, _ = emit_mod.emit(str(src), "csv")
    csv_path = write_text(workdir / "out.csv", csv_text)
    cat = workdir / "cat.jsonl"
    accepted, _ = ingest_mod.ingest(str(csv_path), str(cat))
    out = read_jsonl(cat)
    assert accepted == 2
    assert out[0]["device_id"] == "ab,1"
    assert abs(out[0]["temp"] - 22.5) < 1e-9
    assert out[1]["humidity"] is None


# ── I7: mixed on-error across a chain (skip at ingest, fail at transform) ────

def test_i7_mixed_on_error_chain(workdir):
    """Composes: ingest --on-error skip (bad line dropped) then transform
    --on-error fail on the now-clean catalog succeeds."""
    src = write_text(workdir / "in.ndjson",
                     '{"device_id": "a", "timestamp": "2026-08-01T00:00:00Z", "temp": 22}\n'
                     'BAD\n'
                     '{"device_id": "b", "timestamp": "2026-08-01T00:00:01Z", "temp": 23}\n')
    r1 = run_cli(workdir, "ingest", str(src), "--output", str(workdir / "cat.jsonl"),
                 "--on-error", "skip")
    assert r1.returncode == 0, r1.stderr
    r2 = run_cli(workdir, "transform", "--input", str(workdir / "cat.jsonl"),
                 "--output", str(workdir / "tr.jsonl"), "--on-error", "fail")
    assert r2.returncode == 0, r2.stderr
    assert len(read_jsonl(workdir / "tr.jsonl")) == 2


# ── I8: on-error=fail on a clean input still succeeds and writes output ──────

def test_i8_fail_on_clean_input_succeeds(workdir):
    """Composes: fail mode is not 'fail always' — clean input writes normally."""
    src = write_jsonl(workdir / "in.jsonl", [
        {"device_id": "a", "timestamp": "2026-08-01T00:00:00Z", "temp": 22},
        {"device_id": "b", "timestamp": "2026-08-01T00:00:01Z", "temp": 23},
    ])
    r = run_cli(workdir, "transform", "--input", str(src), "--output",
                str(workdir / "t.jsonl"), "--on-error", "fail")
    assert r.returncode == 0, r.stderr
    assert len(read_jsonl(workdir / "t.jsonl")) == 2
