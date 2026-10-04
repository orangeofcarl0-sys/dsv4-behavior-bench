# Output and statistics

`emit` renders a dataset as JSON, CSV, or Markdown. It reads records and writes
a presentation; it does not change the dataset.

## JSON

```json
{"stats": {...}, "rows": [...]}
```

With `--summary`, a `summary` key is added alongside `stats` and `rows`. Without
it, the document still carries `stats` and `rows`.

## CSV

Header is exactly:

```
device_id,timestamp,temp,humidity
```

Fields containing a comma (or a quote) are quoted so the row re-parses
correctly. A `null` metric is written as an empty cell.

## Markdown

A table plus, optionally, a `## Summary` section. Two rules keep the output
well-formed:

- a `|` inside a cell value is escaped as `\|`;
- a newline inside a cell value becomes a space.

The summary's `mean` is the **arithmetic mean** of the temperatures, not the
mid-range `(min+max)/2`. On symmetric data the two agree; on skewed data they do
not, and the arithmetic mean is correct.

## Statistics

`stats` reports:

- `count` — number of rows;
- `min`, `max`, `mean` — computed over the non-`null` `temp` values only.

When there is no usable `temp` at all, `min`/`max`/`mean` are all `null` and
`count` reflects the rows present (possibly `0`).

## Output is atomic under `fail`

`emit --output` follows the same rule as the other stages: if the run ends in a
data error, an existing output file is left untouched and no new file is
created. See `docs/error-policy.md`.
