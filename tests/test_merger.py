"""Tests for envdiff.merger."""

from pathlib import Path

import pytest

from envdiff.merger import merge_env_files, MergeError, MergeResult


def write_env(tmp_path: Path, filename: str, content: str) -> Path:
    p = tmp_path / filename
    p.write_text(content)
    return p


def test_merge_disjoint_keys(tmp_path):
    a = write_env(tmp_path, "a.env", "FOO=1\nBAR=2\n")
    b = write_env(tmp_path, "b.env", "BAZ=3\nQUX=4\n")
    result = merge_env_files([a, b])
    assert result.merged == {"FOO": "1", "BAR": "2", "BAZ": "3", "QUX": "4"}
    assert not result.has_conflicts


def test_merge_identical_keys_no_conflict(tmp_path):
    a = write_env(tmp_path, "a.env", "FOO=same\n")
    b = write_env(tmp_path, "b.env", "FOO=same\n")
    result = merge_env_files([a, b])
    assert result.merged["FOO"] == "same"
    assert not result.has_conflicts


def test_merge_conflicting_values_first_strategy(tmp_path):
    a = write_env(tmp_path, "a.env", "FOO=alpha\n")
    b = write_env(tmp_path, "b.env", "FOO=beta\n")
    result = merge_env_files([a, b], strategy="first")
    assert result.merged["FOO"] == "alpha"
    assert result.has_conflicts
    assert result.conflicts[0].key == "FOO"


def test_merge_conflicting_values_last_strategy(tmp_path):
    a = write_env(tmp_path, "a.env", "FOO=alpha\n")
    b = write_env(tmp_path, "b.env", "FOO=beta\n")
    result = merge_env_files([a, b], strategy="last")
    assert result.merged["FOO"] == "beta"
    assert result.has_conflicts


def test_merge_three_files(tmp_path):
    a = write_env(tmp_path, "a.env", "A=1\nSHARED=x\n")
    b = write_env(tmp_path, "b.env", "B=2\nSHARED=y\n")
    c = write_env(tmp_path, "c.env", "C=3\nSHARED=x\n")
    result = merge_env_files([a, b, c])
    assert "A" in result.merged
    assert "B" in result.merged
    assert "C" in result.merged
    assert result.has_conflicts


def test_merge_requires_at_least_two_files(tmp_path):
    a = write_env(tmp_path, "a.env", "FOO=1\n")
    with pytest.raises(MergeError, match="At least two"):
        merge_env_files([a])


def test_merge_invalid_strategy(tmp_path):
    a = write_env(tmp_path, "a.env", "FOO=1\n")
    b = write_env(tmp_path, "b.env", "FOO=2\n")
    with pytest.raises(MergeError, match="Unknown strategy"):
        merge_env_files([a, b], strategy="random")


def test_merge_labels_mismatch_raises(tmp_path):
    a = write_env(tmp_path, "a.env", "FOO=1\n")
    b = write_env(tmp_path, "b.env", "FOO=2\n")
    with pytest.raises(MergeError, match="labels"):
        merge_env_files([a, b], labels=["only-one"])


def test_merge_custom_labels(tmp_path):
    a = write_env(tmp_path, "a.env", "FOO=1\n")
    b = write_env(tmp_path, "b.env", "FOO=2\n")
    result = merge_env_files([a, b], labels=["prod", "staging"])
    assert result.sources == ["prod", "staging"]
    conflict = result.conflicts[0]
    assert "prod" in conflict.values
    assert "staging" in conflict.values


def test_merge_conflict_str(tmp_path):
    a = write_env(tmp_path, "a.env", "KEY=hello\n")
    b = write_env(tmp_path, "b.env", "KEY=world\n")
    result = merge_env_files([a, b], labels=["dev", "prod"])
    s = str(result.conflicts[0])
    assert "KEY" in s
    assert "dev" in s
    assert "prod" in s


def test_merge_missing_file_raises(tmp_path):
    a = write_env(tmp_path, "a.env", "FOO=1\n")
    missing = tmp_path / "missing.env"
    with pytest.raises(MergeError):
        merge_env_files([a, missing])
