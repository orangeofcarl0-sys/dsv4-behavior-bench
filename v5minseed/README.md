# datapipe

A CLI pipeline for device telemetry: `ingest → transform → emit`.

```
raw file        catalog.jsonl      cleaned dataset     report
(CSV/JSON/NDJSON)  normalized       deduped/filtered    json/csv/md
```

## Status

`main` is between releases: **v2.2.1 is the last shipped version, and the v2.4
upgrade is only half done.** The tree already contains a partial v2.4 attempt
(see `CHANGELOG.md`), so some v2.4 flags parse but do not behave as documented.
Treat `CHANGELOG.md` + `docs/` as the contract and the source as suspect.

## Quickstart

```bash
python3 tools/run_public_tests.py     # public suite (incomplete, see below)
python3 tools/run_debug_probe.py      # same tests, verbose

PYTHONPATH=. python3 -m datapipe.cli ingest sample_data/telemetry.csv
PYTHONPATH=. python3 -m datapipe.cli transform --input catalog.jsonl \
    --filter "temp>=20" --filter "humidity<80" --unit f
PYTHONPATH=. python3 -m datapipe.cli emit --input transformed.jsonl --format md --summary
```

More worked examples: `examples/`.

## Exit codes

The CLI distinguishes *the data was bad* from *you used it wrong*. Downstream
automation relies on this, so the mapping is part of the interface:

| code | meaning |
|---|---|
| `0` | success — including a run that skipped some bad records |
| `1` | data error — input missing/unreadable, or a bad record that policy refuses to skip |
| `2` | usage / config error — unknown flag, unsupported format, bad flag value, malformed filter expression |

`docs/error-policy.md` explains the skip/fail policy and why a bad *filter*
is a usage error while a bad *record* is a data error.

## Docs

- `docs/architecture.md` — stages, operator ordering, what each module owns.
- `docs/error-policy.md` — `--on-error`, error classification, atomic output.
- `docs/data-model.md` — fields, normalization, legacy fallback, ranges.
- `CHANGELOG.md` — per-version behavior, including intentional changes.
- `examples/` — commands with expected output.

## Known issues

- `tests/public/` is a smoke suite from the v2.2 era. It does **not** cover the
  v2.4 error policy, multi-filter behavior, or output atomicity, and several
  cases already fail on this tree.
- `datapipe/PULL_REQUEST_TEMPLATE.md` is the delivery report format we expect
  for any fix landing on this repo.
