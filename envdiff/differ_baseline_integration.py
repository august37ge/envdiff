"""Integration entry-point for the baseline sub-command."""
from __future__ import annotations

import argparse
import sys

from envdiff.differ_baseline_cli import add_baseline_subcommands


def register(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    """Register the baseline sub-command with an existing subparsers group."""
    add_baseline_subcommands(subparsers)


def run_from_argv(argv: list[str] | None = None) -> None:
    """Standalone entry-point for the baseline command."""
    parser = argparse.ArgumentParser(
        prog="envdiff-baseline",
        description="Compare a .env file against a saved snapshot baseline",
    )
    sub = parser.add_subparsers(dest="command")
    add_baseline_subcommands(sub)
    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help()
        sys.exit(0)
    sys.exit(args.func(args))
