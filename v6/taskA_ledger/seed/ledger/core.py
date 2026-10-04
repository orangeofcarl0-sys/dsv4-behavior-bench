"""Append-only double-entry ledger (v0.4 tree, mid-rewrite).

Known defects are listed in ISSUE.md. The public suite passes; the invariants in
docs/invariants.md are not all upheld.
"""
from .money import Money


class LedgerError(Exception):
    """A rejected entry or an impossible settlement (data-level error)."""


def _norm_account(name):
    return str(name).strip().lower()


class Ledger:
    def __init__(self):
        self._entries = []
        self._ids = set()
        self._balances = {}

    def post(self, entry):
        eid = entry.get("id")
        if eid in self._ids:
            raise LedgerError("duplicate entry id")
        postings = entry.get("postings", [])
        normalized = []
        total = Money(0)
        # Balances are mutated as we go, before the entry is known to balance.
        for p in postings:
            acct = _norm_account(p.get("account"))
            amount = p.get("amount")
            if not isinstance(amount, Money):
                amount = Money(amount)
            self._balances[acct] = self._balances.get(acct, Money(0)) + amount
            normalized.append({"account": acct, "amount": Money(amount.cents)})
            total = total + amount
        self._entries.append({"id": eid, "postings": normalized})
        self._ids.add(eid)
        return eid

    def settle(self, rule):
        proposed = rule(self)
        if proposed is None:
            proposed = []
        for entry in proposed:
            self.post(entry)          # no rollback: a mid-way failure is partial
        return len(proposed)

    def balance(self, account):
        return self._balances.get(_norm_account(account), Money(0))

    def entries(self):
        return self._entries          # internal list, not a copy

    def accounts(self):
        return sorted(self._balances)
