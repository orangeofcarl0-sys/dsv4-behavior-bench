"""Append-only double-entry ledger.

See docs/format.md for the entry format and docs/invariants.md for the rules a
correct implementation guarantees.
"""
from .money import Money


class LedgerError(Exception):
    """A rejected entry or an impossible settlement (data-level error)."""


def _norm_account(name):
    if not isinstance(name, str) or not name.strip():
        raise LedgerError("account name must be a non-empty string")
    return name.strip().lower()


class Ledger:
    def __init__(self):
        self._entries = []
        self._ids = set()
        self._balances = {}

    # -- writes ---------------------------------------------------------------

    def post(self, entry):
        """Validate and append one entry.

        An entry is {"id": str, "postings": [{"account": str, "amount": Money}]}.
        Rejected (LedgerError) if: the id is missing or already used, there are
        fewer than two postings, any account is blank, any amount is zero, or the
        postings do not sum to zero. A rejected entry leaves the ledger unchanged.
        """
        if not isinstance(entry, dict):
            raise LedgerError("entry must be a mapping")
        eid = entry.get("id")
        if not isinstance(eid, str) or not eid:
            raise LedgerError("entry needs a non-empty string id")
        if eid in self._ids:
            raise LedgerError(f"duplicate entry id: {eid}")
        postings = entry.get("postings")
        if not isinstance(postings, list) or len(postings) < 2:
            raise LedgerError("entry needs at least two postings")

        normalized = []
        total = Money(0)
        for p in postings:
            acct = _norm_account(p.get("account"))
            amount = p.get("amount")
            if not isinstance(amount, Money):
                raise LedgerError("posting amount must be Money")
            if amount.cents == 0:
                raise LedgerError("zero-amount postings are not allowed")
            normalized.append((acct, amount))
            total = total + amount
        if total.cents != 0:
            raise LedgerError(f"entry does not balance: {total}")

        # Commit only after every check passed.
        for acct, amount in normalized:
            self._balances[acct] = self._balances.get(acct, Money(0)) + amount
        self._ids.add(eid)
        self._entries.append({
            "id": eid,
            "postings": [{"account": a, "amount": Money(m.cents)} for a, m in normalized],
        })
        return eid

    def settle(self, rule):
        """Apply a settlement rule atomically.

        `rule` is a callable taking the ledger and returning a list of entries to
        post. If any entry is rejected, the whole settlement is rolled back: no
        balances change and no entries are appended. On success all entries are
        posted in order.
        """
        proposed = rule(self)
        if proposed is None:
            proposed = []
        snapshot_entries = list(self._entries)
        snapshot_ids = set(self._ids)
        snapshot_balances = dict(self._balances)
        try:
            for entry in proposed:
                self.post(entry)
        except Exception:
            self._entries = snapshot_entries
            self._ids = snapshot_ids
            self._balances = snapshot_balances
            raise
        return len(proposed)

    # -- reads ----------------------------------------------------------------

    def balance(self, account):
        return self._balances.get(_norm_account(account), Money(0))

    def entries(self):
        """The committed entries in order (deep copies; callers cannot mutate)."""
        out = []
        for e in self._entries:
            out.append({
                "id": e["id"],
                "postings": [{"account": p["account"],
                              "amount": Money(p["amount"].cents)}
                             for p in e["postings"]],
            })
        return out

    def accounts(self):
        return sorted(self._balances)
