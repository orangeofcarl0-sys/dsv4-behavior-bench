# Architecture

Three stages, each a module, connected by files.

```
raw file ──ingest──▶ catalog.jsonl ──transform──▶ transformed.jsonl ──emit──▶ report
```

- **ingest** reads a source file (CSV, a JSON object/array, or NDJSON), picks a
  parser by extension (unknown extensions are sniffed: a leading `{` or `[`
  means JSON/NDJSON, anything else is CSV), and writes a normalized JSONL
  catalog. Normalization covers field aliases, metric typing, and required
  fields. Records that cannot be normalized are handled by the error policy.
- **transform** reads the catalog and produces the cleaned dataset. Its work, in
  order, is: validate metric ranges; collapse duplicate keys (dedupe); apply the
  filter expression(s); then, only if `--unit f` was given, convert `temp`.
- **emit** reads a dataset and renders it as JSON, CSV, or Markdown, optionally
  with a summary. It is a pure reader/serializer: it does not re-order or
  re-filter records.

## Where each rule lives

The split matters because the stages are separately testable and the CLI is a
thin wrapper over them:

- **ingest** owns alias resolution (`device`→`device_id`, `temperature`→`temp`),
  metric typing, and required-field presence.
- **transform** owns ordering: range validation, dedupe, filtering, unit
  conversion. Filtering sees canonical (pre-conversion) values, and a record
  that a later stage removes cannot be brought back by an earlier stage.
- **emit** owns presentation: quoting, escaping, statistics.

## The CLI is a wrapper

`datapipe/cli.py` parses arguments and calls the three module functions. It adds
no semantics of its own beyond argument validation and exit-code mapping; the
library functions must behave identically when called directly. Any behavior a
CLI test observes should be reproducible through the library with the same
arguments, and vice versa.

## Operator ordering is observable

Because transform's steps run in a fixed order, different orderings give
different results on the same input. Two consequences worth stating explicitly,
since they are easy to get wrong:

- Filters compare the values **before** unit conversion. `--filter "temp>25"
  --unit f` means "celsius above 25", not "fahrenheit above 25".
- Dedupe keeps the last record for a key. If filtering ran before dedupe, a
  record that the filter drops could be "replaced" by an earlier duplicate;
  because filtering runs after dedupe, the earlier duplicate stays gone.

> Historical note (pre-2.4): a `transform` run that skipped records returned
> status 1. That is no longer true — see `CHANGELOG.md` and
> `docs/error-policy.md`.
