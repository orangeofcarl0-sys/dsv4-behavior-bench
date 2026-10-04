import json
from conftest import run_ingest, read_jsonl
from datapipe import transform as transform_mod


def run_transform(workdir, rows, **kwargs):
    catalog = workdir / "catalog.jsonl"
    catalog.write_text("\n".join(json.dumps(r) for r in rows), encoding="utf-8")
    out = workdir / "transformed.jsonl"
    kept, skipped = transform_mod.transform(str(catalog), str(out), **kwargs)
    return out, kept, skipped, read_jsonl(out)


ROWS = [
    {"device_id": "AB-1", "timestamp": "2026-08-01T10:00:00Z", "temp": 22.5, "humidity": 45},
    {"device_id": "ab-1", "timestamp": "2026-08-01T10:00:00Z", "temp": 23.0, "humidity": 46},
    {"device_id": "cd-2", "timestamp": "2026-08-01T10:05:00+08:00", "temp": 30.0, "humidity": 50},
    {"device_id": "ef-3", "timestamp": "2026-08-01T10:10:00Z", "temp": 90.0, "humidity": 55},
]


def test_dedupe_case_insensitive(workdir):
    _, kept, skipped, rows = run_transform(workdir, ROWS)
    assert kept == 2  # AB-1/ab-1 collapse to one, cd-2 kept, ef-3 dropped as out-of-range


def test_dedupe_keeps_last(workdir):
    _, _, _, rows = run_transform(workdir, ROWS)
    by_id = {r["device_id"]: r for r in rows}
    assert by_id["ab-1"]["temp"] == 23.0


def test_timestamp_utc_z(workdir):
    _, _, _, rows = run_transform(workdir, ROWS)
    assert rows[0]["timestamp"].endswith("Z")


def test_timestamp_offset_converted(workdir):
    _, kept, skipped, rows = run_transform(workdir, ROWS)
    assert kept == 2
    assert any(r["device_id"] == "cd-2" for r in rows)


def test_range_validation(workdir):
    _, _, _, rows = run_transform(workdir, ROWS)
    assert all(r["device_id"] != "ef-3" for r in rows)


def test_filter_numeric(workdir):
    data = [ROWS[0], dict(ROWS[2])]
    _, kept, _, rows = run_transform(workdir, data, filter_expr="temp>25")
    assert kept == 1
    assert rows[0]["device_id"] == "cd-2"


def test_filter_equality(workdir):
    _, kept, _, rows = run_transform(workdir, ROWS, filter_expr="device_id=cd-2")
    assert kept == 1
    assert rows[0]["device_id"] == "cd-2"


def test_unit_conversion(workdir):
    _, _, _, rows = run_transform(workdir, [ROWS[0]], unit="f")
    assert abs(rows[0]["temp"] - (22.5 * 9 / 5 + 32)) < 0.01
