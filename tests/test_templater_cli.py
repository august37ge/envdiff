"""Tests for envdiff.templater_cli."""

from __future__ import annotations

import os
import argparse
import pytest

from envdiff.templater_cli import add_templater_subcommands, _cmd_template


def _write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fh:
        fh.write(content)


@pytest.fixture()
def env_left(tmp_path):
    p = tmp_path / "left.env"
    _write(str(p), "FOO=bar\nSHARED=same\n")
    return str(p)


@pytest.fixture()
def env_right(tmp_path):
    p = tmp_path / "right.env"
    _write(str(p), "BAZ=qux\nSHARED=same\n")
    return str(p)


def _make_args(left, right=None, output=None, include_values=False,
               placeholder="", no_header=False, no_sort=False, extra_keys=None):
    ns = argparse.Namespace(
        left=left,
        right=right,
        output=output,
        include_values=include_values,
        placeholder=placeholder,
        no_header=no_header,
        no_sort=no_sort,
        extra_keys=extra_keys or [],
    )
    return ns


def test_single_file_template_stdout(env_left, capsys):
    rc = _cmd_template(_make_args(env_left))
    assert rc == 0
    out = capsys.readouterr().out
    assert "FOO=" in out


def test_diff_based_template_includes_both_sides(env_left, env_right, capsys):
    rc = _cmd_template(_make_args(env_left, right=env_right))
    assert rc == 0
    out = capsys.readouterr().out
    assert "FOO=" in out
    assert "BAZ=" in out


def test_output_written_to_file(env_left, tmp_path):
    out_path = str(tmp_path / "template.env")
    rc = _cmd_template(_make_args(env_left, output=out_path))
    assert rc == 0
    assert os.path.exists(out_path)
    content = open(out_path).read()
    assert "FOO=" in content


def test_include_values_flag(env_left, capsys):
    rc = _cmd_template(_make_args(env_left, include_values=True))
    assert rc == 0
    out = capsys.readouterr().out
    assert "FOO=bar" in out


def test_missing_file_returns_error(tmp_path, capsys):
    rc = _cmd_template(_make_args(str(tmp_path / "ghost.env")))
    assert rc == 1
    assert "error" in capsys.readouterr().err.lower()


def test_add_templater_subcommands_registers_template():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_templater_subcommands(sub)
    args = parser.parse_args(["template", "left.env"])
    assert args.left == "left.env"
