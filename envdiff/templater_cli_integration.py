"""Integration helper: wire templater sub-commands into the main CLI parser.

This module is imported by envdiff/cli.py to register the `template` command
without coupling the main CLI directly to the templater implementation.
"""

from __future__ import annotations

import argparse
from typing import List, Optional

from envdiff.templater_cli import add_templater_subcommands


def register(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    """Register all templater sub-commands with *subparsers*."""
    add_templater_subcommands(subparsers)


def run_from_argv(argv: Optional[List[str]] = None) -> int:
    """Standalone entry-point for the template command (useful for testing)."""
    parser = argparse.ArgumentParser(
        prog="envdiff template",
        description="Generate a .env template from a file or diff of two files.",
    )
    subparsers = parser.add_subparsers(dest="command")
    add_templater_subcommands(subparsers)

    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help()
        return 0

    return args.func(args)
