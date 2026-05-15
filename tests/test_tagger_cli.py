"""Integration tests for the tagger CLI sub-command."""
from __future__ import annotations

import argparse
import os
from pathlib import Path

import pytest

from envdiff.tagger_cli import _cmd_tag, add_tagger_subcommands


def _write(path: Path, content: str) -> Path:
    path.write_text(content)
    return path


@pytest.fixture()
def env_left(tmp_path: Path) -> Path:
    return _write(tmp_path / ".env.left", "DB_HOST=localhost\nDB_PORT=5432\nAPI_KEY=secret\n")


@pytest.fixture()
def env_right(tmp_path: Path) -> Path:
    return _write(tmp_path / ".env.right", "DB_HOST=remotehost\nLOG_LEVEL=info\n")


def _make_args(left: str, right: str, rules=None, untagged: bool = False) -> argparse.Namespace:
    return argparse.Namespace(
        left=left,
        right=right,
        rules=rules or [],
        untagged=untagged,
    )


def test_tag_exits_zero_no_rules(env_left, env_right):
    args = _make_args(str(env_left), str(env_right))
    rc = _cmd_tag(args)
    assert rc == 0


def test_tag_with_valid_rule(env_left, env_right):
    args = _make_args(str(env_left), str(env_right), rules=["DB_*:database"])
    rc = _cmd_tag(args)
    assert rc == 0


def test_tag_invalid_rule_format(env_left, env_right):
    args = _make_args(str(env_left), str(env_right), rules=["INVALID_RULE"])
    rc = _cmd_tag(args)
    assert rc == 2


def test_tag_untagged_flag(env_left, env_right):
    args = _make_args(str(env_left), str(env_right), rules=["DB_*:database"], untagged=True)
    rc = _cmd_tag(args)
    assert rc == 0


def test_add_tagger_subcommands_registers_tag():
    parser = argparse.ArgumentParser()
    subs = parser.add_subparsers()
    add_tagger_subcommands(subs)
    parsed = parser.parse_args(["tag", "a.env", "b.env", "--rule", "DB_*:db"])
    assert parsed.left == "a.env"
    assert parsed.rules == ["DB_*:db"]
