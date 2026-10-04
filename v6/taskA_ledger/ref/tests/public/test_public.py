"""Public suite for ledger (do not modify).

Covers basic posting and balances. It is blind to atomicity, id re-use after
rejection, settlement rollback, exactness, and read isolation.
"""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from ledger import Ledger, Money, LedgerError


def test_post_and_balance():
    L = Ledger()
    L.post({"id": "e1", "postings": [
        {"account": "cash", "amount": Money(500)},
        {"account": "revenue", "amount": Money(-500)},
    ]})
    assert L.balance("cash") == Money(500)
    assert L.balance("revenue") == Money(-500)


def test_balance_sums_to_zero():
    L = Ledger()
    L.post({"id": "e1", "postings": [
        {"account": "a", "amount": Money(100)},
        {"account": "b", "amount": Money(-100)},
    ]})
    assert L.balance("a") + L.balance("b") == Money(0)


def test_case_insensitive_account():
    L = Ledger()
    L.post({"id": "e1", "postings": [
        {"account": "Cash", "amount": Money(10)},
        {"account": "cash", "amount": Money(-10)},
    ]})
    assert L.balance("CASH") == Money(0)


def test_entries_listed():
    L = Ledger()
    L.post({"id": "e1", "postings": [
        {"account": "a", "amount": Money(1)},
        {"account": "b", "amount": Money(-1)},
    ]})
    assert [e["id"] for e in L.entries()] == ["e1"]


def test_money_str():
    assert str(Money(1234)) == "12.34"
    assert str(Money(-5)) == "-0.05"
