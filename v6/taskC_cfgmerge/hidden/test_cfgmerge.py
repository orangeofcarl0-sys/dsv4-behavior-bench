"""cfgmerge hidden suite — precedence, deletion, list replacement, env typing,
immutability.

Every behavior is derivable from docs/precedence.md + ISSUE.md. The public suite
is deliberately blind to all of it.
"""
import os
import sys
from pathlib import Path

import pytest

REPO = Path(os.environ.get("CANDIDATE_REPO",
                           Path(__file__).resolve().parents[1] / "candidate"))
sys.path.insert(0, str(REPO))

from cfgmerge import load, get, deep_merge  # noqa: E402


# ── P1: per-leaf merge of nested tables ──────────────────────────────────────

def test_p1_nested_leaf_merge_file():
    r = load({"db": {"host": "localhost", "port": 5432, "user": "app"}},
             {"db": {"port": 6000}})
    assert r == {"db": {"host": "localhost", "port": 6000, "user": "app"}}, r


def test_p1_nested_leaf_merge_three_layers():
    r = load({"a": {"x": 1, "y": 2}},
             {"a": {"y": 3, "z": 4}},
             {"APP_A__X": "9"}, prefix="APP",
             cli_overrides={"a": {"z": 5}})
    assert r == {"a": {"x": 9, "y": 3, "z": 5}}, r


# ── P2: falsy values are real values ─────────────────────────────────────────

def test_p2_false_overrides_true():
    assert load({"flag": True}, {"flag": False}) == {"flag": False}


def test_p2_zero_overrides_nonzero():
    assert load({"port": 5432}, {"port": 0}) == {"port": 0}


def test_p2_empty_string_overrides():
    assert load({"name": "svc"}, {"name": ""}) == {"name": ""}


def test_p2_falsy_in_nested_table():
    r = load({"srv": {"on": True, "port": 80}}, {"srv": {"on": False}})
    assert r == {"srv": {"on": False, "port": 80}}, r


# ── P3: None deletes a key ───────────────────────────────────────────────────

def test_p3_none_deletes_top_level():
    assert load({"a": 1, "b": 2}, {"a": None}) == {"b": 2}


def test_p3_none_deletes_nested():
    r = load({"db": {"host": "h", "port": 1}}, {"db": {"port": None}})
    assert r == {"db": {"host": "h"}}, r


# ── P4: lists are replaced, not merged ───────────────────────────────────────

def test_p4_list_replaced():
    assert load({"tags": [1, 2, 3]}, {"tags": [9]}) == {"tags": [9]}


def test_p4_list_replaced_by_empty():
    assert load({"tags": [1, 2]}, {"tags": []}) == {"tags": []}


# ── P5: environment layer typing and nesting ─────────────────────────────────

def test_p5_env_nested_and_typed():
    env = {"APP_DB__HOST": "prod", "APP_DEBUG": "true", "APP_WORKERS": "8",
           "APP_NAME": "svc", "OTHER_X": "nope"}
    r = load({}, environ=env, prefix="APP")
    assert r == {"db": {"host": "prod"}, "debug": True, "workers": 8,
                 "name": "svc"}, r


def test_p5_env_false_and_case_insensitive():
    r = load({}, environ={"APP_ON": "FALSE"}, prefix="APP")
    assert r == {"on": False}, r


def test_p5_env_overrides_file():
    r = load({"port": 1}, {"port": 2}, {"APP_PORT": "3"}, prefix="APP")
    assert r == {"port": 3}, r


# ── P6: full precedence order defaults < file < env < cli ────────────────────

def test_p6_precedence_order():
    r = load({"a": "default", "b": "default", "c": "default", "d": "default"},
             {"a": "file", "b": "file", "c": "file"},
             {"APP_A": "env", "APP_B": "env"}, prefix="APP",
             cli_overrides={"a": "cli"})
    assert r == {"a": "cli", "b": "env", "c": "file", "d": "default"}, r


# ── P7: immutability of inputs ───────────────────────────────────────────────

def test_p7_defaults_not_mutated():
    d = {"db": {"host": "h"}, "tags": [1]}
    load(d, {"db": {"port": 2}}, {"APP_TAGS": "x"}, prefix="APP",
         cli_overrides={"db": {"user": "u"}})
    assert d == {"db": {"host": "h"}, "tags": [1]}, d


def test_p7_idempotent():
    d = {"db": {"host": "h", "port": 1}}
    f = {"db": {"port": 2}}
    assert load(d, f) == load(d, f)


def test_p7_returned_structure_is_independent():
    d = {"db": {"host": "h"}}
    r = load(d)
    r["db"]["host"] = "changed"
    assert d == {"db": {"host": "h"}}, d
