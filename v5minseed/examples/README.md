# Examples

Worked commands with the output we expect from a correct v2.4 build. These are
illustrative, not a test suite.

## 1. Happy path

```bash
PYTHONPATH=. python3 -m datapipe.cli ingest sample_data/telemetry.csv --output catalog.jsonl
PYTHONPATH=. python3 -m datapipe.cli transform --input catalog.jsonl --output transformed.jsonl
PYTHONPATH=. python3 -m datapipe.cli emit --input transformed.jsonl --format json --summary
```

Exit status `0` throughout. `emit` prints `{"stats": {...}, "rows": [...],
"summary": ...}`.

## 2. Bad records, default policy

`catalog.ndjson`:

```
{"device_id": "a", "timestamp": "2026-08-01T00:00:00Z", "temp": 22}
NOT-JSON
{"device_id": "b", "timestamp": "2026-08-01T00:00:01Z", "temp": 23}
```

```bash
PYTHONPATH=. python3 -m datapipe.cli ingest catalog.ndjson --output cat.jsonl
```

```
ingest: accepted=2 skipped=1
```

Exit status `0` — skipping bad records is a success.

## 3. Same input, `--on-error fail`

```bash
PYTHONPATH=. python3 -m datapipe.cli ingest catalog.ndjson --output cat.jsonl --on-error fail
```

Exit status `1`, an error message on stderr (not a traceback), and `cat.jsonl`
is **not** created. If `cat.jsonl` already existed with old content, it is left
exactly as it was.

## 4. Repeated filters

```bash
PYTHONPATH=. python3 -m datapipe.cli transform --input catalog.jsonl \
    --filter "temp>=20" --filter "humidity<80" --output transformed.jsonl
```

Keeps only records satisfying **both** conditions. Writing the two filters in
the other order keeps the same records.

## 5. Filters before unit conversion

```bash
PYTHONPATH=. python3 -m datapipe.cli transform --input catalog.jsonl \
    --filter "temp>25" --unit f --output transformed.jsonl
```

Selects records whose **celsius** temperature exceeds 25, then converts the
survivors to fahrenheit for output.

## 6. Legacy alias and a real zero

`legacy.ndjson`:

```
{"device_id": "a", "timestamp": "2026-08-01T00:00:00Z", "temperature": 20}
{"device_id": "b", "timestamp": "2026-08-01T00:00:01Z", "temp": 0, "temperature": 99}
```

After ingest, device `a` has `temp = 20.0` (alias used), and device `b` has
`temp = 0.0` (the real zero is kept; `temperature` is ignored).

## 7. Markdown report

```bash
PYTHONPATH=. python3 -m datapipe.cli emit --input transformed.jsonl --format md \
    --summary --output report.md
```

`report.md` contains the table and a `## Summary` section whose `mean` is the
arithmetic mean of the temperatures.
