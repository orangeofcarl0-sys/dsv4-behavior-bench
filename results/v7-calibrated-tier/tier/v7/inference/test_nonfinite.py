"""Behaviour: NaN / Infinity / -Infinity are record-level invalid -- rejected, never
normalised to null and kept.

Anchor: seed 0/1, gold 1/1, gold2 1/1. Live for models: p=0.58, D=1.37.
This is the behaviour that the V5 v2.4.1 errata had to add coverage for; here it is
a first-class scored behaviour instead of a late patch.
Source: legacy d112 / d113 / d117.
"""
from conftest import transform_mod, read_jsonl, write_jsonl


def _transform(src, out, **kw):
    return transform_mod.transform(str(src), str(out), **kw)


def test_nan_rejected(workdir):
    src = workdir / "in.jsonl"
    write_jsonl(src, [{"device_id": "a", "timestamp": "2026-08-01T00:00:00Z", "temp": "nan"}])
    out = workdir / "t.jsonl"
    kept, skipped = _transform(src, out)
    assert kept == 0 and skipped == 1, f"nan must count as invalid, got ({kept},{skipped})"


def test_inf_rejected(workdir):
    src = workdir / "in.jsonl"
    write_jsonl(src, [{"device_id": "a", "timestamp": "2026-08-01T00:00:00Z", "temp": "inf"}])
    out = workdir / "t.jsonl"
    kept, skipped = _transform(src, out)
    assert kept == 0 and skipped == 1, f"inf must count as invalid, got ({kept},{skipped})"


def test_negative_infinity_rejected(workdir):
    src = workdir / "in.jsonl"
    write_jsonl(src, [{"device_id": "a", "timestamp": "2026-08-01T00:00:00Z", "temp": "-Infinity"}])
    out = workdir / "t.jsonl"
    kept, skipped = _transform(src, out)
    assert kept == 0 and skipped == 1, f"-Infinity must count as invalid, got ({kept},{skipped})"


def test_nan_never_reaches_output(workdir):
    src = workdir / "in.jsonl"
    write_jsonl(src, [{"device_id": "a", "timestamp": "2026-08-01T00:00:00Z", "temp": float("nan")}])
    out = workdir / "t.jsonl"
    _transform(src, out)
    if out.exists():
        text = out.read_text(encoding="utf-8")
        assert "NaN" not in text and "nan" not in text, f"non-finite leaked: {text!r}"
