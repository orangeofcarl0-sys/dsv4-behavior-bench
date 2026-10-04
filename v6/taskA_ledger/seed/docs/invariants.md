# Invariants

These guarantees hold for a correct ledger. They are the contract; the public
suite does not check all of them.

## I1 — Double entry balances

Every committed entry's postings sum to exactly zero. The sum of all balances
across all accounts is therefore always zero.

## I2 — Append-only, ordered

`entries()` returns committed entries in the order they were posted. Committed
entries are never reordered, edited, or removed by later operations.

## I3 — Atomic rejection

A rejected entry changes nothing. In particular, a rejected entry must not
consume its `id`: a corrected entry with the same id can still be posted
afterwards. Validation happens **before** any mutation.

## I4 — Atomic settlement

`settle(rule)` is all-or-nothing. If the rule proposes several entries and one of
them is rejected, the ledger is restored exactly to its pre-settlement state:
balances, entries, and used ids all as they were. A settlement either applies
every proposed entry or none.

## I5 — Case-insensitive accounts

Balances and lookups treat account names case-insensitively and trim surrounding
whitespace.

## I6 — Read isolation

`entries()` returns copies. A caller that mutates the returned structure (or a
`Money` in it) must not be able to change the ledger's internal state.

## I7 — Exact arithmetic

Balances are exact integer cents. Repeated posting and settling never
accumulates floating-point error, and a balance of zero is exactly zero.
