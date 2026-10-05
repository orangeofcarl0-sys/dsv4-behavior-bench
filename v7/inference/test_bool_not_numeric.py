"""Behaviour: JSON booleans are not numbers. temp:true must not coerce to 1.0;
it normalises to null (row kept) rather than being treated as a value.

Anchor: seed 0/1, gold 0/1, gold2 1/1 -- this is one of the two behaviours that
separates gold2 from gold, i.e. it is genuinely at the top of the difficulty band.
Live for models: p=0.39, D=4.33.
Source: legacy d123.
"""
from conftest import ingest_mod, read_jsonl, write_jsonl


def test_true_is_not_one(workdir):
    src = workdir / "in.jsonl"
    write_jsonl(src, [{"device_id": "a", "timestamp": "2026-08-01T00:00:00Z", "temp": True}])
    out = workdir / "cat.jsonl"
    ingest_mod.ingest(str(src), str(out))
    rows = read_jsonl(out)
    assert rows[0]["temp"] is None, f"bool must not coerce to a number, got {rows[0]['temp']!r}"


def test_false_is_not_zero(workdir):
    src = workdir / "in.jsonl"
    write_jsonl(src, [{"device_id": "a", "timestamp": "2026-08-01T00:00:00Z", "temp": False}])
    out = workdir / "cat.jsonl"
    ingest_mod.ingest(str(src), str(out))
    rows = read_jsonl(out)
    assert rows[0]["temp"] is None, f"bool must not coerce to a number, got {rows[0]['temp']!r}"


def test_bool_humidity_also_null(workdir):
    src = workdir / "in.jsonl"
    write_jsonl(src, [{"device_id": "a", "timestamp": "2026-08-01T00:00:00Z",
                       "temp": 20.0, "humidity": True}])
    out = workdir / "cat.jsonl"
    ingest_mod.ingest(str(src), str(out))
    rows = read_jsonl(out)
    assert rows[0]["humidity"] is None, f"got {rows[0]['humidity']!r}"
