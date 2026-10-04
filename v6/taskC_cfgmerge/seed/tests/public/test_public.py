"""Public suite for cfgmerge (do not modify).

Covers the simple cases only: flat merges, nested merges where both sides are
present, and a basic environment read. It is blind to falsy overrides, deletion,
list replacement, env typing, and immutability.
"""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from cfgmerge import load, get, deep_merge


def test_flat_override():
    assert load({"a": 1}, {"a": 2}) == {"a": 2}


def test_nested_both_present():
    r = load({"db": {"host": "h", "port": 1}}, {"db": {"port": 2}})
    assert r == {"db": {"host": "h", "port": 2}}


def test_get_dotted():
    assert get({"db": {"host": "h"}}, "db.host") == "h"


def test_get_missing_default():
    assert get({}, "a.b", "fallback") == "fallback"


def test_deep_merge_adds_new_key():
    assert deep_merge({"a": 1}, {"b": 2}) == {"a": 1, "b": 2}


def test_env_reads_string():
    r = load({}, environ={"APP_NAME": "svc"}, prefix="APP")
    assert r == {"name": "svc"}
