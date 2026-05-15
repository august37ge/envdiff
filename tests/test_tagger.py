"""Tests for envdiff.tagger."""
from __future__ import annotations

import pytest

from envdiff.comparator import CompareResult, KeyDiff
from envdiff.tagger import TagError, TagResult, TagRule, tag_result


def _make_result(*keys: str) -> CompareResult:
    diffs = [KeyDiff(key=k, left_value=None, right_value="x") for k in keys]
    return CompareResult(diffs=diffs)


def test_tag_result_none_raises():
    with pytest.raises(TagError):
        tag_result(None, [])  # type: ignore[arg-type]


def test_no_rules_all_untagged():
    result = _make_result("DB_HOST", "API_KEY")
    tr = tag_result(result, [])
    assert len(tr.tagged) == 2
    assert all(tk.tags == [] for tk in tr.tagged)
    assert len(tr.untagged()) == 2


def test_glob_pattern_matches_key():
    result = _make_result("DB_HOST", "DB_PORT", "API_KEY")
    rules = [TagRule(pattern="DB_*", tag="database")]
    tr = tag_result(result, rules)
    db_keys = tr.by_tag("database")
    assert {tk.key for tk in db_keys} == {"DB_HOST", "DB_PORT"}


def test_multiple_rules_can_apply_to_same_key():
    result = _make_result("DB_SECRET")
    rules = [
        TagRule(pattern="DB_*", tag="database"),
        TagRule(pattern="*SECRET*", tag="sensitive"),
    ]
    tr = tag_result(result, rules)
    assert tr.tagged[0].tags == ["database", "sensitive"]


def test_untagged_excludes_tagged_keys():
    result = _make_result("DB_HOST", "LOG_LEVEL")
    rules = [TagRule(pattern="DB_*", tag="database")]
    tr = tag_result(result, rules)
    untagged = tr.untagged()
    assert len(untagged) == 1
    assert untagged[0].key == "LOG_LEVEL"


def test_all_tags_returns_unique_labels():
    result = _make_result("DB_HOST", "DB_PASS", "API_KEY")
    rules = [
        TagRule(pattern="DB_*", tag="database"),
        TagRule(pattern="*_KEY", tag="sensitive"),
    ]
    tr = tag_result(result, rules)
    assert set(tr.all_tags()) == {"database", "sensitive"}


def test_no_diffs_returns_empty_tag_result():
    result = CompareResult(diffs=[])
    tr = tag_result(result, [TagRule(pattern="*", tag="all")])
    assert tr.tagged == []


def test_tagged_key_str_with_tags():
    result = _make_result("DB_HOST")
    rules = [TagRule(pattern="DB_*", tag="db")]
    tr = tag_result(result, rules)
    assert "DB_HOST" in str(tr.tagged[0])
    assert "db" in str(tr.tagged[0])


def test_tagged_key_str_untagged():
    result = _make_result("LOG_LEVEL")
    tr = tag_result(result, [])
    assert "(untagged)" in str(tr.tagged[0])
