"""CLI subcommands for the grouper module."""
from __future__ import annotations

import argparse
import json
import sys
from typing import List

from envdiff.differ import diff_files
from envdiff.grouper import GroupError, group_by_prefix


def add_grouper_subcommands(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser(
        "group",
        help="Group diff keys by prefix and display counts.",
    )
    p.add_argument("left", help="Left .env file")
    p.add_argument("right", help="Right .env file")
    p.add_argument(
        "--prefixes",
        nargs="+",
        metavar="PREFIX",
        help="Explicit prefixes to group by (e.g. DB AWS APP).",
    )
    p.add_argument(
        "--separator",
        default="_",
        help="Key separator character (default: '_').",
    )
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        dest="fmt",
        help="Output format.",
    )
    p.set_defaults(func=_cmd_group)


def _cmd_group(args: argparse.Namespace) -> int:
    try:
        compare_result = diff_files(args.left, args.right)
    except Exception as exc:  # noqa: BLE001
        print(f"error: {exc}", file=sys.stderr)
        return 1

    try:
        group_result = group_by_prefix(
            compare_result,
            prefixes=args.prefixes,
            separator=args.separator,
        )
    except GroupError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.fmt == "json":
        payload = {
            "groups": {
                name: [d.key for d in g.diffs]
                for name, g in group_result.groups.items()
            },
            "ungrouped": [d.key for d in group_result.ungrouped],
            "total_diffs": group_result.total_diffs(),
        }
        print(json.dumps(payload, indent=2))
    else:
        _print_text(group_result, args.left, args.right)

    return 0


def _print_text(group_result, left: str, right: str) -> None:
    print(f"Grouped diff: {left}  vs  {right}")
    print(f"Total diffs : {group_result.total_diffs()}")
    print()
    for name in group_result.group_names:
        grp = group_result.groups[name]
        if grp.diffs:
            print(f"  [{name}_*]  {len(grp)} key(s)")
            for d in grp.diffs:
                print(f"    - {d.key}")
    if group_result.ungrouped:
        print(f"  [ungrouped]  {len(group_result.ungrouped)} key(s)")
        for d in group_result.ungrouped:
            print(f"    - {d.key}")
