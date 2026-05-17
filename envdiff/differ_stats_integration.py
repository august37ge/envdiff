"""Integration entry-point for differ_stats CLI sub-commands."""
from __future__ import annotations

import argparse

from envdiff.differ_stats_cli import add_stats_subcommands


def register(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Register the 'stats' sub-command onto an existing subparsers group."""
    add_stats_subcommands(subparsers)


def run_from_argv(argv=None) -> int:
    """Standalone entry-point for the stats command."""
    parser = argparse.ArgumentParser(
        prog="envdiff-stats",
        description="Aggregate diff statistics across multiple .env file pairs.",
    )
    subparsers = parser.add_subparsers(dest="command")
    add_stats_subcommands(subparsers)
    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help()
        return 0
    return args.func(args)
