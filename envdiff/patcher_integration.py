"""Integration entry-point for the patcher CLI subcommand."""
from __future__ import annotations

import argparse
import sys

from envdiff.patcher_cli import add_patcher_subcommands


def register(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Register patcher subcommands onto *subparsers*."""
    add_patcher_subcommands(subparsers)


def run_from_argv(argv: list[str] | None = None) -> int:
    """Standalone entry-point: ``python -m envdiff.patcher_integration``."""
    parser = argparse.ArgumentParser(
        prog="envdiff-patch",
        description="Patch a base .env file with keys from another environment.",
    )
    subparsers = parser.add_subparsers(dest="command")
    add_patcher_subcommands(subparsers)

    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help()
        return 0
    return args.func(args)  # type: ignore[no-any-return]


if __name__ == "__main__":  # pragma: no cover
    sys.exit(run_from_argv())
