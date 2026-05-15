"""Integration entry-point: register multi-diff into the main CLI."""
from __future__ import annotations

import argparse

from envdiff.differ_multi_cli import add_multi_diff_subcommands


def register(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    """Register the *multi-diff* sub-command with an existing subparsers group."""
    add_multi_diff_subcommands(subparsers)


def run_from_argv(argv: list[str] | None = None) -> None:
    """Standalone entry-point for quick manual testing."""
    parser = argparse.ArgumentParser(
        prog="envdiff-multi",
        description="Compare multiple .env files against a baseline.",
    )
    subs = parser.add_subparsers(dest="command")
    register(subs)

    args = parser.parse_args(argv)
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()
