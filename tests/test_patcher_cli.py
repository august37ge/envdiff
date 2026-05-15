"""Tests for envdiff.patcher_cli."""
from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from envdiff.patcher_cli import _cmd_patch, add_patcher_subcommands


def _write(tmp_path: Path, name: str, content: str) -> Path:
    p = tmp_path / name
    p.write_text(content, encoding="utf-8")
    return p


def _make_args(**kwargs) -> argparse.Namespace:  # type: ignore[no-untyped-def]
    defaults = dict(
        fill_missing=True,
        overwrite_mismatches=False,
        comment_source=False,
        output=None,
    )
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_patch_stdout_exits_zero(tmp_path: Path, capsys) -> None:  # type: ignore[no-untyped-def]
    base = _write(tmp_path, "base.env", "FOO=1\n")
    other = _write(tmp_path, "other.env", "FOO=1\nBAR=2\n")
    args = _make_args(base=str(base), other=str(other))
    rc = _cmd_patch(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "BAR=2" in out


def test_patch_output_file_created(tmp_path: Path, capsys) -> None:  # type: ignore[no-untyped-def]
    base = _write(tmp_path, "base.env", "FOO=1\n")
    other = _write(tmp_path, "other.env", "FOO=1\nBAR=2\n")
    dest = tmp_path / "out.env"
    args = _make_args(base=str(base), other=str(other), output=str(dest))
    rc = _cmd_patch(args)
    assert rc == 0
    assert dest.exists()
    assert "BAR=2" in dest.read_text()


def test_patch_missing_base_returns_error(tmp_path: Path, capsys) -> None:  # type: ignore[no-untyped-def]
    other = _write(tmp_path, "other.env", "FOO=1\n")
    args = _make_args(base=str(tmp_path / "missing.env"), other=str(other))
    rc = _cmd_patch(args)
    assert rc == 1
    assert "not found" in capsys.readouterr().err


def test_patch_missing_other_returns_error(tmp_path: Path, capsys) -> None:  # type: ignore[no-untyped-def]
    base = _write(tmp_path, "base.env", "FOO=1\n")
    args = _make_args(base=str(base), other=str(tmp_path / "missing.env"))
    rc = _cmd_patch(args)
    assert rc == 1


def test_add_patcher_subcommands_registers_patch() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_patcher_subcommands(sub)
    ns = parser.parse_args(["patch", "a.env", "b.env"])
    assert ns.base == "a.env"
    assert ns.other == "b.env"
