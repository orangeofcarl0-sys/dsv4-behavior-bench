"""D11: spec-inference pressure — behaviors the spec implies but never
states; only an implementation that models the FULL pipeline semantics passes.
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


# D11.1: dedupe key uses NORMALIZED timestamp (Z), so pre-normalized variants
#        with different offsets MUST dedupe to one row. (spec: "按 (device_id
#        转小写, timestamp) 去重" — timestamp is the NORMALIZED one)

def test_d111_dedupe_normalized_ts_collapses_offsets(workdir):
    src = workdir / "in.jsonl"
    write_jsonl(src, [
        {"device_id": "a", "timestamp": "2026-08-01T02:00:00+08:00", "temp": 10.0},
        {"device_id": "A", "timestamp": "2026-07-31T18:00:00Z", "temp": 20.0},  # same instant!
    ])
    out = workdir / "t.jsonl"
    kept, _ = transform_mod.transform(str(src), str(out), dedupe=True)
    assert kept == 1, f"same instant w/ different offsets must dedupe, got {kept}"


# D11.2: range check happens on COERCED numeric values (a string "85.0" is
#        coerced then range-checked; string "nan" must be rejected as invalid)

def test_d112_nan_temp_rejected(workdir):
    src = workdir / "in.jsonl"
    write_jsonl(src, [{"device_id": "a", "timestamp": "2026-08-01T00:00:00Z", "temp": "nan"}])
    out = workdir / "t.jsonl"
    kept, skipped = transform_mod.transform(str(src), str(out))
    assert kept == 0 and skipped == 1, f"nan must fail range check, got ({kept},{skipped})"


def test_d113_inf_temp_rejected(workdir):
    src = workdir / "in.jsonl"
    write_jsonl(src, [{"device_id": "a", "timestamp": "2026-08-01T00:00:00Z", "temp": "inf"}])
    out = workdir / "t.jsonl"
    kept, skipped = transform_mod.transform(str(src), str(out))
    assert kept == 0 and skipped == 1, f"inf must fail range check, got ({kept},{skipped})"


# D11.3: filter on converted-unit values — spec order: dedupe → filter → unit.
#        If filter ran AFTER unit conversion, temp>25 in F would mean >-3.9C.
#        Spec says nothing explicit, but the pipeline is ingest→transform→emit
#        and --unit is a transform output concern, so filter is on INPUT units.

def test_d114_filter_before_unit_conversion(workdir):
    src = workdir / "in.jsonl"
    write_jsonl(src, [
        {"device_id": "a", "timestamp": "2026-08-01T00:00:00Z", "temp": 20.0},
        {"device_id": "b", "timestamp": "2026-08-01T00:01:00Z", "temp": 30.0},
    ])
    out = workdir / "t.jsonl"
    kept, _ = transform_mod.transform(str(src), str(out), filter_expr="temp>25", unit="f")
    rows = read_jsonl(out)
    assert kept == 1 and rows[0]["device_id"] == "b"
    assert abs(rows[0]["temp"] - 86.0) < 1e-9


# D11.4: dedupe keep-LAST with --no-dedupe retaining both (spec flag)

def test_d115_no_dedupe_keeps_all(workdir):
    src = workdir / "in.jsonl"
    write_jsonl(src, [
        {"device_id": "a", "timestamp": "2026-08-01T00:00:00Z", "temp": 10.0},
        {"device_id": "a", "timestamp": "2026-08-01T00:00:00Z", "temp": 20.0},
    ])
    out = workdir / "t.jsonl"
    kept, _ = transform_mod.transform(str(src), str(out), dedupe=False)
    assert kept == 2, f"--no-dedupe must keep both, got {kept}"


# D11.5: CSV output round-trips through ingest (idempotence across modules)

def test_d116_csv_emit_roundtrip_ingest(workdir):
    src = workdir / "in.jsonl"
    write_jsonl(src, [{"device_id": "ab,1", "timestamp": "2026-08-01T00:00:00Z", "temp": 22.5, "humidity": 45}])
    csv_text, _ = emit_mod.emit(str(src), "csv")
    csv_path = workdir / "out.csv"
    csv_path.write_text(csv_text, encoding="utf-8")
    cat = workdir / "cat.jsonl"
    accepted, skipped = ingest_mod.ingest(str(csv_path), str(cat))
    rows = read_jsonl(cat)
    assert accepted == 1
    assert rows[0]["device_id"] == "ab,1", f"CSV roundtrip lost comma field: {rows[0]['device_id']!r}"
    assert abs(rows[0]["temp"] - 22.5) < 1e-9


# D11.6: emit JSON output is itself valid NDJSON-parseable rows (no NaN/Inf)

def test_d117_emit_json_no_nan(workdir):
    src = workdir / "in.jsonl"
    write_jsonl(src, [{"device_id": "a", "timestamp": "2026-08-01T00:00:00Z", "temp": 22.0}])
    text, _ = emit_mod.emit(str(src), "json")
    assert "NaN" not in text and "Infinity" not in text and "inf" not in text.lower()


# D11.7: CLI chain exit codes precisely per spec (0 success / 1 data / 2 usage)

def test_d118_cli_usage_error_exit2(workdir):
    r = run_cli(workdir, "emit", "--format", "xml")
    assert r.returncode == 2, f"bad format must exit 2, got {r.returncode}"


def test_d119_cli_missing_transform_input_exit1(workdir):
    r = run_cli(workdir, "transform", "--input", str(workdir / "nope.jsonl"))
    assert r.returncode == 1, f"missing input must exit 1, got {r.returncode}"


# D11.8: unit conversion does not mutate the input file (side-effect free)

def test_d1110_transform_does_not_modify_input(workdir):
    src = workdir / "in.jsonl"
    write_jsonl(src, [{"device_id": "a", "timestamp": "2026-08-01T00:00:00Z", "temp": 20.0}])
    before = src.read_bytes()
    out = workdir / "t.jsonl"
    transform_mod.transform(str(src), str(out), unit="f")
    assert src.read_bytes() == before, "transform must not modify input file"


# D11.9: idempotent re-transform (already-normalized input stays stable)

def test_d1111_retransform_idempotent(workdir):
    src = workdir / "in.jsonl"
    write_jsonl(src, [{"device_id": "a", "timestamp": "2026-08-01T00:00:00Z", "temp": 20.0}])
    out1 = workdir / "t1.jsonl"
    out2 = workdir / "t2.jsonl"
    transform_mod.transform(str(src), str(out1))
    transform_mod.transform(str(out1), str(out2))
    rows1 = read_jsonl(out1)
    rows2 = read_jsonl(out2)
    assert rows1 == rows2, "re-transform must be idempotent"
