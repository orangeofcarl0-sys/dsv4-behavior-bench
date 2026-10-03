"""V5 core: the explicit v2.4 contract.

Every assertion here is traceable to a numbered clause in
spec/ONBOARDING_TODO_v2.4.md (see the provenance tags in each docstring).
These are the "must hold" behaviors a correct v2.4 implementation exhibits.
"""
import json
from pathlib import Path

import pytest

from conftest import (
    ingest_mod, transform_mod, emit_mod, DataError,
    write_jsonl, write_text, read_jsonl, run_cli, assert_clean_data_error,
)


# ── C1: --on-error defaults to skip (backward compatibility) ─────────────────

def test_c1_default_on_error_is_skip(workdir):
    """§4/§6: --on-error defaults to skip; malformed lines are skipped and the
    run still succeeds with exit 0."""
    src = write_text(workdir / "in.ndjson",
                     '{"device_id": "a", "timestamp": "2026-08-01T00:00:00Z", "temp": 22}\n'
                     'NOT-JSON\n'
                     '{"device_id": "b", "timestamp": "2026-08-01T00:00:01Z", "temp": 23}\n')
    r = run_cli(workdir, "ingest", str(src))
    assert r.returncode == 0, r.stderr
    assert "accepted=2" in r.stdout and "skipped=1" in r.stdout, r.stdout


def test_c1_library_default_skips(workdir):
    """§5/§6: ingest(path, out) keeps its two-arg signature and defaults to skip."""
    src = write_text(workdir / "in.ndjson",
                     '{"device_id": "a", "timestamp": "2026-08-01T00:00:00Z", "temp": 22}\n'
                     'oops\n')
    accepted, skipped = ingest_mod.ingest(str(src), str(workdir / "cat.jsonl"))
    assert (accepted, skipped) == (1, 1)


# ── C2: skip is exit 0 even when records were skipped ────────────────────────

def test_c2_skip_nonzero_skipped_still_exit0(workdir):
    """§7: under skip, skipped>0 must NOT change the exit code; success is 0."""
    src = write_jsonl(workdir / "in.jsonl", [
        {"device_id": "a", "timestamp": "2026-08-01T00:00:00Z", "temp": 22},
        {"device_id": "b", "timestamp": "2026-08-01T00:00:01Z", "temp": 999},  # out of range
    ])
    r = run_cli(workdir, "transform", "--input", str(src), "--output",
                str(workdir / "t.jsonl"))
    assert r.returncode == 0, r.stderr
    assert "kept=1" in r.stdout and "skipped=1" in r.stdout, r.stdout


# ── C3: fail raises DataError from the library ───────────────────────────────

def test_c3_fail_raises_data_error(workdir):
    """§6: under fail, the first malformed record raises DataError."""
    src = write_text(workdir / "in.ndjson",
                     '{"device_id": "a", "timestamp": "2026-08-01T00:00:00Z", "temp": 22}\n'
                     'NOT-JSON\n')
    with pytest.raises(DataError):
        ingest_mod.ingest(str(src), str(workdir / "cat.jsonl"), on_error="fail")


def test_c3_transform_fail_raises_data_error(workdir):
    src = write_text(workdir / "in.jsonl", 'NOT-JSON\n')
    with pytest.raises(DataError):
        transform_mod.transform(str(src), str(workdir / "t.jsonl"), on_error="fail")


# ── C4: fail maps to CLI exit 1 (data error, not usage) ──────────────────────

def test_c4_fail_cli_exit1(workdir):
    """§6/§7: fail + malformed record -> exit 1."""
    src = write_text(workdir / "in.ndjson", 'NOT-JSON\n')
    r = run_cli(workdir, "ingest", str(src), "--output", str(workdir / "cat.jsonl"),
                "--on-error", "fail")
    assert_clean_data_error(r)


# ── C5: atomic output — absent stays absent ──────────────────────────────────

def test_c5_atomic_output_absent_stays_absent(workdir):
    """§8: fail with no pre-existing output must not create the file."""
    src = write_text(workdir / "in.ndjson",
                     '{"device_id": "a", "timestamp": "2026-08-01T00:00:00Z", "temp": 22}\n'
                     'BAD\n'
                     '{"device_id": "c", "timestamp": "2026-08-01T00:00:02Z", "temp": 24}\n')
    out = workdir / "cat.jsonl"
    with pytest.raises(DataError):
        ingest_mod.ingest(str(src), str(out), on_error="fail")
    assert not out.exists(), "fail mode left a partial output file"


def test_c5_atomic_transform_output_absent_stays_absent(workdir):
    src = write_text(workdir / "in.jsonl",
                     '{"device_id": "a", "timestamp": "2026-08-01T00:00:00Z", "temp": 22}\n'
                     'BAD\n')
    out = workdir / "t.jsonl"
    with pytest.raises(DataError):
        transform_mod.transform(str(src), str(out), on_error="fail")
    assert not out.exists()


# ── C6: atomic output — existing file keeps its old content ──────────────────

def test_c6_atomic_existing_output_unchanged(workdir):
    """§8: fail must not truncate an existing output."""
    src = write_text(workdir / "in.ndjson",
                     '{"device_id": "a", "timestamp": "2026-08-01T00:00:00Z", "temp": 22}\n'
                     '{"device_id": "b", "timestamp": "2026-08-01T00:00:01Z", "temp": 23}\n'
                     'BAD\n')
    out = workdir / "cat.jsonl"
    out.write_text("OLD CONTENT\n", encoding="utf-8")
    with pytest.raises(DataError):
        ingest_mod.ingest(str(src), str(out), on_error="fail")
    assert out.read_text(encoding="utf-8") == "OLD CONTENT\n"


def test_c6_atomic_emit_output_unchanged(workdir):
    """§8: emit --output is covered by the same atomicity contract."""
    src = write_text(workdir / "in.jsonl",
                     '{"device_id": "a", "timestamp": "2026-08-01T00:00:00Z", "temp": 22}\n'
                     'BAD\n')
    out = workdir / "report.json"
    out.write_text("PREVIOUS\n", encoding="utf-8")
    with pytest.raises(DataError):
        emit_mod.emit(str(src), "json", out_path=str(out), on_error="fail")
    assert out.read_text(encoding="utf-8") == "PREVIOUS\n"


# ── C7: malformed filter is a usage error (exit 2), never a skipped record ───

def test_c7_malformed_filter_exit2(workdir):
    """§7/§9: a malformed filter expression is a usage error -> exit 2."""
    src = write_jsonl(workdir / "in.jsonl", [
        {"device_id": "a", "timestamp": "2026-08-01T00:00:00Z", "temp": 22},
    ])
    r = run_cli(workdir, "transform", "--input", str(src), "--output",
                str(workdir / "t.jsonl"), "--filter", "temp>>20")
    assert r.returncode == 2, (r.returncode, r.stderr)


def test_c7_malformed_filter_raises_value_error(workdir):
    """§5/§9: library surfaces malformed filters as a usage (ValueError) error,
    distinct from DataError."""
    src = write_jsonl(workdir / "in.jsonl", [
        {"device_id": "a", "timestamp": "2026-08-01T00:00:00Z", "temp": 22},
    ])
    with pytest.raises(ValueError) as ei:
        transform_mod.transform(str(src), str(workdir / "t.jsonl"), filter_expr="temp>>20")
    assert not isinstance(ei.value, DataError)


# ── C8: DataError is distinguishable from ValueError ─────────────────────────

def test_c8_data_error_not_value_error(workdir):
    """§5: DataError must NOT subclass ValueError so data vs usage errors are
    separable at the boundary."""
    assert not issubclass(DataError, ValueError)
    assert issubclass(DataError, Exception)


# ── C9: repeated --filter is AND ─────────────────────────────────────────────

def test_c9_multiple_filters_and(workdir):
    """§4/§9: --filter A --filter B keeps only rows satisfying both."""
    src = write_jsonl(workdir / "in.jsonl", [
        {"device_id": "a", "timestamp": "2026-08-01T00:00:00Z", "temp": 25, "humidity": 50},
        {"device_id": "b", "timestamp": "2026-08-01T00:00:01Z", "temp": 25, "humidity": 90},
        {"device_id": "c", "timestamp": "2026-08-01T00:00:02Z", "temp": 10, "humidity": 50},
    ])
    r = run_cli(workdir, "transform", "--input", str(src), "--output",
                str(workdir / "t.jsonl"), "--filter", "temp>=20", "--filter", "humidity<80")
    assert r.returncode == 0, r.stderr
    rows = read_jsonl(workdir / "t.jsonl")
    assert [x["device_id"] for x in rows] == ["a"], rows


def test_c9_library_filters_list_and(workdir):
    """§5: library accepts a `filters` list with the same AND semantics.
    `c` fails the first filter but passes the second, so a last-filter-only
    implementation would wrongly keep it."""
    src = write_jsonl(workdir / "in.jsonl", [
        {"device_id": "a", "timestamp": "2026-08-01T00:00:00Z", "temp": 25, "humidity": 50},
        {"device_id": "b", "timestamp": "2026-08-01T00:00:01Z", "temp": 25, "humidity": 90},
        {"device_id": "c", "timestamp": "2026-08-01T00:00:02Z", "temp": 10, "humidity": 50},
    ])
    kept, _ = transform_mod.transform(str(src), str(workdir / "t.jsonl"),
                                      filters=["temp>=20", "humidity<80"])
    rows = read_jsonl(workdir / "t.jsonl")
    assert kept == 1 and rows[0]["device_id"] == "a", rows


# ── C10: filters run before unit conversion ──────────────────────────────────

def test_c10_filter_before_unit_conversion(workdir):
    """§3: filters compare pre-conversion (celsius) values."""
    src = write_jsonl(workdir / "in.jsonl", [
        {"device_id": "a", "timestamp": "2026-08-01T00:00:00Z", "temp": 20},
        {"device_id": "b", "timestamp": "2026-08-01T00:00:01Z", "temp": 30},
    ])
    kept, _ = transform_mod.transform(str(src), str(workdir / "t.jsonl"),
                                      filter_expr="temp>25", unit="f")
    rows = read_jsonl(workdir / "t.jsonl")
    assert kept == 1 and rows[0]["device_id"] == "b"
    assert abs(rows[0]["temp"] - 86.0) < 1e-9


# ── C11: filters run after dedupe; a filtered-out dup must not resurrect ─────

def test_c11_filter_after_dedupe_no_resurrect(workdir):
    """§3: dedupe keeps the LAST duplicate; if that last value fails the filter
    the earlier duplicate must NOT come back."""
    src = write_jsonl(workdir / "in.jsonl", [
        {"device_id": "a", "timestamp": "2026-08-01T00:00:00Z", "temp": 30},
        {"device_id": "a", "timestamp": "2026-08-01T00:00:00Z", "temp": 10},  # last -> fails
        {"device_id": "b", "timestamp": "2026-08-01T00:00:01Z", "temp": 40},
    ])
    kept, _ = transform_mod.transform(str(src), str(workdir / "t.jsonl"),
                                      filter_expr="temp>20")
    rows = read_jsonl(workdir / "t.jsonl")
    assert kept == 1 and rows[0]["device_id"] == "b", rows


# ── C12: emit --output honors the fail contract ──────────────────────────────

def test_c12_emit_fail_absent_stays_absent(workdir):
    src = write_text(workdir / "in.jsonl",
                     '{"device_id": "a", "timestamp": "2026-08-01T00:00:00Z", "temp": 22}\n'
                     'BAD\n')
    out = workdir / "report.json"
    r = run_cli(workdir, "emit", "--input", str(src), "--format", "json",
                "--output", str(out), "--on-error", "fail")
    assert_clean_data_error(r)
    assert not out.exists()


# ── C13: filter_expr and filters merge (backward compat + new) ───────────────

def test_c13_filter_expr_and_filters_merge(workdir):
    """§5: filter_expr is equivalent to filters=[filter_expr]; both combine."""
    src = write_jsonl(workdir / "in.jsonl", [
        {"device_id": "a", "timestamp": "2026-08-01T00:00:00Z", "temp": 25, "humidity": 50},
        {"device_id": "b", "timestamp": "2026-08-01T00:00:01Z", "temp": 25, "humidity": 90},
    ])
    kept, _ = transform_mod.transform(str(src), str(workdir / "t.jsonl"),
                                      filter_expr="temp>=20",
                                      filters=["humidity<80"])
    assert kept == 1
    rows = read_jsonl(workdir / "t.jsonl")
    assert rows[0]["device_id"] == "a"
