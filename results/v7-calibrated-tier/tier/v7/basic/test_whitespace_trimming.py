"""Behaviour: device_id / timestamp surrounding whitespace is stripped.

Anchor: seed 0/3, gold 3/3, gold2 3/3. Live for models: p=0.67, D very high.
Source: legacy d2 / t4a.
"""
from conftest import ingest_mod, read_jsonl, write_jsonl


def test_device_id_trimmed(workdir):
    src = workdir / "in.jsonl"
    write_jsonl(src, [{"device_id": "  ab-1  ", "timestamp": "2026-08-01T00:00:00Z", "temp": 22.0}])
    out = workdir / "cat.jsonl"
    ingest_mod.ingest(str(src), str(out))
    rows = read_jsonl(out)
    assert rows[0]["device_id"] == "ab-1", f"got {rows[0]['device_id']!r}"


def test_timestamp_trimmed(workdir):
    src = workdir / "in.jsonl"
    write_jsonl(src, [{"device_id": "ab-1", "timestamp": "  2026-08-01T00:00:00Z  ", "temp": 22.0}])
    out = workdir / "cat.jsonl"
    ingest_mod.ingest(str(src), str(out))
    rows = read_jsonl(out)
    assert rows[0]["timestamp"] == "2026-08-01T00:00:00Z", f"got {rows[0]['timestamp']!r}"


def test_whitespace_only_field_is_missing(workdir):
    """a whitespace-only device_id is missing, not a value named '   '"""
    src = workdir / "in.jsonl"
    write_jsonl(src, [
        {"device_id": "   ", "timestamp": "2026-08-01T00:00:00Z", "temp": 22.0},
        {"device_id": "ok", "timestamp": "2026-08-01T00:00:01Z", "temp": 23.0},
    ])
    out = workdir / "cat.jsonl"
    accepted, skipped = ingest_mod.ingest(str(src), str(out))
    rows = read_jsonl(out)
    assert accepted == 1 and skipped == 1, f"got accepted={accepted} skipped={skipped}"
    assert rows[0]["device_id"] == "ok"
