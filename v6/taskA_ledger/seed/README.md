# ledger

An append-only double-entry ledger.

```python
from ledger import Ledger, Money, LedgerError

L = Ledger()
L.post({"id": "e1", "postings": [
    {"account": "cash",   "amount": Money(500)},
    {"account": "revenue", "amount": Money(-500)},
]})
assert L.balance("cash") == Money(500)
```

## Status

v0.4, mid-rewrite toward v1.0. The public suite passes, but the invariants in
`docs/invariants.md` are not all upheld — see `ISSUE.md`.

## Layout

```
ledger/
  __init__.py
  core.py          # Ledger, LedgerError
  money.py         # Money
tests/public/      # public suite (do not modify)
docs/format.md     # entry format
docs/invariants.md # the guarantees
ISSUE.md           # current production report
```
