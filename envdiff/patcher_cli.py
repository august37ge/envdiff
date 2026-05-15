"""CLI subcommands for the patcher module."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envdiff.differ import diff_files
from envdiff.patcher import PatchOptions, patch_result, write_patch


def add_patcher_subcommands(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "patch",
        help="Patch a base .env file with keys from another environment file.",
    )
    p.add_argument("base", help="Base .env file to patch")
    p.add_argument("other", help="Source .env file providing new/changed values")
    p.add_argument(
        "--output", "-o", default=None,
        help="Destination file (default: stdout)",
    )
    p.add_argument(
        "--fill-missing", action="store_true", default=True,
        help="Add keys present in OTHER but missing in BASE (default: on)",
    )
    p.add_argument(
        "--no-fill-missing", dest="fill_missing", action="store_false",
    )
    p.add_argument(
        "--overwrite-mismatches", action="store_true", default=False,
        help="Replace BASE values with OTHER values where keys differ",
    )
    p.add_argument(
        "--comment-source", action="store_true", default=False,
        help="Annotate added/changed lines with a comment",
    )
    p.set_defaults(func=_cmd_patch)


def _cmd_patch(args: argparse.Namespace) -> int:
    base = Path(args.base)
    other = Path(args.other)

    for p in (base, other):
        if not p.exists():
            print(f"error: file not found: {p}", file=sys.stderr)
            return 1

    options = PatchOptions(
        fill_missing=args.fill_missing,
        overwrite_mismatches=args.overwrite_mismatches,
        comment_source=args.comment_source,
    )

    try:
        compare = diff_files(base, other)
        result = patch_result(base, other, compare, options)
    except Exception as exc:  # noqa: BLE001
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.output:
        write_patch(result, Path(args.output), options)
        added = len(result.added_keys)
        changed = len(result.changed_keys)
        print(f"Patched {args.output}: {added} added, {changed} changed.")
    else:
        print(str(result))

    return 0
