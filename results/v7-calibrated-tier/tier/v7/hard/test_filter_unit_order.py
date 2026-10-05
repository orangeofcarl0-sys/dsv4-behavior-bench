"""Behaviour: filter compares the ORIGINAL celsius value; --unit converts after.

This is a FORMER SPEC GAP. Under the v2.3 task book the order was never stated,
every model family implemented the other reading, and the three legacy tests for
it sat at p=0.06 with zero between-model variance -- i.e. the legacy suite was
scoring a rule it had never published.

The V7 task book states the order explicitly, so this becomes a fair inference
item. Its verdict is UNMEASURED until the V7 pilot runs: the p and D below are
from the unstated-spec condition and must not be reused as calibration.
"""
from conftest import read_jsonl, transform_mod, write_jsonl


def test_filter_uses_celsius_not_fahrenheit(workdir):
    src = workdir / "in.jsonl"
    write_jsonl(src, [
        {"device_id": "a", "timestamp": "2026-08-01T00:00:00Z", "temp": 20.0},  # 68F
        {"device_id": "b", "timestamp": "2026-08-01T00:01:00Z", "temp": 30.0},  # 86F
    ])
    out = workdir / "t.jsonl"
    kept, _ = transform_mod.transform(str(src), str(out), filter_expr="temp>25", unit="f")
    rows = read_jsonl(out)
    assert kept == 1 and rows[0]["device_id"] == "b", f"kept={kept} rows={rows}"
    assert abs(rows[0]["temp"] - 86.0) < 1e-9, f"got {rows[0]['temp']!r}"


def test_filter_survives_reordering_of_records(workdir):
    """same contract, records in the other order -- guards against an order-dependent fix"""
    src = workdir / "in.jsonl"
    write_jsonl(src, [
        {"device_id": "b", "timestamp": "2026-08-01T00:01:00Z", "temp": 30.0},
        {"device_id": "a", "timestamp": "2026-08-01T00:00:00Z", "temp": 20.0},
    ])
    out = workdir / "t.jsonl"
    kept, _ = transform_mod.transform(str(src), str(out), filter_expr="temp>25", unit="f")
    rows = read_jsonl(out)
    assert kept == 1 and rows[0]["device_id"] == "b", f"kept={kept} rows={rows}"
    assert abs(rows[0]["temp"] - 86.0) < 1e-9
