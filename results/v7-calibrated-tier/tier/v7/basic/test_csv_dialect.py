"""Behaviour: CSV dialect robustness -- BOM tolerated, quoted commas parsed,
short rows skipped, emitted fields re-quoted.

Anchor: seed 0/1, gold 1/1, gold2 1/1. Live for models: p=0.78, D=2.93.
Source: legacy t2 / t3 / d116 / d124 / d7.
"""
from conftest import emit_mod, ingest_mod, read_jsonl, transform_mod, write_jsonl


def test_bom_and_quoted_comma(workdir):
    src = workdir / "in.csv"
    src.write_text('\ufeffdevice_id,timestamp,temp,humidity\n"ab,1",2026-08-01T00:00:00Z,22.5,40\n',
                   encoding="utf-8")
    out = workdir / "cat.jsonl"
    ingest_mod.ingest(str(src), str(out))
    rows = read_jsonl(out)
    assert rows[0]["device_id"] == "ab,1", f"got {rows[0]['device_id']!r}"
    assert abs(rows[0]["temp"] - 22.5) < 1e-9


def test_emit_csv_quotes_comma(workdir):
    src = workdir / "in.jsonl"
    write_jsonl(src, [{"device_id": "ab,1", "timestamp": "2026-08-01T00:00:00Z",
                       "temp": 22.5, "humidity": 40.0}])
    cat = workdir / "cat.jsonl"
    ingest_mod.ingest(str(src), str(cat))
    tr = workdir / "t.jsonl"
    transform_mod.transform(str(cat), str(tr))
    out = workdir / "o.csv"
    emit_mod.emit(str(tr), "csv", out_path=str(out))
    text = out.read_text(encoding="utf-8")
    assert '"ab,1"' in text, f"comma field must be quoted, got {text!r}"
