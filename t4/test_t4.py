"""T4 deep-tier tests: spec-derived semantics beyond public coverage.

T4a (boundary extensions): behavior only a robust implementation handles.
T4b (spec inference): behaviors derivable from the v2.3 spec text but never
     exercised by public tests (requires reading/understanding the spec).
T4c (cross-module consistency): interactions between ingest/transform/emit
     that public tests never combine.
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


# ─────────────────────────── T4a: boundary extensions ───────────────────────

def test_t4a_ndjson_malformed_counted_not_crash(workdir):
    """Malformed NDJSON lines must be skipped+counted, not crash the pipeline."""
    src = workdir / "in.ndjson"
    src.write_text(
        '{"device_id": "a", "timestamp": "2026-08-01T00:00:00Z", "temp": 22.0}\n'
        '{broken json}\n'
        '{"device_id": "b", "timestamp": "2026-08-01T00:00:01Z", "temp": 23.0}\n'
        '{"device_id": "c", "timestamp": "2026-08-01T00:00:02Z"\n'
        '{"device_id": "d", "timestamp": "2026-08-01T00:00:03Z", "temp": 24.0}\n',
        encoding="utf-8",
    )
    out = workdir / "cat.jsonl"
    accepted, skipped = ingest_mod.ingest(str(src), str(out))
    # valid: a, b, d (3); malformed: '{broken json}' + truncated line (2)
    assert accepted == 3, f"expected 3 accepted, got {accepted}"
    assert skipped == 2, f"expected 2 malformed skipped, got {skipped}"


def test_t4a_extless_json_sniffed(workdir):
    """Content sniffing: extensionless file starting with [ or { must parse as JSON."""
    src = workdir / "data.raw"
    src.write_text(json.dumps([{"device_id": "a", "timestamp": "2026-08-01T00:00:00Z", "temp": 22.0}]), encoding="utf-8")
    out = workdir / "cat.jsonl"
    accepted, skipped = ingest_mod.ingest(str(src), str(out))
    assert accepted == 1 and skipped == 0


def test_t4a_legacy_temperature_field(workdir):
    """Spec: 'temperature' legacy field name must normalize to temp."""
    src = workdir / "in.jsonl"
    write_jsonl(src, [{"device_id": "a", "timestamp": "2026-08-01T00:00:00Z", "temperature": 22.5}])
    out = workdir / "cat.jsonl"
    accepted, skipped = ingest_mod.ingest(str(src), str(out))
    assert accepted == 1 and skipped == 0
    rows = read_jsonl(out)
    assert rows[0]["temp"] == 22.5


def test_t4a_whitespace_fields_trimmed(workdir):
    """device_id/timestamp whitespace must be trimmed (GOLD trims)."""
    src = workdir / "in.jsonl"
    write_jsonl(src, [{"device_id": "  ab-1  ", "timestamp": "  2026-08-01T00:00:00Z  ", "temp": 22.0}])
    out = workdir / "cat.jsonl"
    accepted, skipped = ingest_mod.ingest(str(src), str(out))
    rows = read_jsonl(out)
    assert rows[0]["device_id"] == "ab-1"
    assert rows[0]["timestamp"] == "2026-08-01T00:00:00Z"


def test_t4a_nonnumeric_temp_skipped_as_null(workdir):
    """Spec: temp/humidity are 'number or null'; unparseable -> null, keep row."""
    src = workdir / "in.jsonl"
    write_jsonl(src, [{"device_id": "a", "timestamp": "2026-08-01T00:00:00Z", "temp": "not-a-number"}])
    out = workdir / "cat.jsonl"
    accepted, skipped = ingest_mod.ingest(str(src), str(out))
    assert accepted == 1 and skipped == 0
    rows = read_jsonl(out)
    assert rows[0]["temp"] is None


# ─────────────────────────── T4b: spec inference ────────────────────────────

def test_t4b_dedupe_keeps_last_value_and_lowercase_key(workdir):
    """Spec: dedupe by (device_id lowercased, timestamp), keep LAST occurrence.
    Same key must keep the LAST row's values (temp=25), not the first (temp=10).
    """
    src = workdir / "in.jsonl"
    write_jsonl(src, [
        {"device_id": "AB-1", "timestamp": "2026-08-01T00:00:00Z", "temp": 10.0},
        {"device_id": "ab-1", "timestamp": "2026-08-01T00:00:00Z", "temp": 25.0},
    ])
    out = workdir / "t.jsonl"
    kept, skipped = transform_mod.transform(str(src), str(out), dedupe=True)
    assert kept == 1
    rows = read_jsonl(out)
    assert rows[0]["temp"] == 25.0


def test_t4b_filter_applied_after_dedupe(workdir):
    """Spec order: dedupe THEN filter (a filtered-away duplicate must not
    resurrect a deduped row)."""
    src = workdir / "in.jsonl"
    write_jsonl(src, [
        {"device_id": "a", "timestamp": "2026-08-01T00:00:00Z", "temp": 20.0},
        {"device_id": "a", "timestamp": "2026-08-01T00:00:00Z", "temp": 99.0},  # dup key, would fail range
        {"device_id": "b", "timestamp": "2026-08-01T00:00:01Z", "temp": 30.0},
    ])
    out = workdir / "t.jsonl"
    kept, skipped = transform_mod.transform(str(src), str(out), filter_expr="temp>25")
    rows = read_jsonl(out)
    # a dedupes to the LAST (99 -> out of range, skipped before dedupe), so only b remains
    assert kept == 1
    assert rows[0]["device_id"] == "b"


def test_t4b_unit_f_applies_after_filter(workdir):
    """Filter is on ORIGINAL celsius values; unit conversion happens after."""
    src = workdir / "in.jsonl"
    write_jsonl(src, [
        {"device_id": "a", "timestamp": "2026-08-01T00:00:00Z", "temp": 20.0},  # 68F
        {"device_id": "b", "timestamp": "2026-08-01T00:00:01Z", "temp": 30.0},  # 86F
    ])
    out = workdir / "t.jsonl"
    kept, _ = transform_mod.transform(str(src), str(out), filter_expr="temp>25", unit="f")
    rows = read_jsonl(out)
    assert kept == 1
    assert rows[0]["device_id"] == "b"
    assert abs(rows[0]["temp"] - 86.0) < 1e-9


# ─────────────────────── T4c: cross-module consistency ──────────────────────

def test_t4c_full_pipeline_roundtrip(workdir):
    """Full chain: ingest CSV -> transform -> emit, with filter+unit+summary.
    The output must be exactly parseable and consistent."""
    src = workdir / "in.csv"
    src.write_text(
        'device_id,timestamp,temp,humidity\n'
        'a,2026-08-01T00:00:00+08:00,20,45\n'
        'b,2026-08-01T00:00:01Z,30,55\n'
        'c,2026-08-01T00:00:02+05:30,85,100\n'
        'bad-line-without-commas\n',
        encoding="utf-8",
    )
    cat = workdir / "catalog.jsonl"
    acc, sk_ingest = ingest_mod.ingest(str(src), str(cat))
    assert acc == 3, f"ingest accepted {acc}"
    tr = workdir / "transformed.jsonl"
    kept, sk_tr = transform_mod.transform(str(cat), str(tr), filter_expr="temp>25", unit="f")
    # a=20C (filtered), b=30C->86F (kept), c=85C->185F (kept), bad-line skipped at ingest
    assert kept == 2, f"expected 2 kept, got {kept}"
    rows = read_jsonl(tr)
    temps = sorted(r["temp"] for r in rows)
    assert abs(temps[0] - 86.0) < 1e-9 and abs(temps[1] - 185.0) < 1e-9
    text, stats = emit_mod.emit(str(tr), "json", summary=True)
    doc = json.loads(text)
    assert doc["stats"]["count"] == 2
    assert "summary" in doc
    assert abs(doc["stats"]["mean"] - (86.0 + 185.0) / 2) < 1e-9


def test_t4c_emit_md_uses_arithmetic_mean(workdir):
    """Spec: md mean is arithmetic mean (not mid-range). Asymmetric data."""
    src = workdir / "in.jsonl"
    write_jsonl(src, [
        {"device_id": "a", "timestamp": "2026-08-01T00:00:00Z", "temp": 10.0},
        {"device_id": "b", "timestamp": "2026-08-01T00:00:01Z", "temp": 20.0},
        {"device_id": "c", "timestamp": "2026-08-01T00:00:02Z", "temp": 60.0},
    ])
    text, _ = emit_mod.emit(str(src), "md")
    assert "- mean: 30.0" in text, [l for l in text.splitlines() if "mean" in l]


def test_t4c_cli_chain_end_to_end(workdir):
    """CLI chain with --output writes files; exit codes per spec."""
    src = workdir / "in.csv"
    src.write_text(
        'device_id,timestamp,temp,humidity\n'
        'a,2026-08-01T00:00:00Z,20,45\n',
        encoding="utf-8",
    )
    r1 = run_cli(workdir, "ingest", str(src), "--output", str(workdir / "cat.jsonl"))
    assert r1.returncode == 0, r1.stderr
    assert (workdir / "cat.jsonl").exists()
    r2 = run_cli(workdir, "transform", "--input", str(workdir / "cat.jsonl"), "--output", str(workdir / "tr.jsonl"), "--filter", "temp>15")
    assert r2.returncode == 0, r2.stderr
    assert (workdir / "tr.jsonl").exists()
    r3 = run_cli(workdir, "emit", "--input", str(workdir / "tr.jsonl"), "--format", "md", "--output", str(workdir / "rep.md"))
    assert r3.returncode == 0, r3.stderr
    assert (workdir / "rep.md").exists()
    r4 = run_cli(workdir, "ingest", str(workdir / "missing.csv"))
    assert r4.returncode == 1, f"missing input must exit 1, got {r4.returncode}"
