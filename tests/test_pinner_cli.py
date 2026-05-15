"""Tests for envdiff.pinner_cli."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from envdiff.pinner_cli import _cmd_pin, _cmd_pin_diff, add_pinner_subcommands


def _write(tmp_path: Path, name: str, content: str) -> Path:
    p = tmp_path / name
    p.write_text(content, encoding="utf-8")
    return p


def _make_args(**kwargs) -> argparse.Namespace:
    return argparse.Namespace(**kwargs)


def test_pin_creates_file(tmp_path: Path) -> None:
    env = _write(tmp_path, ".env", "KEY=val\n")
    out = tmp_path / "pin.json"
    args = _make_args(env_file=str(env), output=str(out))
    rc = _cmd_pin(args)
    assert rc == 0
    assert out.exists()
    data = json.loads(out.read_text())
    assert data["values"] == {"KEY": "val"}


def test_pin_missing_file_returns_error(tmp_path: Path) -> None:
    args = _make_args(env_file=str(tmp_path / "ghost.env"), output=str(tmp_path / "p.json"))
    rc = _cmd_pin(args)
    assert rc == 1


def test_pin_diff_no_changes_exits_zero(tmp_path: Path) -> None:
    env = _write(tmp_path, ".env", "A=1\n")
    pin_path = tmp_path / "pin.json"
    _cmd_pin(_make_args(env_file=str(env), output=str(pin_path)))
    args = _make_args(env_file=str(env), pin_file=str(pin_path), fmt="text")
    rc = _cmd_pin_diff(args)
    assert rc == 0


def test_pin_diff_with_changes_exits_one(tmp_path: Path) -> None:
    env = _write(tmp_path, ".env", "A=1\n")
    pin_path = tmp_path / "pin.json"
    _cmd_pin(_make_args(env_file=str(env), output=str(pin_path)))
    env.write_text("A=2\n", encoding="utf-8")
    args = _make_args(env_file=str(env), pin_file=str(pin_path), fmt="text")
    rc = _cmd_pin_diff(args)
    assert rc == 1


def test_pin_diff_json_format(tmp_path: Path, capsys) -> None:
    env = _write(tmp_path, ".env", "A=old\n")
    pin_path = tmp_path / "pin.json"
    _cmd_pin(_make_args(env_file=str(env), output=str(pin_path)))
    env.write_text("A=new\n", encoding="utf-8")
    args = _make_args(env_file=str(env), pin_file=str(pin_path), fmt="json")
    _cmd_pin_diff(args)
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["changed"]["A"]["current"] == "new"


def test_add_pinner_subcommands_registers(tmp_path: Path) -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command")
    add_pinner_subcommands(sub)
    args = parser.parse_args(["pin", str(tmp_path / "e.env"), "-o", str(tmp_path / "p.json")])
    assert args.command == "pin"
