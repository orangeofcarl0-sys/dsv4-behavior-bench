"""ledger hidden suite — atomicity, id re-use, settlement rollback, exactness,
read isolation.

Every behavior is derivable from docs/invariants.md + docs/format.md + ISSUE.md.
The public suite is deliberately blind to all of it.
"""
import os
import sys
from pathlib import Path

import pytest

REPO = Path(os.environ.get("CANDIDATE_REPO",
                           Path(__file__).resolve().parents[1] / "candidate"))
sys.path.insert(0, str(REPO))

from ledger import Ledger, Money, LedgerError  # noqa: E402


def _entry(eid, pairs):
    return {"id": eid, "postings": [{"account": a, "amount": Money(m)} for a, m in pairs]}


def _snapshot(L):
    return (
        [(e["id"], [(p["account"], p["amount"].cents) for p in e["postings"]])
         for e in L.entries()],
        {a: L.balance(a).cents for a in L.accounts()},
    )


# ── I3: a rejected entry changes nothing ─────────────────────────────────────

def test_i3_unbalanced_entry_rejected_and_no_state_change():
    L = Ledger()
    L.post(_entry("ok", [("a", 100), ("b", -100)]))
    before = _snapshot(L)
    with pytest.raises(LedgerError):
        L.post(_entry("bad", [("a", 100), ("b", -50)]))
    assert _snapshot(L) == before, "rejected entry mutated the ledger"


def test_i3_single_posting_rejected():
    L = Ledger()
    with pytest.raises(LedgerError):
        L.post(_entry("one", [("a", 100)]))
    assert L.entries() == [] and L.accounts() == []


def test_i3_zero_amount_rejected():
    L = Ledger()
    with pytest.raises(LedgerError):
        L.post(_entry("z", [("a", 0), ("b", 0)]))
    assert _snapshot(L) == ([], {})


def test_i3_blank_account_rejected():
    L = Ledger()
    with pytest.raises(LedgerError):
        L.post(_entry("blank", [("  ", 100), ("b", -100)]))
    assert L.accounts() == []


# ── I3b: a rejected id is not consumed ───────────────────────────────────────

def test_i3b_id_reusable_after_rejection():
    L = Ledger()
    with pytest.raises(LedgerError):
        L.post(_entry("e1", [("a", 100), ("b", -50)]))
    L.post(_entry("e1", [("a", 100), ("b", -100)]))   # corrected, same id
    assert [e["id"] for e in L.entries()] == ["e1"]
    assert L.balance("a") == Money(100)


# ── I4: settlement is atomic ─────────────────────────────────────────────────

def test_i4_settlement_all_or_nothing():
    L = Ledger()
    L.post(_entry("base", [("a", 10), ("b", -10)]))
    before = _snapshot(L)

    def rule(_):
        return [
            _entry("s1", [("a", 5), ("b", -5)]),      # valid
            _entry("s2", [("a", 7), ("b", -3)]),      # unbalanced -> reject
        ]

    with pytest.raises(LedgerError):
        L.settle(rule)
    assert _snapshot(L) == before, "settlement was not rolled back"


def test_i4_settlement_success_applies_all():
    L = Ledger()
    L.post(_entry("base", [("a", 10), ("b", -10)]))

    def rule(_):
        return [_entry("s1", [("a", 5), ("b", -5)]),
                _entry("s2", [("a", 2), ("b", -2)])]

    assert L.settle(rule) == 2
    assert L.balance("a") == Money(17)
    assert sorted(e["id"] for e in L.entries()) == ["base", "s1", "s2"]


# ── I7: exact integer arithmetic ─────────────────────────────────────────────

def test_i7_exact_zero_after_cancelling_postings():
    L = Ledger()
    for i in range(50):
        L.post(_entry(f"e{i}", [("a", 10), ("b", -10)]))
        L.post(_entry(f"f{i}", [("a", -10), ("b", 10)]))
    assert L.balance("a").cents == 0, L.balance("a").cents


def test_i7_money_rejects_float():
    with pytest.raises(TypeError):
        Money(1.5)


# ── I6: read isolation ───────────────────────────────────────────────────────

def test_i6_entries_returns_copies():
    L = Ledger()
    L.post(_entry("e1", [("a", 100), ("b", -100)]))
    snap = L.entries()
    snap[0]["postings"][0]["amount"] = Money(999999)
    snap.append({"id": "injected", "postings": []})
    assert [e["id"] for e in L.entries()] == ["e1"]
    assert L.balance("a") == Money(100)


# ── I5: case-insensitive and trimmed accounts ────────────────────────────────

def test_i5_case_and_whitespace_insensitive():
    L = Ledger()
    L.post(_entry("e1", [("  Cash ", 100), ("revenue", -100)]))
    assert L.balance("cash") == Money(100)
    assert L.balance("CASH") == Money(100)


# ── I1/I2: double-entry and ordering ─────────────────────────────────────────

def test_i1_global_balance_zero():
    L = Ledger()
    L.post(_entry("e1", [("a", 30), ("b", -10), ("c", -20)]))
    assert sum(L.balance(a).cents for a in L.accounts()) == 0


def test_i2_order_preserved():
    L = Ledger()
    for i in range(5):
        L.post(_entry(f"e{i}", [("a", 1), ("b", -1)]))
    assert [e["id"] for e in L.entries()] == [f"e{i}" for i in range(5)]
