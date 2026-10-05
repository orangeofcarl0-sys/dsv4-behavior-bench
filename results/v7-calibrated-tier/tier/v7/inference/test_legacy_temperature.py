"""Behaviour: legacy 'temperature' field is a fallback when temp is absent/null/empty,
but temp=0 is a real value and must NOT fall back.

Anchor: seed 0/1, gold 1/1, gold2 1/1. Live for models: p=0.28, D=3.53.
Source: legacy t4a / d3.
"""
from conftest import ingest_mod, read_jsonl, write_jsonl


def test_fallback_when_temp_empty(workdir):
    src = workdir / "in.jsonl"
    write_jsonl(src, [{"device_id": "a", "timestamp": "2026-08-01T00:00:00Z",
                       "temp": "", "temperature": 21.5}])
    out = workdir / "cat.jsonl"
    ingest_mod.ingest(str(src), str(out))
    rows = read_jsonl(out)
    assert abs(rows[0]["temp"] - 21.5) < 1e-9, f"got {rows[0]['temp']!r}"


def test_fallback_when_temp_null(workdir):
    src = workdir / "in.jsonl"
    write_jsonl(src, [{"device_id": "a", "timestamp": "2026-08-01T00:00:00Z",
                       "temp": None, "temperature": 21.5}])
    out = workdir / "cat.jsonl"
    ingest_mod.ingest(str(src), str(out))
    rows = read_jsonl(out)
    assert abs(rows[0]["temp"] - 21.5) < 1e-9, f"got {rows[0]['temp']!r}"


def test_zero_temp_does_not_fall_back(workdir):
    src = workdir / "in.jsonl"
    write_jsonl(src, [{"device_id": "a", "timestamp": "2026-08-01T00:00:00Z",
                       "temp": 0, "temperature": 99.0}])
    out = workdir / "cat.jsonl"
    ingest_mod.ingest(str(src), str(out))
    rows = read_jsonl(out)
    assert rows[0]["temp"] == 0, f"temp=0 is real, got {rows[0]['temp']!r}"
