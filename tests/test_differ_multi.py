"""Tests for envdiff.differ_multi."""
from __future__ import annotations

from pathlib import Path

import pytest

from envdiff.differ_multi import MultiDiffError, MultiDiffResult, diff_multi


def _write(path: Path, content: str) -> Path:
    path.write_text(content)
    return path


@pytest.fixture()
def env_base(tmp_path: Path) -> Path:
    return _write(tmp_path / "base.env", "A=1\nB=2\nC=3\n")


@pytest.fixture()
def env_full(tmp_path: Path) -> Path:
    return _write(tmp_path / "full.env", "A=1\nB=2\nC=3\n")


@pytest.fixture()
def env_missing(tmp_path: Path) -> Path:
    return _write(tmp_path / "missing.env", "A=1\n")


@pytest.fixture()
def env_mismatch(tmp_path: Path) -> Path:
    return _write(tmp_path / "mismatch.env", "A=99\nB=2\nC=3\n")


def test_identical_files_no_diffs(env_base, env_full):
    result = diff_multi(env_base, [env_full])
    assert isinstance(result, MultiDiffResult)
    assert not result.any_diffs()
    assert result.targets_with_diffs() == []


def test_missing_key_detected(env_base, env_missing):
    result = diff_multi(env_base, [env_missing])
    assert result.any_diffs()
    assert str(env_missing) in result.targets_with_diffs()


def test_mismatch_detected(env_base, env_mismatch):
    result = diff_multi(env_base, [env_mismatch])
    assert result.any_diffs()


def test_keys_only_ignores_mismatch(env_base, env_mismatch):
    result = diff_multi(env_base, [env_mismatch], keys_only=True)
    assert not result.any_diffs()


def test_multiple_targets(env_base, env_full, env_missing):
    result = diff_multi(env_base, [env_full, env_missing])
    assert len(result.results) == 2
    assert result.any_diffs()
    assert str(env_missing) in result.targets_with_diffs()
    assert str(env_full) not in result.targets_with_diffs()


def test_empty_targets_raises(env_base):
    with pytest.raises(MultiDiffError, match="At least one target"):
        diff_multi(env_base, [])


def test_missing_baseline_raises(tmp_path):
    with pytest.raises(MultiDiffError, match="Baseline file not found"):
        diff_multi(tmp_path / "ghost.env", [tmp_path / "x.env"])


def test_missing_target_raises(env_base, tmp_path):
    with pytest.raises(MultiDiffError):
        diff_multi(env_base, [tmp_path / "nonexistent.env"])
