# Error policy

`datapipe` has to survive real telemetry, which always contains some bad rows.
The policy is a single switch, `--on-error`, that decides what a bad record does
to the run. The library exposes the same switch as `on_error=` on every stage
function.

## Two modes

- **`skip` (default).** The bad record is dropped, counted, and the run
  continues. A run that skipped records is still a *success*: it exits `0`.
- **`fail`.** The run stops at the **first** bad record. The library raises
  `DataError`; the CLI exits `1`.

`fail` is the strict dual of `skip`: it stops exactly on the record that `skip`
would have dropped. So the two modes must agree on *which* records are bad —
only the consequence differs.

## What counts as bad

There are three buckets, and conflating them is the most common defect:

| bucket | examples | policy consequence |
|---|---|---|
| malformed record | unparseable JSON line, a non-object record, missing/blank `device_id` or `timestamp`, an unparseable timestamp | dropped under `skip`, stops under `fail` |
| invalid record | a metric outside its allowed range, or a non-finite metric (`NaN`/`Infinity`) | dropped under `skip`, stops under `fail` |
| usable record with an unusable *field* | `temp` is text like `"n/a"`, or a JSON boolean | **kept**; the field normalizes to `null` |

The third row is the subtle one: a record whose temperature cannot be read is
still a record. Only records that are structurally bad, or whose *values* are
outside the domain, are policy events. In particular a non-finite number is not
a "weird but usable" value — it is not a valid reading, so it belongs to the
invalid bucket, not the `null` bucket.

## Errors that are *not* policy events

Some errors are the operator's fault, not the data's, and must never be folded
into `skipped`:

- an unknown flag, an unsupported `--format`, an invalid `--on-error` value;
- a **malformed filter expression** (no operator, empty comparison value, or a
  value that itself starts with an operator).

These are usage errors: the CLI exits `2`, and the library surfaces them as a
`ValueError`. A malformed filter is not "a record we skip" — the command was
wrong, so it stops the same way regardless of `--on-error`.

Conversely, a bug in the program must not be dressed up as a data error. A
broad `except Exception` that turns every unexpected failure into a skipped
record hides real defects; only the *defined* bad-record conditions above feed
the policy.

## Data errors vs usage errors in code

The library distinguishes them by type: `DataError` marks a record-level data
problem, and it is deliberately **not** a `ValueError`, so a caller can tell
"the input was bad" apart from "the call was wrong". See `docs/api.md`.

## Counting

`skipped` counts each bad record exactly once. A record removed by one stage
must not be counted again by a later stage, and a record kept but with a
`null` field is not skipped at all.

## Atomicity

Under `fail`, a run that aborts must not publish a half-written result. The
externally observable contract:

- output did not exist before → it must not exist after;
- output existed before → it must be byte-for-byte unchanged after.

This holds for `ingest --output`, `transform --output`, and `emit --output`. The
implementation technique is not part of the contract (validate-then-write,
write-to-temp-then-rename, and equivalents are all fine); only the observable
file state is.

> Pre-2.4 note: in 2.3 a `transform` run that skipped records returned status 1,
> and failed runs could leave a truncated output. Both are superseded — see
> `CHANGELOG.md`.
