"""Tests for envdiff.trimmer_cli."""
from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from envdiff.trimmer_cli import add_trimmer_subcommands, _cmd_trim


def _write(tmp_path: Path, name: str, content: str) -> Path:
    p = tmp_path / name
    p.write_text(content, encoding="utf-8")
    return p


def _make_args(**kwargs) -> argparse.Namespace:
    defaults = {"output": None, "check": False}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_trim_stdout_exits_zero(tmp_path: Path, capsys) -> None:
    p = _write(tmp_path, ".env", "KEY=value\n")
    rc = _cmd_trim(_make_args(file=str(p)))
    assert rc == 0
    out = capsys.readouterr().out
    assert "KEY=value" in out


def test_trim_output_file_created(tmp_path: Path) -> None:
    p = _write(tmp_path, ".env", "KEY= hello \n")
    out = tmp_path / "out.env"
    rc = _cmd_trim(_make_args(file=str(p), output=str(out)))
    assert rc == 0
    assert out.exists()
    assert "KEY=hello" in out.read_text()


def test_check_exits_zero_when_clean(tmp_path: Path, capsys) -> None:
    p = _write(tmp_path, ".env", "KEY=clean\n")
    rc = _cmd_trim(_make_args(file=str(p), check=True))
    assert rc == 0
    assert "already trimmed" in capsys.readouterr().out


def test_check_exits_one_when_dirty(tmp_path: Path) -> None:
    p = _write(tmp_path, ".env", "KEY=  dirty  \n")
    rc = _cmd_trim(_make_args(file=str(p), check=True))
    assert rc == 1


def test_missing_file_returns_error(tmp_path: Path, capsys) -> None:
    rc = _cmd_trim(_make_args(file=str(tmp_path / "nope.env")))
    assert rc == 1
    assert "error" in capsys.readouterr().err


def test_subcommand_registered() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_trimmer_subcommands(sub)
    args = parser.parse_args(["trim", "some.env"])
    assert hasattr(args, "func")
