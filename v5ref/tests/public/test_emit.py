import json
from conftest import read_jsonl
from datapipe import emit as emit_mod


def make_records(workdir, rows):
    p = workdir / "records.jsonl"
    p.write_text("\n".join(json.dumps(r) for r in rows), encoding="utf-8")
    return p


ROWS = [
    {"device_id": "ab-1", "timestamp": "2026-08-01T10:00:00Z", "temp": 20.0, "humidity": 45},
    {"device_id": "cd-2", "timestamp": "2026-08-01T10:05:00Z", "temp": 30.0, "humidity": 50},
]


def test_emit_json_stats(workdir):
    p = make_records(workdir, ROWS)
    text, stats = emit_mod.emit(str(p), "json")
    doc = json.loads(text)
    assert doc["stats"]["count"] == 2
    assert doc["stats"]["mean"] == 25.0


def test_emit_json_empty(workdir):
    p = make_records(workdir, [])
    text, stats = emit_mod.emit(str(p), "json")
    doc = json.loads(text)
    assert doc["stats"]["count"] == 0
    assert doc["stats"]["mean"] is None


def test_emit_csv_quoting(workdir):
    p = make_records(workdir, [{"device_id": "ab,1", "timestamp": "2026-08-01T10:00:00Z", "temp": 20.0, "humidity": None}])
    text, _ = emit_mod.emit(str(p), "csv")
    lines = text.splitlines()
    assert len(lines) == 2
    assert '"ab,1"' in lines[1]


def test_emit_md_mean(workdir):
    p = make_records(workdir, ROWS)
    text, _ = emit_mod.emit(str(p), "md")
    assert "- mean: 25.0" in text
