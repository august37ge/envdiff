"""Tests for envdiff.comparator."""

import pytest
from envdiff.comparator import compare_envs, KeyDiff


LEFT = {"DB_HOST": "localhost", "DB_PORT": "5432", "SECRET": "abc"}
RIGHT = {"DB_HOST": "prod.db", "DB_PORT": "5432", "API_KEY": "xyz"}


def test_no_diffs_identical():
    result = compare_envs({"A": "1"}, {"A": "1"})
    assert not result.has_diffs
    assert result.diffs == []


def test_missing_in_right():
    result = compare_envs(LEFT, RIGHT)
    keys = {d.key for d in result.missing_in_right}
    assert "SECRET" in keys


def test_missing_in_left():
    result = compare_envs(LEFT, RIGHT)
    keys = {d.key for d in result.missing_in_left}
    assert "API_KEY" in keys


def test_value_mismatch():
    result = compare_envs(LEFT, RIGHT)
    mismatched_keys = {d.key for d in result.mismatched}
    assert "DB_HOST" in mismatched_keys


def test_no_mismatch_when_keys_only():
    result = compare_envs(LEFT, RIGHT, keys_only=True)
    assert result.mismatched == []
    # missing keys still reported
    assert result.missing_in_right or result.missing_in_left


def test_paths_stored_in_result():
    result = compare_envs({}, {}, left_path=".env.dev", right_path=".env.prod")
    assert result.left_path == ".env.dev"
    assert result.right_path == ".env.prod"


def test_diffs_sorted_by_key():
    left = {"Z": "1", "A": "1", "M": "1"}
    right = {"Z": "2", "A": "2", "M": "2"}
    result = compare_envs(left, right)
    keys = [d.key for d in result.diffs]
    assert keys == sorted(keys)


def test_keydiff_str_missing_in_left():
    d = KeyDiff(key="FOO", status="missing_in_left", right_value="bar")
    assert "missing in left" in str(d)
    assert "FOO" in str(d)


def test_keydiff_str_missing_in_right():
    d = KeyDiff(key="FOO", status="missing_in_right", left_value="bar")
    assert "missing in right" in str(d)


def test_keydiff_str_value_mismatch():
    d = KeyDiff(key="FOO", status="value_mismatch", left_value="a", right_value="b")
    assert "mismatch" in str(d)
    assert "'a'" in str(d)
    assert "'b'" in str(d)


def test_empty_envs():
    result = compare_envs({}, {})
    assert not result.has_diffs
