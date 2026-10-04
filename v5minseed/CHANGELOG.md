# Changelog

All notable behavior of the `datapipe` CLI. Entries describe **user-visible**
behavior, not implementation. When a note here contradicts a comment or doc
elsewhere, the newest released version wins.

## v2.4.0 — in progress (NOT released)

Target of the current upgrade. The tree has a partial attempt; nothing below is
guaranteed to actually work yet.

- **New error policy** `--on-error skip|fail` (CLI and library). `skip` is the
  default and preserves the pre-2.4 behavior: bad records are dropped, counted,
  and processing continues. `fail` stops at the **first** bad record.
- **A command that merely skipped bad records is a success.** In 2.3 a run that
  skipped anything still returned a non-zero status; from 2.4 a clean exit is
  `0` even when records were skipped, and only `fail` mode (or unreadable input)
  is a data error.
- **Failed runs must not leave partial output.** A command that ends in a data
  error leaves any pre-existing output file byte-for-byte untouched, and never
  creates a new one. This applies to `ingest --output`, `transform --output`
  and `emit --output` alike.
- **Repeated `--filter`** is allowed and combines with AND. A single `--filter`
  keeps its 2.3 meaning. Filter expressions are unchanged from 2.3.
- The library gains an `on_error=` argument on `ingest`/`transform`/`emit` and a
  `filters=[...]` list on `transform`; see `docs/api.md`.
- **Non-finite metrics are invalid, not missing.** `NaN` / `Infinity` /
  `-Infinity` (as a number or as a string) are a record-level data error under
  the error policy — the record is skipped (or fails the run). They must never
  be normalized to `null` and kept.

## v2.3.0

Feature/robustness release. Adds the normalization and output behavior the
pipeline still relies on.

- Range validation on metrics; out-of-range records are rejected, not clamped.
- Dedupe collapses `(device_id, timestamp)` to the **last** occurrence.
- `device_id` is matched case-insensitively for dedupe.
- Timestamps are normalized to UTC ISO-8601 ending in `Z`, preserving
  fractional seconds.
- `--unit f` converts `temp` with `C * 9 / 5 + 32`.
- Markdown report mean is the arithmetic mean; cell values containing `|` are
  escaped so the table stays well-formed.
- CSV output quotes fields that contain commas.

### Fixed in 2.3.0

- `temp = 0` was treated as "missing" and fell back to the legacy `temperature`
  field, silently replacing a real 0 °C reading. `0` is a valid value and no
  longer falls back; only an absent, `null`, or empty/whitespace `temp` does.
- CSV output with a UTF-8 BOM was mis-parsed on re-ingest.

### Known 2.3 behavior we are changing in 2.4

- In 2.3, `transform` returned exit status 1 whenever it skipped records. Some
  scripts keyed off that. **2.4 makes skip a success (0)**; see the 2.4 note
  above. Do not preserve the 2.3 exit status.

## v2.2.1

Last shipped release. `ingest → transform → emit` with JSON/CSV/Markdown output
and the public smoke suite in `tests/public/`.

## v2.2.0

- Legacy `temperature` field is accepted as an alias for `temp`.
- `device` is accepted as an alias for `device_id` when the latter is absent.
