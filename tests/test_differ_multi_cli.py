"""Tests for envdiff.differ_multi_cli."""
from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from envdiff.differ_multi_cli import add_multi_diff_subcommands, _cmd_multi_diff


def _write(path: Path, content: str) -> Path:
    path.write_text(content)
    return path


@pytest.fixture()
def env_left(tmp_path: Path) -> Path:
    return _write(tmp_path / "left.env", "A=1\nB=2\n")


@pytest.fixture()
def env_right(tmp_path: Path) -> Path:
    return _write(tmp_path / "right.env", "A=1\nB=2\n")


@pytest.fixture()
def env_diff(tmp_path: Path) -> Path:
    return _write(tmp_path / "diff.env", "A=99\n")


def _make_args(**kwargs) -> argparse.Namespace:
    defaults = dict(baseline=None, targets=[], keys_only=False, fmt="text", fail_on_diff=False, func=_cmd_multi_diff)
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_subcommand_registers(capsys):
    parser = argparse.ArgumentParser()
    subs = parser.add_subparsers()
    add_multi_diff_subcommands(subs)
    # no error means registration succeeded


def test_no_diffs_exits_zero(env_left, env_right, capsys):
    args = _make_args(baseline=str(env_left), targets=[str(env_right)])
    _cmd_multi_diff(args)  # should not raise
    out = capsys.readouterr().out
    assert "left.env" in out


def test_fail_on_diff_exits_one(env_left, env_diff):
    args = _make_args(baseline=str(env_left), targets=[str(env_diff)], fail_on_diff=True)
    with pytest.raises(SystemExit) as exc:
        _cmd_multi_diff(args)
    assert exc.value.code == 1


def test_no_fail_on_diff_exits_zero(env_left, env_diff):
    args = _make_args(baseline=str(env_left), targets=[str(env_diff)], fail_on_diff=False)
    _cmd_multi_diff(args)  # should not raise SystemExit


def test_bad_baseline_exits_two(tmp_path, env_right):
    args = _make_args(baseline=str(tmp_path / "ghost.env"), targets=[str(env_right)])
    with pytest.raises(SystemExit) as exc:
        _cmd_multi_diff(args)
    assert exc.value.code == 2


def test_json_format_output(env_left, env_right, capsys):
    args = _make_args(baseline=str(env_left), targets=[str(env_right)], fmt="json")
    _cmd_multi_diff(args)
    out = capsys.readouterr().out
    assert "{" in out
