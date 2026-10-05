"""Behaviour: microsecond precision survives transform (UTC normalization must not
truncate to seconds).

Anchor: seed 0/1, gold 1/1, gold2 1/1. Live for models: p=0.44, D=1.87.
Source: legacy d102 / t2.
"""
from conftest import transform_mod, read_jsonl, write_jsonl


def test_microseconds_preserved(workdir):
    src = workdir / "in.jsonl"
    write_jsonl(src, [{"device_id": "a", "timestamp": "2026-07-31T18:00:00.123456Z", "temp": 20.0}])
    out = workdir / "t.jsonl"
    transform_mod.transform(str(src), str(out))
    rows = read_jsonl(out)
    assert rows[0]["timestamp"] == "2026-07-31T18:00:00.123456Z", f"got {rows[0]['timestamp']!r}"


def test_microseconds_survive_offset_normalization(workdir):
    src = workdir / "in.jsonl"
    write_jsonl(src, [{"device_id": "a", "timestamp": "2026-07-31T20:00:00.500000+02:00", "temp": 20.0}])
    out = workdir / "t.jsonl"
    transform_mod.transform(str(src), str(out))
    rows = read_jsonl(out)
    assert rows[0]["timestamp"] == "2026-07-31T18:00:00.500000Z", f"got {rows[0]['timestamp']!r}"
