"""Integration entry-point so pinner subcommands can be registered centrally."""
from __future__ import annotations

import argparse

from envdiff.pinner_cli import add_pinner_subcommands


def register(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Register pin / pin-diff subcommands onto *subparsers*."""
    add_pinner_subcommands(subparsers)


def run_from_argv(argv: list[str] | None = None) -> int:
    """Standalone entry-point for the pinner CLI."""
    parser = argparse.ArgumentParser(prog="envdiff-pin")
    sub = parser.add_subparsers(dest="command")
    add_pinner_subcommands(sub)
    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help()
        return 0
    return args.func(args)
