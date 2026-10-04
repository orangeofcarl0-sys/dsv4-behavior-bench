# ISSUE: ledger invariants violated in production

**Reported by:** payments team
**Severity:** critical

The ledger is producing wrong balances and, worse, leaving corrupted state after
failed operations. `docs/invariants.md` states what must hold; the current code
violates several of them.

Observed:

1. **Partial postings on a rejected entry.** Posting an entry that should be
   rejected (e.g. postings that do not sum to zero, or a blank account) leaves
   some of its postings applied to balances, and sometimes appends half an entry.
   The ledger must be unchanged after a rejection (I3).

2. **A rejected id is consumed.** After a rejection, re-posting a corrected entry
   with the same id fails as a "duplicate", even though nothing was committed.

3. **Settlement is not atomic.** When a settlement proposes multiple entries and
   a later one is rejected, the earlier ones stay applied. A settlement must
   apply all of its entries or none (I4).

4. **Float drift.** Balances accumulate floating-point error; a balance that
   should be exactly zero comes back as a tiny nonzero value. Money must be exact
   integer cents (I7), and constructing it from a float must be rejected.

5. **Reads leak.** `entries()` returns internal structures, so a caller mutating
   the result corrupts the ledger (I6).

## What we need

Make the ledger uphold every invariant in `docs/invariants.md`. Keep the public
API (`Ledger`, `post`, `balance`, `settle`, `entries`, `LedgerError`, `Money`)
and the entry format unchanged. Do not modify `tests/`.
