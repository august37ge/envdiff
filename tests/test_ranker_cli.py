"""Integration tests for the ranker CLI subcommand."""
from __future__ import annotations

import argparse
import os
from pathlib import Path

import pytest

from envdiff.ranker_cli import _cmd_rank, add_ranker_subcommands


def _write(path: Path, content: str) -> Path:
    path.write_text(content)
    return path


@pytest.fixture()
def env_left(tmp_path: Path) -> Path:
    return _write(tmp_path / ".env.left", "SHARED=same\nONLY_LEFT=val\nDIFF=left_val\n")


@pytest.fixture()
def env_right(tmp_path: Path) -> Path:
    return _write(tmp_path / ".env.right", "SHARED=same\nONLY_RIGHT=val\nDIFF=right_val\n")


def _make_args(**kwargs) -> argparse.Namespace:
    defaults = {"top": 0, "min_severity": "ok", "func": _cmd_rank}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_rank_exits_zero_on_valid_files(env_left, env_right):
    args = _make_args(left=str(env_left), right=str(env_right))
    rc = _cmd_rank(args)
    assert rc == 0


def test_rank_bad_file_exits_nonzero(tmp_path):
    args = _make_args(left=str(tmp_path / "missing.env"), right=str(tmp_path / "also.env"))
    rc = _cmd_rank(args)
    assert rc == 1


def test_rank_top_limits_output(env_left, env_right, capsys):
    args = _make_args(left=str(env_left), right=str(env_right), top=1)
    rc = _cmd_rank(args)
    assert rc == 0
    out = capsys.readouterr().out
    data_lines = [l for l in out.splitlines() if l and not l.startswith("-") and "SEVERITY" not in l]
    assert len(data_lines) == 1


def test_rank_min_severity_missing_filters(env_left, env_right, capsys):
    args = _make_args(left=str(env_left), right=str(env_right), min_severity="missing")
    rc = _cmd_rank(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "OK" not in out
    assert "MISMATCH" not in out


def test_add_ranker_subcommands_registers_rank():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_ranker_subcommands(sub)
    args = parser.parse_args(["rank", "a.env", "b.env"])
    assert args.left == "a.env"
    assert args.right == "b.env"
