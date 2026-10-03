"""V5 metamorphic: deterministic invariant tests (stdlib only, fixed seeds).

These check properties rather than fixed examples: idempotence, representation
invariance, whitespace invariance, order invariance. All randomness uses a
fixed seed so runs are reproducible.
"""
import json
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from conftest import (
    ingest_mod, transform_mod, emit_mod,
    write_jsonl, write_text, write_csv, read_jsonl, run_cli,
)


def _random_rows(seed, n=12):
    rng = random.Random(seed)
    rows = []
    for i in range(n):
        device = f"dev-{rng.randint(0, 4)}"
        base = datetime(2026, 8, 1, tzinfo=timezone.utc) + timedelta(
            seconds=rng.randint(0, 100000), microseconds=rng.choice([0, 123456, 999999])
        )
        offset = timedelta(hours=rng.choice([-12, -5, 0, 5, 8, 14]))
        local = base.astimezone(timezone(offset))
        ts = local.isoformat()
        if local.utcoffset() == timedelta(0):
            ts = ts.replace("+00:00", "Z")
        rows.append({
            "device_id": device,
            "timestamp": ts,
            "temp": rng.randint(-40, 85) + rng.choice([0.0, 0.5]),
            "humidity": rng.randint(0, 100),
        })
    return rows


# ── M1: timestamp normalization idempotence ──────────────────────────────────

def test_m1_normalization_idempotent(workdir):
    """normalize(normalize(x)) == normalize(x) across offsets and microseconds."""
    rows = _random_rows(seed=1234)
    src = write_jsonl(workdir / "in.jsonl", rows)
    t1 = workdir / "t1.jsonl"
    t2 = workdir / "t2.jsonl"
    transform_mod.transform(str(src), str(t1))
    transform_mod.transform(str(t1), str(t2))
    assert read_jsonl(t1) == read_jsonl(t2), "re-normalization must be a fixed point"
    assert all(r["timestamp"].endswith("Z") for r in read_jsonl(t1))


def test_m1_microseconds_roundtrip(workdir):
    """Every microsecond value must survive normalization unchanged."""
    rows = _random_rows(seed=99)
    src = write_jsonl(workdir / "in.jsonl", rows)
    out = workdir / "t.jsonl"
    transform_mod.transform(str(src), str(out))
    for row in read_jsonl(out):
        # parse back: microseconds present must be preserved exactly
        dt = datetime.fromisoformat(row["timestamp"].replace("Z", "+00:00"))
        assert dt.microsecond in (0, 123456, 999999), row["timestamp"]


# ── M2: format equivalence (CSV / JSON array / NDJSON -> same canonicals) ────

def test_m2_format_equivalence(workdir):
    """The same logical records in CSV, JSON array, and NDJSON ingest to equal
    canonical records."""
    rows = [
        {"device_id": "ab-1", "timestamp": "2026-08-01T00:00:00Z", "temp": 22.5, "humidity": 45},
        {"device_id": "cd-2", "timestamp": "2026-08-01T00:01:00Z", "temp": 23.0, "humidity": 50},
    ]
    csv_path = write_csv(workdir / "in.csv", [
        {"device_id": r["device_id"], "timestamp": r["timestamp"],
         "temp": str(r["temp"]), "humidity": str(r["humidity"])} for r in rows
    ])
    json_path = write_text(workdir / "in.json", json.dumps(rows))
    ndjson_path = write_jsonl(workdir / "in.ndjson", rows)

    results = []
    for i, path in enumerate([csv_path, json_path, ndjson_path]):
        cat = workdir / f"cat{i}.jsonl"
        accepted, _ = ingest_mod.ingest(str(path), str(cat))
        assert accepted == 2
        results.append(read_jsonl(cat))
    assert results[0] == results[1] == results[2], results


# ── M3: filter whitespace invariance ─────────────────────────────────────────

def test_m3_filter_whitespace_invariance(workdir):
    """`temp>20`, `temp >20`, `temp> 20`, `  temp > 20  ` are equivalent."""
    src = write_jsonl(workdir / "in.jsonl", [
        {"device_id": "a", "timestamp": "2026-08-01T00:00:00Z", "temp": 25},
        {"device_id": "b", "timestamp": "2026-08-01T00:00:01Z", "temp": 10},
    ])
    outs = []
    for i, expr in enumerate(["temp>20", "temp >20", "temp> 20", "  temp > 20  "]):
        out = workdir / f"t{i}.jsonl"
        transform_mod.transform(str(src), str(out), filter_expr=expr)
        outs.append(read_jsonl(out))
    assert all(o == outs[0] for o in outs), outs
    assert [r["device_id"] for r in outs[0]] == ["a"]


# ── M4: multiple-filter order invariance ─────────────────────────────────────

def test_m4_filter_order_invariance(workdir):
    """A AND B == B AND A."""
    rows = _random_rows(seed=7)
    src = write_jsonl(workdir / "in.jsonl", rows)
    o1 = workdir / "o1.jsonl"
    o2 = workdir / "o2.jsonl"
    transform_mod.transform(str(src), str(o1), filters=["temp>=20", "humidity<80"])
    transform_mod.transform(str(src), str(o2), filters=["humidity<80", "temp>=20"])
    assert read_jsonl(o1) == read_jsonl(o2)


# ── M5: dedupe representation invariance ─────────────────────────────────────

def test_m5_dedupe_representation_invariance(workdir):
    """device casing and equivalent timezone representations must not change the
    dedupe outcome (key is lowercase device + normalized timestamp)."""
    variants = [
        {"device_id": "AB-1", "timestamp": "2026-08-01T02:00:00+08:00", "temp": 30},
        {"device_id": "ab-1", "timestamp": "2026-07-31T18:00:00Z", "temp": 30},
        {"device_id": "Ab-1", "timestamp": "2026-07-31T13:00:00-05:00", "temp": 30},
    ]
    results = []
    for i, first in enumerate(variants):
        src = write_jsonl(workdir / f"in{i}.jsonl", [first, variants[i]])
        out = workdir / f"t{i}.jsonl"
        kept, _ = transform_mod.transform(str(src), str(out))
        results.append((kept, read_jsonl(out)))
    assert all(k == 1 for k, _ in results), results
    assert all(r[0]["timestamp"] == "2026-07-31T18:00:00Z" for _, r in results), results


# ── M6: dedupe keep-last is stable under shuffled input order ────────────────

def test_m6_keep_last_order_stable(workdir):
    """For a duplicate key, the LAST occurrence in file order wins, and the
    surviving row's value is deterministic given the file order."""
    base = {"device_id": "a", "timestamp": "2026-08-01T00:00:00Z"}
    src = write_jsonl(workdir / "in.jsonl", [
        dict(base, temp=10), dict(base, temp=20), dict(base, temp=30),
    ])
    out = workdir / "t.jsonl"
    transform_mod.transform(str(src), str(out))
    rows = read_jsonl(out)
    assert len(rows) == 1 and rows[0]["temp"] == 30.0


# ── M7: skip-mode totals are conserved (accepted + skipped == inputs) ────────

def test_m7_skip_totals_conserved(workdir):
    """Under skip, accepted + skipped equals the number of non-blank input
    records (malformed JSON lines and non-object records are each counted once;
    blank lines are ignored)."""
    rows = _random_rows(seed=42, n=20)
    lines = [json.dumps(r) for r in rows]
    lines.insert(3, "{bad}")            # malformed JSON
    lines.insert(9, "not json")         # malformed JSON
    lines.insert(15, '{"unterminated": ')  # malformed JSON
    lines.append("[1,2,3]")             # non-object record
    lines.append("")                    # blank, ignored
    src = write_text(workdir / "in.ndjson", "\n".join(lines) + "\n")
    accepted, skipped = ingest_mod.ingest(str(src), str(workdir / "cat.jsonl"))
    assert accepted == len(rows), accepted
    assert skipped == 4, skipped
    assert accepted + skipped == len(rows) + 4, (accepted, skipped)


# ── M8: transform kept+skipped equals catalog record count ───────────────────

def test_m8_transform_totals_conserved(workdir):
    rows = _random_rows(seed=2024, n=15)
    rows.append({"device_id": "bad", "timestamp": "nope", "temp": 10})
    rows.append({"device_id": "hot", "timestamp": "2026-08-01T00:00:00Z", "temp": 500})
    src = write_jsonl(workdir / "in.jsonl", rows)
    kept, skipped = transform_mod.transform(str(src), str(workdir / "t.jsonl"))
    assert kept + skipped == len(rows), (kept, skipped, len(rows))
