"""scheduler_integration.py – entry-point wiring for the scheduler feature."""
from __future__ import annotations

import argparse

from envdiff.scheduler_cli import add_scheduler_subcommands


def register(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    """Register scheduler subcommands onto *subparsers*."""
    add_scheduler_subcommands(subparsers)


def run_from_argv(argv: list[str] | None = None) -> int:
    """Standalone entry-point for scheduler commands."""
    parser = argparse.ArgumentParser(
        prog="envdiff-scheduler",
        description="Periodic env-diff scheduling utilities.",
    )
    sub = parser.add_subparsers(dest="command")
    add_scheduler_subcommands(sub)
    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help()
        return 0
    return args.func(args)
