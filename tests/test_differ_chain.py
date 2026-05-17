"""Tests for envdiff.differ_chain."""
from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from envdiff.differ_chain import ChainError, ChainLink, ChainResult, diff_chain
from envdiff.differ_chain_cli import _cmd_chain, add_chain_subcommands


def _write(tmp_path: Path, name: str, content: str) -> Path:
    p = tmp_path / name
    p.write_text(content)
    return p


@pytest.fixture()
def env_a(tmp_path):
    return _write(tmp_path, "a.env", "KEY1=alpha\nKEY2=shared\n")


@pytest.fixture()
def env_b(tmp_path):
    return _write(tmp_path, "b.env", "KEY2=shared\nKEY3=beta\n")


@pytest.fixture()
def env_c(tmp_path):
    return _write(tmp_path, "c.env", "KEY3=beta\nKEY4=gamma\n")


def test_fewer_than_two_files_raises(tmp_path, env_a):
    with pytest.raises(ChainError, match="At least two"):
        diff_chain([env_a])


def test_missing_file_raises(tmp_path, env_a):
    with pytest.raises(ChainError, match="File not found"):
        diff_chain([env_a, tmp_path / "ghost.env"])


def test_two_file_chain_produces_one_link(env_a, env_b):
    result = diff_chain([env_a, env_b])
    assert isinstance(result, ChainResult)
    assert len(result) == 1
    assert isinstance(result.links[0], ChainLink)


def test_three_file_chain_produces_two_links(env_a, env_b, env_c):
    result = diff_chain([env_a, env_b, env_c])
    assert len(result) == 2


def test_any_diffs_true_when_keys_differ(env_a, env_b):
    result = diff_chain([env_a, env_b])
    assert result.any_diffs() is True


def test_any_diffs_false_when_identical(tmp_path):
    same = _write(tmp_path, "same1.env", "KEY=value\n")
    same2 = _write(tmp_path, "same2.env", "KEY=value\n")
    result = diff_chain([same, same2])
    assert result.any_diffs() is False


def test_links_with_diffs_filters_correctly(env_a, env_b, tmp_path):
    clean1 = _write(tmp_path, "c1.env", "X=1\n")
    clean2 = _write(tmp_path, "c2.env", "X=1\n")
    result = diff_chain([clean1, clean2])
    assert result.links_with_diffs() == []


def test_cli_exits_zero_no_fail_flag(tmp_path, env_a, env_b):
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd")
    add_chain_subcommands(sub)
    args = parser.parse_args(["chain", str(env_a), str(env_b)])
    assert _cmd_chain(args) == 0


def test_cli_exits_one_with_fail_flag_and_diffs(tmp_path, env_a, env_b):
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd")
    add_chain_subcommands(sub)
    args = parser.parse_args(["chain", "--fail-on-diff", str(env_a), str(env_b)])
    assert _cmd_chain(args) == 1


def test_cli_returns_error_on_missing_file(tmp_path, env_a):
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd")
    add_chain_subcommands(sub)
    args = parser.parse_args(["chain", str(env_a), str(tmp_path / "nope.env")])
    assert _cmd_chain(args) == 1
