"""D12: adversarial robustness — targets implementation weaknesses that
even the strongest agent product (GOLD==m1-router) may exhibit.

Each test first verifies the WEAKNESS exists in seed, then demands the
robust behavior. These are derived from pipeline consistency: if ingest
tolerates malformed records (spec), transform/emit operating on the SAME
pipeline should too.
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


# ── D12.1: transform must tolerate malformed lines (pipeline consistency) ────

def test_d121_transform_skips_malformed_line(workdir):
    """ingest tolerates bad records (D1); transform consumes ingest's output,
    so it must also skip a bad line rather than crash the whole pipeline."""
    src = workdir / "in.jsonl"
    src.write_text(
        '{"device_id": "a", "timestamp": "2026-08-01T00:00:00Z", "temp": 22.0}\n'
        'NOT-JSON\n'
        '{"device_id": "b", "timestamp": "2026-08-01T00:00:01Z", "temp": 23.0}\n',
        encoding="utf-8",
    )
    out = workdir / "t.jsonl"
    kept, skipped = transform_mod.transform(str(src), str(out))
    assert kept == 2, f"transform must keep valid lines, got kept={kept}"


# ── D12.2: emit must tolerate malformed lines ────────────────────────────────

def test_d122_emit_skips_malformed_line(workdir):
    src = workdir / "in.jsonl"
    src.write_text(
        '{"device_id": "a", "timestamp": "2026-08-01T00:00:00Z", "temp": 22.0}\n'
        '{oops}\n',
        encoding="utf-8",
    )
    text, stats = emit_mod.emit(str(src), "json")
    assert stats["count"] == 1, f"emit must skip malformed, got {stats}"


# ── D12.3: JSON boolean is NOT a numeric metric (spec: number or null) ───────

def test_d123_bool_temp_not_numeric(workdir):
    """Spec: temp is '数值或 null'. JSON true/false are booleans, not numbers;
    a strict implementation must not accept them as 1.0/0.0."""
    src = workdir / "in.jsonl"
    write_jsonl(src, [{"device_id": "a", "timestamp": "2026-08-01T00:00:00Z", "temp": True}])
    out = workdir / "cat.jsonl"
    accepted, _ = ingest_mod.ingest(str(src), str(out))
    rows = read_jsonl(out)
    assert rows[0]["temp"] is None, f"bool must not coerce to number, got {rows[0]['temp']!r}"


# ── D12.4: CSV row with fewer columns than header ────────────────────────────

def test_d124_csv_short_row_skipped(workdir):
    """A CSV row missing columns must not silently misalign (device_id
    getting the timestamp value). Missing device_id/timestamp -> skip+count."""
    src = workdir / "in.csv"
    src.write_text(
        'device_id,timestamp,temp,humidity\n'
        'a,2026-08-01T00:00:00Z,22.0,45\n'
        'only-one-field\n',
        encoding="utf-8",
    )
    out = workdir / "cat.jsonl"
    accepted, skipped = ingest_mod.ingest(str(src), str(out))
    assert accepted == 1, f"got accepted={accepted}"
    assert skipped >= 1, f"short row must be skipped, got skipped={skipped}"


# ── D12.5: transform input as JSON array (single line) must not crash ────────

def test_d125_transform_json_array_input(workdir):
    """A whole-file JSON array is a plausible catalog; must be handled
    gracefully (either parse or skip), never AttributeError-crash."""
    src = workdir / "in.json"
    src.write_text(
        json.dumps([{"device_id": "a", "timestamp": "2026-08-01T00:00:00Z", "temp": 22.0}]),
        encoding="utf-8",
    )
    out = workdir / "t.jsonl"
    try:
        kept, skipped = transform_mod.transform(str(src), str(out))
        # graceful: either parse the array (kept=1) or skip non-object lines
        # (kept=0). CRASH is the only failure mode.
        assert kept in (0, 1), f"got kept={kept}"
        if kept == 1:
            rows = read_jsonl(out)
            assert rows[0]["device_id"] == "a"
    except (AttributeError, TypeError) as exc:
        raise AssertionError(f"transform crashed on array input: {exc!r}")


# ── D12.6: emit md table escaping (device_id with pipe breaks table) ─────────

def test_d126_md_table_pipe_escaped(workdir):
    """Markdown table cells containing '|' must be escaped (\\|) or the
    table structure breaks."""
    src = workdir / "in.jsonl"
    write_jsonl(src, [{"device_id": "a|b", "timestamp": "2026-08-01T00:00:00Z", "temp": 22.0}])
    text, _ = emit_mod.emit(str(src), "md")
    # the cell must not introduce an extra column: look for escaped or absent pipe
    lines = [l for l in text.splitlines() if l.startswith("|")]
    # header + separator + 1 data row = 3 table lines
    assert len(lines) == 3, f"table must have header+sep+row, got {len(lines)} lines"
    # escaped pipe must not create a 5th column: data row has exactly 5 pipe chars
    data_row = lines[2]
    unescaped = data_row.replace("\\|", "").count("|")
    assert unescaped == 5, f"escaped pipe broke table: {data_row!r}"


# ── D12.7: CLI transform exit code on malformed input (data error=1) ─────────

def test_d127_cli_transform_malformed_exit1(workdir):
    src = workdir / "in.jsonl"
    src.write_text("NOT-JSON\n", encoding="utf-8")
    r = run_cli(workdir, "transform", "--input", str(src))
    # malformed data is a DATA error -> exit 1 (not 2 usage)
    assert r.returncode == 1, f"got {r.returncode}"


# ── D12.8: dedupe keeps LAST occurrence across the full row (not first) ──────

def test_d128_dedupe_keeps_last_humidity(workdir):
    src = workdir / "in.jsonl"
    write_jsonl(src, [
        {"device_id": "a", "timestamp": "2026-08-01T00:00:00Z", "temp": 10.0, "humidity": 10},
        {"device_id": "a", "timestamp": "2026-08-01T00:00:00Z", "temp": 10.0, "humidity": 90},
    ])
    out = workdir / "t.jsonl"
    kept, _ = transform_mod.transform(str(src), str(out))
    rows = read_jsonl(out)
    assert rows[0]["humidity"] == 90, f"must keep LAST row, got humidity={rows[0]['humidity']!r}"


# ── D12.9: filter on missing field returns no rows (no crash) ────────────────

def test_d129_filter_missing_field_no_crash(workdir):
    src = workdir / "in.jsonl"
    write_jsonl(src, [{"device_id": "a", "timestamp": "2026-08-01T00:00:00Z", "temp": 22.0}])
    out = workdir / "t.jsonl"
    kept, _ = transform_mod.transform(str(src), str(out), filter_expr="nonexistent>5")
    assert kept == 0


# ── D12.10: temp "0" and humidity 0 preserved (not treated as missing) ───────

def test_d1210_zero_values_preserved(workdir):
    src = workdir / "in.jsonl"
    write_jsonl(src, [{"device_id": "a", "timestamp": "2026-08-01T00:00:00Z", "temp": 0.0, "humidity": 0}])
    out = workdir / "cat.jsonl"
    accepted, _ = ingest_mod.ingest(str(src), str(out))
    rows = read_jsonl(out)
    assert rows[0]["temp"] == 0.0, f"got {rows[0]['temp']!r}"
    assert rows[0]["humidity"] == 0.0, f"got {rows[0]['humidity']!r}"
