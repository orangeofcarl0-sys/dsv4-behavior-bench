"""ledger — an append-only double-entry ledger with a settlement step.

Public API:
    Ledger.post(entry)      -- append an entry
    Ledger.balance(account) -- current balance for one account
    Ledger.settle(rule)     -- apply a settlement rule, atomically
    Ledger.entries()        -- the committed entries, in order
    LedgerError             -- raised for a rejected entry or settlement

Invariants are documented in docs/invariants.md; the entry format in
docs/format.md.
"""
from .core import Ledger, LedgerError
from .money import Money

__all__ = ["Ledger", "LedgerError", "Money"]
