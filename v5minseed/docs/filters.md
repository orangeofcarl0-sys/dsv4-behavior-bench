# Filters

`transform` accepts zero or more filters. Each filter is a single comparison:

```
field OP value
```

## Operators

`>=` `<=` `!=` `>` `<` `=`.

## Whitespace

Whitespace around the field, operator, and value is free: `temp>20`,
`temp >20`, `temp> 20`, and `  temp > 20  ` are the same filter.

## Comparison

When both the field value and the comparison value parse as numbers, the
comparison is numeric; otherwise it is a string comparison. A record whose field
is missing (`null`) does not match any filter.

## Multiple filters

`--filter` may be repeated, and the filters combine with **AND**: a record is
kept only if it satisfies *every* filter.

```bash
--filter "temp>=20" --filter "humidity<80"
```

keeps only records where both conditions hold.

AND is commutative and associative, so the order the filters are written in does
not change the result: `A B` and `B A` keep the same records. The library
`filters=[...]` list behaves the same as repeated `--filter`, and a single
`filter_expr=` is equivalent to a one-element `filters` list; if both are given
they merge and all combine with AND.

## A filter is not a policy event

A malformed filter — no operator, an empty comparison value, or a value that
itself begins with an operator (e.g. `temp>>20`, `temp>`) — is a **usage
error**, not a bad record. It exits `2` and is never counted as a skipped
record, regardless of `--on-error`. The command was wrong, not the data.

## Filters and unit conversion

Filters always compare canonical values, i.e. the values *before* any `--unit f`
conversion. `--filter "temp>25" --unit f` means "celsius above 25"; the
surviving rows are then converted for output.
