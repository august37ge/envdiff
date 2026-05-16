"""Tests for envdiff.aliaser."""
from __future__ import annotations

import pytest

from envdiff.aliaser import (
    AliasError,
    AliasMap,
    AliasRule,
    apply_aliases,
    build_alias_map,
)


# ---------------------------------------------------------------------------
# AliasRule
# ---------------------------------------------------------------------------

def test_alias_rule_matches_canonical():
    rule = AliasRule(canonical="DATABASE_URL", aliases=["DB_URL"])
    assert rule.matches("DATABASE_URL")


def test_alias_rule_matches_alias():
    rule = AliasRule(canonical="DATABASE_URL", aliases=["DB_URL", "POSTGRES_URL"])
    assert rule.matches("DB_URL")
    assert rule.matches("POSTGRES_URL")


def test_alias_rule_no_match_for_unknown_key():
    rule = AliasRule(canonical="DATABASE_URL", aliases=["DB_URL"])
    assert not rule.matches("REDIS_URL")


def test_alias_rule_empty_canonical_raises():
    with pytest.raises(AliasError):
        AliasRule(canonical="")


# ---------------------------------------------------------------------------
# AliasMap
# ---------------------------------------------------------------------------

def test_alias_map_resolve_known_alias():
    rule = AliasRule(canonical="DATABASE_URL", aliases=["DB_URL"])
    am = AliasMap(rules=[rule])
    assert am.resolve("DB_URL") == "DATABASE_URL"


def test_alias_map_resolve_unknown_key_returns_itself():
    am = AliasMap(rules=[])
    assert am.resolve("SOME_KEY") == "SOME_KEY"


def test_alias_map_duplicate_alias_raises():
    r1 = AliasRule(canonical="A", aliases=["X"])
    r2 = AliasRule(canonical="B", aliases=["X"])
    with pytest.raises(AliasError, match="already mapped"):
        AliasMap(rules=[r1, r2])


def test_alias_map_add_rule_updates_index():
    am = AliasMap()
    am.add_rule(AliasRule(canonical="SECRET_KEY", aliases=["APP_SECRET"]))
    assert am.resolve("APP_SECRET") == "SECRET_KEY"


# ---------------------------------------------------------------------------
# build_alias_map
# ---------------------------------------------------------------------------

def test_build_alias_map_from_dicts():
    rules = [{"canonical": "DB_URL", "aliases": ["DATABASE_URL", "POSTGRES_URL"]}]
    am = build_alias_map(rules)
    assert am.resolve("DATABASE_URL") == "DB_URL"


def test_build_alias_map_missing_canonical_raises():
    with pytest.raises(AliasError, match="missing 'canonical'"):
        build_alias_map([{"aliases": ["FOO"]}])


def test_build_alias_map_empty_returns_empty_map():
    am = build_alias_map([])
    assert am.rules == []


# ---------------------------------------------------------------------------
# apply_aliases
# ---------------------------------------------------------------------------

def test_apply_aliases_renames_key():
    env = {"DB_URL": "postgres://localhost/db", "DEBUG": "true"}
    rule = AliasRule(canonical="DATABASE_URL", aliases=["DB_URL"])
    am = AliasMap(rules=[rule])
    result = apply_aliases(env, am)
    assert result["DATABASE_URL"] == "postgres://localhost/db"
    assert "DB_URL" not in result


def test_apply_aliases_preserves_unmatched_keys():
    """Keys with no alias rule should pass through unchanged."""
    env = {"DEBUG": "true", "PORT": "8080"}
    am = AliasMap(rules=[])
    result = apply_aliases(env, am)
    assert result == {"DEBUG": "true", "PORT": "8080"}


def test_apply_aliases_empty_env_returns_empty():
    """Applying aliases to an empty environment should return an empty dict."""
    am = AliasMap(rules=[AliasRule(canonical="DATABASE_URL", aliases=["DB_URL"])])
    result = apply_aliases({}, am)
    assert result == {}
