"""Behaviour: the three-stage chain composes correctly end to end.

Anchor: seed 0/1, gold 0/1, gold2 1/1 -- one of only two live behaviours that
separate gold2 from gold, so it sits at the top of the measured difficulty band.
Live for models: p=0.25, D=2.43.

NOTE ON FAIRNESS: this behaviour exercises the filter/unit ordering. Under the
original v2.3 task book that order was never stated (measured p=0.06, zero
between-model variance -- a spec gap, not a hard behaviour). The V7 task book
states it explicitly; this file is only fair against that revision.
Source: legacy t4c.
"""
import json

from conftest import emit_mod, ingest_mod, read_jsonl, transform_mod, write_jsonl


def test_chain_normalizes_filters_converts_and_summarises(workdir):
    src = workdir / "in.csv"
    src.write_text(
        "device_id,timestamp,temp,humidity\n"
        "a,2026-08-01T00:00:00+08:00,20,45\n"
        "b,2026-08-01T00:00:01Z,30,55\n"
        "c,2026-08-01T00:00:02+05:30,85,100\n"
        "bad-line-without-commas\n",
        encoding="utf-8",
    )
    cat = workdir / "catalog.jsonl"
    accepted, _ = ingest_mod.ingest(str(src), str(cat))
    assert accepted == 3, f"ingest accepted {accepted}"

    tr = workdir / "transformed.jsonl"
    kept, _ = transform_mod.transform(str(cat), str(tr), filter_expr="temp>25", unit="f")
    assert kept == 2, f"expected 2 kept, got {kept}"
    temps = sorted(r["temp"] for r in read_jsonl(tr))
    assert abs(temps[0] - 86.0) < 1e-9 and abs(temps[1] - 185.0) < 1e-9, f"got {temps}"

    text, stats = emit_mod.emit(str(tr), "json", summary=True)
    doc = json.loads(text)
    assert doc["stats"]["count"] == 2
    assert "summary" in doc
    assert abs(doc["stats"]["mean"] - (86.0 + 185.0) / 2) < 1e-9


def test_chain_timestamps_all_normalized(workdir):
    src = workdir / "in.jsonl"
    write_jsonl(src, [
        {"device_id": "a", "timestamp": "2026-08-01T08:00:00+08:00", "temp": 30.0},
        {"device_id": "b", "timestamp": "2026-08-01T00:00:01Z", "temp": 30.0},
    ])
    cat = workdir / "cat.jsonl"
    ingest_mod.ingest(str(src), str(cat))
    tr = workdir / "t.jsonl"
    transform_mod.transform(str(cat), str(tr))
    stamps = sorted(r["timestamp"] for r in read_jsonl(tr))
    assert stamps == ["2026-08-01T00:00:00Z", "2026-08-01T00:00:01Z"], f"got {stamps}"
