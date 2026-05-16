"""CLI sub-commands for the inspector feature."""
from __future__ import annotations

import argparse
import sys

from envdiff.inspector import inspect_file, InspectError


def add_inspector_subcommands(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser(
        "inspect",
        help="Inspect keys in a single .env file and report value characteristics.",
    )
    p.add_argument("file", help="Path to the .env file to inspect.")
    p.add_argument(
        "--key",
        metavar="KEY",
        default=None,
        help="Inspect a single key only.",
    )
    p.add_argument(
        "--only-empty",
        action="store_true",
        default=False,
        help="Show only keys with empty values.",
    )
    p.set_defaults(func=_cmd_inspect)


def _cmd_inspect(args: argparse.Namespace) -> int:
    try:
        result = inspect_file(args.file)
    except InspectError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    keys = result.keys

    if args.key:
        found = result.find(args.key)
        if found is None:
            print(f"error: key '{args.key}' not found in {args.file}", file=sys.stderr)
            return 1
        keys = [found]

    if args.only_empty:
        keys = [k for k in keys if k.is_empty]

    if not keys:
        print("No matching keys.")
        return 0

    print(f"Inspecting: {result.path}  ({result.total} total keys)")
    print()
    for ki in keys:
        print(f"  {ki}")

    return 0
