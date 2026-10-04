# Entry format

```python
{
  "id": "e1",                     # required, non-empty string, unique
  "postings": [                   # required, at least two
    {"account": "cash",    "amount": Money(500)},
    {"account": "revenue", "amount": Money(-500)},
  ],
}
```

## Amounts

`Money` is an **exact integer number of cents**. Constructing `Money` from a
float is not allowed — floating point cannot represent cents exactly and would
make balances drift. Use `Money(500)` for 5.00.

## Accounts

Account names are trimmed and compared **case-insensitively**; `Cash` and
`cash` are the same account. A blank account name is invalid.

## Validation

An entry is rejected (raising `LedgerError`) when:

- `id` is missing, empty, or already used;
- there are fewer than two postings;
- any posting has a blank account;
- any posting amount is zero;
- the postings do not sum to exactly zero.

A rejected entry must leave the ledger **completely unchanged** — no partial
balances, no appended entry, and its id must not be consumed.
