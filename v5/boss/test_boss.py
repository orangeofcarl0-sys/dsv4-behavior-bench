"""V5 boss: high-information-density end-to-end composite scenarios.

Each boss case composes many contract clauses into one realistic pipeline run
(design §7). They are not weighted higher per se; they exist to test global
consistency. Every rule they exercise is stated in the frozen v2.4 spec.
"""
import json
from pathlib import Path

import pytest

from conftest import (
    ingest_mod, transform_mod, emit_mod,
    write_jsonl, write_text, write_bytes, write_csv, read_jsonl, run_cli,
    assert_clean_data_error,
)


# ── B1: NDJSON malformed + skip + skipped count + valid rows preserved ───────

def test_b1_ndjson_skip_preserves_valid(workdir):
    src = write_text(workdir / "in.ndjson",
                     '{"device_id": "a", "timestamp": "2026-08-01T00:00:00Z", "temp": 22}\n'
                     '{broken}\n'
                     '{"device_id": "b", "timestamp": "2026-08-01T00:00:01Z", "temp": 23}\n'
                     '{"device_id": "c", "timestamp": "2026-08-01T00:00:02Z", "temp": 24}\n')
    accepted, skipped = ingest_mod.ingest(str(src), str(workdir / "cat.jsonl"))
    assert (accepted, skipped) == (3, 1)
    assert [r["device_id"] for r in read_jsonl(workdir / "cat.jsonl")] == ["a", "b", "c"]


# ── B2: same input + fail + exit 1 + atomic output ───────────────────────────

def test_b2_ndjson_fail_exit1_atomic(workdir):
    src = write_text(workdir / "in.ndjson",
                     '{"device_id": "a", "timestamp": "2026-08-01T00:00:00Z", "temp": 22}\n'
                     '{"device_id": "b", "timestamp": "2026-08-01T00:00:01Z", "temp": 23}\n'
                     '{broken}\n'
                     '{"device_id": "d", "timestamp": "2026-08-01T00:00:03Z", "temp": 24}\n')
    out = workdir / "cat.jsonl"
    r = run_cli(workdir, "ingest", str(src), "--output", str(out), "--on-error", "fail")
    assert_clean_data_error(r)
    assert not out.exists(), "fail left a partial output"


# ── B3: timezone + microseconds + case-insensitive dedupe + keep-last ────────

def test_b3_tz_micros_case_dedupe(workdir):
    src = write_jsonl(workdir / "in.jsonl", [
        {"device_id": "AB-1", "timestamp": "2026-08-01T02:00:00.123456+08:00", "temp": 20},
        {"device_id": "ab-1", "timestamp": "2026-07-31T18:00:00.123456Z", "temp": 30},
        {"device_id": "ab-1", "timestamp": "2026-08-01T02:00:00.123456+08:00", "temp": 40},
    ])
    kept, _ = transform_mod.transform(str(src), str(workdir / "t.jsonl"))
    rows = read_jsonl(workdir / "t.jsonl")
    assert kept == 1, rows
    assert rows[0]["timestamp"] == "2026-07-31T18:00:00.123456Z"
    assert rows[0]["temp"] == 40.0, "keep LAST across case/offset-equivalent keys"


# ── B4: dedupe + repeated filters + unit conversion ordering ─────────────────

def test_b4_dedupe_filters_unit(workdir):
    src = write_jsonl(workdir / "in.jsonl", [
        {"device_id": "A", "timestamp": "2026-08-01T00:00:00Z", "temp": 50, "humidity": 40},
        {"device_id": "a", "timestamp": "2026-08-01T00:00:00Z", "temp": 10, "humidity": 40},  # last -> filter fail
        {"device_id": "b", "timestamp": "2026-08-01T00:01:00Z", "temp": 30, "humidity": 50},
        {"device_id": "c", "timestamp": "2026-08-01T00:02:00Z", "temp": 30, "humidity": 95},
    ])
    kept, _ = transform_mod.transform(
        str(src), str(workdir / "t.jsonl"),
        filters=["temp>=20", "humidity<80"], unit="f",
    )
    rows = read_jsonl(workdir / "t.jsonl")
    assert kept == 1 and rows[0]["device_id"] == "b", rows
    assert abs(rows[0]["temp"] - 86.0) < 1e-9


# ── B5: legacy temperature + temp=0 / empty / null distinctions ──────────────

def test_b5_legacy_temperature_distinctions(workdir):
    src = write_jsonl(workdir / "in.jsonl", [
        {"device_id": "a", "timestamp": "2026-08-01T00:00:00Z", "temp": 0, "temperature": 99},
        {"device_id": "b", "timestamp": "2026-08-01T00:00:01Z", "temp": "", "temperature": 25},
        {"device_id": "c", "timestamp": "2026-08-01T00:00:02Z", "temp": None, "temperature": 30},
        {"device_id": "d", "timestamp": "2026-08-01T00:00:03Z", "temperature": 22},
    ])
    ingest_mod.ingest(str(src), str(workdir / "cat.jsonl"))
    by = {r["device_id"]: r["temp"] for r in read_jsonl(workdir / "cat.jsonl")}
    assert by["a"] == 0.0, "temp=0 must not fall back"
    assert by["b"] == 25.0, "empty temp falls back"
    assert by["c"] == 30.0, "null temp falls back"
    assert by["d"] == 22.0, "absent temp falls back"


# ── B6: CSV BOM + quoted comma + normalize + transform + emit roundtrip ──────

def test_b6_csv_bom_quoted_roundtrip(workdir):
    csv_path = write_csv(workdir / "in.csv", [
        {"device_id": "ab,1", "timestamp": "2026-08-01T00:00:00Z", "temp": "22.5", "humidity": "45"},
        {"device_id": "cd-2", "timestamp": "2026-08-01T00:05:00+08:00", "temp": "23.1", "humidity": "50"},
    ], bom=True)
    cat = workdir / "cat.jsonl"
    accepted, skipped = ingest_mod.ingest(str(csv_path), str(cat))
    assert (accepted, skipped) == (2, 0), (accepted, skipped)
    rows = read_jsonl(cat)
    assert rows[0]["device_id"] == "ab,1", rows[0]["device_id"]
    tr = workdir / "tr.jsonl"
    kept, _ = transform_mod.transform(str(cat), str(tr))
    assert kept == 2
    tr_rows = read_jsonl(tr)
    assert all(r["timestamp"].endswith("Z") for r in tr_rows)
    text, stats = emit_mod.emit(str(tr), "csv")
    assert '"ab,1"' in text
    assert stats["count"] == 2


# ── B7: markdown output + pipe/newline escaping + correct summary ────────────

def test_b7_md_escaping_and_summary(workdir):
    src = write_jsonl(workdir / "in.jsonl", [
        {"device_id": "a|b", "timestamp": "2026-08-01T00:00:00Z", "temp": 10, "humidity": 40},
        {"device_id": "c", "timestamp": "2026-08-01T00:01:00Z", "temp": 20, "humidity": 50},
        {"device_id": "d", "timestamp": "2026-08-01T00:02:00Z", "temp": 60, "humidity": 60},
    ])
    text, _ = emit_mod.emit(str(src), "md", summary=True)
    table_lines = [l for l in text.splitlines() if l.startswith("|")]
    assert len(table_lines) == 5, table_lines  # header + sep + 3 rows
    data_row = [l for l in table_lines if "a\\|b" in l]
    assert data_row, f"pipe must be escaped: {table_lines}"
    assert data_row[0].replace("\\|", "").count("|") == 5, data_row[0]
    assert "- mean: 30.0" in text, [l for l in text.splitlines() if "mean" in l]
    assert "## Summary" in text


# ── B8: full CLI chain with mixed on-error, multiple filters, files, summary ─

def test_b8_full_cli_chain(workdir):
    src = write_text(workdir / "in.ndjson",
                     '{"device_id": "a", "timestamp": "2026-08-01T02:00:00+08:00", "temp": 20, "humidity": 45}\n'
                     '{"device_id": "A", "timestamp": "2026-07-31T18:00:00Z", "temp": 30, "humidity": 50}\n'
                     '{"device_id": "b", "timestamp": "2026-08-01T00:01:00Z", "temp": 35, "humidity": 95}\n'
                     'BAD-LINE\n'
                     '{"device_id": "c", "timestamp": "2026-08-01T00:02:00Z", "temp": 40, "humidity": 60}\n')
    r1 = run_cli(workdir, "ingest", str(src), "--output", str(workdir / "cat.jsonl"),
                 "--on-error", "skip")
    assert r1.returncode == 0, r1.stderr
    r2 = run_cli(workdir, "transform", "--input", str(workdir / "cat.jsonl"),
                 "--output", str(workdir / "tr.jsonl"),
                 "--filter", "temp>=25", "--filter", "humidity<80", "--unit", "f",
                 "--on-error", "fail")
    assert r2.returncode == 0, r2.stderr
    rows = read_jsonl(workdir / "tr.jsonl")
    # a/A collapse to one (temp 30C), b filtered out (humidity 95), c kept (40C)
    assert sorted(r["device_id"] for r in rows) == ["A", "c"], rows
    assert all(abs(r["temp"] - (t * 9 / 5 + 32)) < 1e-9 for r, t in zip(rows, [30, 40]))
    r3 = run_cli(workdir, "emit", "--input", str(workdir / "tr.jsonl"),
                 "--format", "md", "--summary", "--output", str(workdir / "rep.md"))
    assert r3.returncode == 0, r3.stderr
    report = (workdir / "rep.md").read_text(encoding="utf-8")
    assert "- records: 2" in report and "## Summary" in report


# ── B9: existing output + fail mode -> old output unchanged ──────────────────

def test_b9_existing_output_unchanged_on_fail(workdir):
    src = write_text(workdir / "in.ndjson",
                     '{"device_id": "a", "timestamp": "2026-08-01T00:00:00Z", "temp": 22}\n'
                     '{"device_id": "b", "timestamp": "2026-08-01T00:00:01Z", "temp": 23}\n'
                     'BAD\n')
    out = workdir / "cat.jsonl"
    out.write_text("KEEP ME\n", encoding="utf-8")
    r = run_cli(workdir, "ingest", str(src), "--output", str(out), "--on-error", "fail")
    assert r.returncode == 1, (r.returncode, r.stderr)
    assert out.read_text(encoding="utf-8") == "KEEP ME\n"


# ── B10: library and CLI semantics correspond under skip and fail ────────────

def test_b10_library_cli_correspond(workdir):
    src = write_text(workdir / "in.ndjson",
                     '{"device_id": "a", "timestamp": "2026-08-01T00:00:00Z", "temp": 22}\n'
                     '{oops}\n'
                     '{"device_id": "b", "timestamp": "2026-08-01T00:00:01Z", "temp": 23}\n')
    # skip: both keep 2, drop 1, and produce identical catalogs
    lib = workdir / "lib.jsonl"
    acc, sk = ingest_mod.ingest(str(src), str(lib), on_error="skip")
    assert (acc, sk) == (2, 1)
    r = run_cli(workdir, "ingest", str(src), "--output", str(workdir / "cli.jsonl"),
                "--on-error", "skip")
    assert r.returncode == 0 and "skipped=1" in r.stdout
    assert read_jsonl(lib) == read_jsonl(workdir / "cli.jsonl")
    # fail: library raises, CLI exits 1, neither leaves output
    from datapipe import DataError
    with pytest.raises(DataError):
        ingest_mod.ingest(str(src), str(workdir / "lib_fail.jsonl"), on_error="fail")
    r2 = run_cli(workdir, "ingest", str(src), "--output", str(workdir / "cli_fail.jsonl"),
                 "--on-error", "fail")
    assert r2.returncode == 1
    assert not (workdir / "lib_fail.jsonl").exists()
    assert not (workdir / "cli_fail.jsonl").exists()


# ── B11: atomicity for emit --output with pre-existing report ────────────────

def test_b11_emit_fail_preserves_existing_report(workdir):
    src = write_text(workdir / "in.jsonl",
                     '{"device_id": "a", "timestamp": "2026-08-01T00:00:00Z", "temp": 22}\n'
                     '{oops}\n')
    out = workdir / "report.json"
    out.write_text('{"previous": true}\n', encoding="utf-8")
    r = run_cli(workdir, "emit", "--input", str(src), "--format", "json",
                "--output", str(out), "--on-error", "fail")
    assert_clean_data_error(r)
    assert out.read_text(encoding="utf-8") == '{"previous": true}\n'
