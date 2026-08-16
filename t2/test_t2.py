"""T2 boundary tests: edge inputs a competent fixer handles without deep spec reading."""
import json
from pathlib import Path

from conftest import read_jsonl, write_jsonl, ingest_mod, transform_mod, emit_mod


def test_t2_boundary_temp_85_kept(workdir):
    # exactly at upper bound must be kept
    src = workdir / "in.jsonl"
    write_jsonl(src, [{"device_id": "a", "timestamp": "2026-08-01T00:00:00Z", "temp": 85.0, "humidity": 50}])
    out = workdir / "t.jsonl"
    kept, skipped = transform_mod.transform(str(src), str(out))
    assert kept == 1 and skipped == 0


def test_t2_boundary_temp_85_plus_epsilon_skipped(workdir):
    src = workdir / "in.jsonl"
    write_jsonl(src, [{"device_id": "a", "timestamp": "2026-08-01T00:00:00Z", "temp": 85.01, "humidity": 50}])
    out = workdir / "t.jsonl"
    kept, skipped = transform_mod.transform(str(src), str(out))
    assert kept == 0 and skipped == 1


def test_t2_empty_catalog_emit_no_crash(workdir):
    src = workdir / "empty.jsonl"
    src.write_text("", encoding="utf-8")
    text, stats = emit_mod.emit(str(src), "json")
    assert stats["count"] == 0 and stats["min"] is None and stats["mean"] is None


def test_t2_filter_string_equality(workdir):
    src = workdir / "in.jsonl"
    write_jsonl(src, [
        {"device_id": "ab-1", "timestamp": "2026-08-01T00:00:00Z", "temp": 20.0, "humidity": 45},
        {"device_id": "cd-2", "timestamp": "2026-08-01T00:00:00Z", "temp": 30.0, "humidity": 50},
    ])
    out = workdir / "t.jsonl"
    kept, _ = transform_mod.transform(str(src), str(out), filter_expr="device_id=ab-1")
    assert kept == 1


def test_t2_single_object_json(workdir):
    src = workdir / "in.json"
    src.write_text(json.dumps({"device_id": "a", "timestamp": "2026-08-01T00:00:00Z", "temp": 22.0}), encoding="utf-8")
    out = workdir / "cat.jsonl"
    accepted, skipped = ingest_mod.ingest(str(src), str(out))
    assert accepted == 1 and skipped == 0


def test_t2_microsecond_timestamp(workdir):
    src = workdir / "in.jsonl"
    write_jsonl(src, [{"device_id": "a", "timestamp": "2026-08-01T00:00:00.123456+08:00", "temp": 22.0}])
    out = workdir / "t.jsonl"
    kept, skipped = transform_mod.transform(str(src), str(out))
    assert kept == 1 and skipped == 0
    rows = read_jsonl(out)
    assert rows[0]["timestamp"].endswith("Z")


def test_t2_ndjson_bad_line_skipped(workdir):
    src = workdir / "in.jsonl"
    src.write_text(
        '{"device_id": "a", "timestamp": "2026-08-01T00:00:00Z", "temp": 22.0}\n'
        'NOT-JSON\n'
        '{"device_id": "b", "timestamp": "2026-08-01T00:00:01Z", "temp": 23.0}\n',
        encoding="utf-8",
    )
    out = workdir / "cat.jsonl"
    accepted, skipped = ingest_mod.ingest(str(src), str(out))
    assert accepted == 2 and skipped == 1


def test_t2_csv_bom_quotes(workdir):
    src = workdir / "in.csv"
    content = 'device_id,timestamp,temp,humidity\n"ab,1",2026-08-01T00:00:00Z,20.5,45\n'
    src.write_bytes(b"\xef\xbb\xbf" + content.encode("utf-8"))
    out = workdir / "cat.jsonl"
    accepted, skipped = ingest_mod.ingest(str(src), str(out))
    assert accepted == 1 and skipped == 0
    rows = read_jsonl(out)
    assert rows[0]["device_id"] == "ab,1"
    assert rows[0]["temp"] == 20.5