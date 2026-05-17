"""Integration entry-point for the chain-diff feature."""
from __future__ import annotations

import argparse
import sys

from envdiff.differ_chain_cli import add_chain_subcommands, _cmd_chain


def register(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    """Register the 'chain' sub-command on an existing subparsers action."""
    add_chain_subcommands(subparsers)


def run_from_argv(argv: list[str] | None = None) -> None:  # pragma: no cover
    """Standalone entry-point for the chain sub-command."""
    parser = argparse.ArgumentParser(
        prog="envdiff-chain",
        description="Compare consecutive .env file pairs along a chain.",
    )
    sub = parser.add_subparsers(dest="command")
    add_chain_subcommands(sub)
    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help()
        sys.exit(0)
    sys.exit(args.func(args))
