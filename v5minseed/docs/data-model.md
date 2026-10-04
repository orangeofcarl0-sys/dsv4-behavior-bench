# Data model

Every record that survives `ingest` has four fields:

| field | type | notes |
|---|---|---|
| `device_id` | string | required; trimmed |
| `timestamp` | string | required; normalized to UTC ISO-8601 `…Z` |
| `temp` | float or `null` | celsius |
| `humidity` | float or `null` | percent |

## Required fields

`device_id` and `timestamp` must be present and non-blank. Their absence is a
malformed record (see `docs/error-policy.md`), not a `null` field. Leading and
trailing whitespace is trimmed.

## Field aliases

Older exporters used different names, and the pipeline keeps accepting them:

- `device` is accepted when `device_id` is absent.
- `temperature` is accepted as an alias for `temp`.

The `temperature` fallback applies only when `temp` is genuinely absent, `null`,
or an empty/whitespace string. A present, usable value — **including `0`** — is
used as-is and does not fall back. This was a real bug once: a `temp` of `0`
fell back to `temperature` and silently replaced a valid 0 °C reading with some
other number. `0` is a temperature.

## Metric typing

`temp` and `humidity` are normalized to `float`, or to `null` when the value
cannot be read as a number. Text like `"n/a"` and JSON booleans (`true`/`false`)
are not numbers and normalize to `null`. A record is kept in this case.

A value that parses to a **non-finite** float — `NaN`, `Infinity`, `-Infinity`,
whether written as a number or as a string — is a different story: it is not a
usable reading. It is a record-level data error handled by the error policy
(skipped, or fails the run); it is never normalized to `null` and kept.

## Timestamps

Timestamps are normalized to UTC and rendered as ISO-8601 ending in `Z`,
**preserving fractional seconds**. A timestamp with an explicit UTC offset is
converted, so `2026-08-01T02:00:00+08:00` and `2026-07-31T18:00:00Z` are the
same instant. A timestamp that cannot be parsed is a malformed record.

Normalization is idempotent: running the normalizer over already-normalized
timestamps changes nothing.

## Ranges

- `temp` ∈ [-40, 85] (°C)
- `humidity` ∈ [0, 100] (%)

A value outside its range is an invalid record. A `null` value passes range
validation (there is nothing to check).

## Dedupe

A duplicate is two records with the same `(device_id, timestamp)` key, where
`device_id` is compared **case-insensitively** and the timestamp is the
normalized instant. The pipeline keeps the **last** occurrence; earlier ones are
dropped. `--no-dedupe` turns this off.

Because normalization happens first, records that look different in the source
(`AB-1` vs `ab-1`, or two equivalent timezone renderings of the same instant)
collapse to one key.

## Representation independence

A record's meaning does not depend on how it was stored. In particular, a
dataset written as CSV by `emit` and read back by `ingest` yields the same
canonical records as the JSONL it came from, provided no information was lost in
the CSV encoding (CSV has no native `null`, so an absent humidity round-trips as
`null` only because empty cells map back to `null`).
