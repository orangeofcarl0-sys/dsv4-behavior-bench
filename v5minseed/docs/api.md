# Library API

The CLI is a wrapper over these functions; calling them directly must give the
same results as the equivalent command.

```python
from datapipe import ingest, transform, emit, DataError
```

## `ingest(path, out, on_error="skip") -> (accepted, skipped)`

Reads `path` (CSV / JSON / NDJSON), writes a normalized JSONL catalog to `out`,
and returns the number of accepted and skipped records.

## `transform(catalog, out, filter_expr=None, dedupe=True, unit=None, filters=None, on_error="skip") -> (kept, skipped)`

Reads a catalog, writes the cleaned dataset to `out`, and returns the number of
kept and skipped records.

- `filter_expr` — a single filter expression (the 2.3 form).
- `filters` — a list of filter expressions. If both `filter_expr` and `filters`
  are given they are merged, and all filters combine with AND (see
  `docs/filters.md`).
- `dedupe` — set to `False` to disable dedupe (`--no-dedupe`).
- `unit` — `"f"` converts `temp` to fahrenheit; `None`/`"c"` leaves it celsius.
- `on_error` — `"skip"` (default) or `"fail"`.

## `emit(records_path, fmt, out_path=None, summary=False, on_error="skip") -> (text, stats)`

Renders records as `fmt` (`"json"`, `"csv"`, `"md"`). With `out_path=None` the
rendered text is returned (and the CLI prints it); with `out_path` set it is
written to that file. `stats` is the statistics dict described in
`docs/emit.md`.

## Errors

```python
class DataError(Exception): ...
```

`DataError` is raised for record-level data errors under `on_error="fail"`. It
represents *bad data*. Usage errors — a malformed filter, an unknown option, an
unsupported format — are *bad calls* and are reported as `ValueError` (CLI exit
`2`).

`DataError` is intentionally **not** a subclass of `ValueError`. Callers rely on
being able to separate the two with a single `except` clause each:

```python
try:
    transform(src, out, filter_expr=expr, on_error="fail")
except DataError:      # the input data was bad
    ...
except ValueError:     # the call itself was wrong
    ...
```

If `DataError` were a `ValueError`, the first clause could never distinguish the
two cases, and a caller would be forced to inspect strings. Keep them distinct.

## Equivalence with the CLI

For the same input and the same `on_error`, the library and the CLI agree:
whatever the library raises as `DataError`, the CLI reports as exit `1`; whatever
the library raises as `ValueError`, the CLI reports as exit `2`. The counts they
report for the same run match as well.
