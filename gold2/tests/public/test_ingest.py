from conftest import run_ingest, read_jsonl

CSV = """device_id,timestamp,temp,humidity
ab-1,2026-08-01T10:00:00Z,22.5,45
cd-2,2026-08-01T10:05:00Z,23.1,50
"""


def test_csv_basic(workdir):
    out, accepted, skipped = run_ingest(workdir, CSV)
    rows = read_jsonl(out)
    assert accepted == 2
    assert skipped == 0
    assert rows[0]["device_id"] == "ab-1"
    assert rows[0]["temp"] == 22.5


def test_csv_bom(workdir):
    content = "\ufeff" + CSV
    out, accepted, skipped = run_ingest(workdir, content)
    rows = read_jsonl(out)
    assert accepted == 2
    assert all(r["device_id"] == r["device_id"].strip() for r in rows)
    assert rows[0]["device_id"] == "ab-1"


def test_csv_quoted_commas(workdir):
    content = 'device_id,timestamp,temp,humidity\n"ab,1",2026-08-01T10:00:00Z,22.5,45\n'
    out, accepted, skipped = run_ingest(workdir, content)
    rows = read_jsonl(out)
    assert accepted == 1
    assert rows[0]["device_id"] == "ab,1"


def test_json_list(workdir):
    content = '[{"device_id": "ab-1", "timestamp": "2026-08-01T10:00:00Z", "temp": 22.5}]'
    out, accepted, skipped = run_ingest(workdir, content, name="input.json")
    assert accepted == 1
    assert read_jsonl(out)[0]["temp"] == 22.5


def test_ndjson(workdir):
    content = '{"device_id": "ab-1", "timestamp": "2026-08-01T10:00:00Z", "temp": 22.5}\n{"device_id": "cd-2", "timestamp": "2026-08-01T10:05:00Z", "temp": 23.1}'
    out, accepted, skipped = run_ingest(workdir, content, name="input.ndjson")
    assert accepted == 2
    assert read_jsonl(out)[1]["device_id"] == "cd-2"


def test_skip_invalid_records(workdir):
    content = 'device_id,timestamp,temp,humidity\n,2026-08-01T10:00:00Z,22.5,45\ncd-2,,23.1,50\n'
    out, accepted, skipped = run_ingest(workdir, content)
    assert accepted == 0
    assert skipped == 2
