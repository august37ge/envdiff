"""CLI subcommands for the pinner feature."""
from __future__ import annotations

import argparse
import json
import sys

from envdiff.pinner import PinError, diff_against_pin, load_pin, pin_file, save_pin


def add_pinner_subcommands(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    _add_pin(subparsers)
    _add_pin_diff(subparsers)


def _add_pin(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("pin", help="Pin the current state of an env file")
    p.add_argument("env_file", help="Path to the .env file to pin")
    p.add_argument("-o", "--output", required=True, help="Path to write the pin JSON file")
    p.set_defaults(func=_cmd_pin)


def _add_pin_diff(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("pin-diff", help="Diff an env file against a saved pin")
    p.add_argument("env_file", help="Path to the current .env file")
    p.add_argument("pin_file", help="Path to the saved pin JSON file")
    p.add_argument("--format", choices=["text", "json"], default="text", dest="fmt")
    p.set_defaults(func=_cmd_pin_diff)


def _cmd_pin(args: argparse.Namespace) -> int:
    try:
        entry = pin_file(args.env_file)
        save_pin(entry, args.output)
        print(f"Pinned {args.env_file} -> {args.output}")
        return 0
    except PinError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


def _cmd_pin_diff(args: argparse.Namespace) -> int:
    try:
        entry = load_pin(args.pin_file)
        result = diff_against_pin(args.env_file, entry)
    except PinError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.fmt == "json":
        print(json.dumps(result, indent=2))
    else:
        _print_text(result, args.env_file, entry.pinned_at)

    has_diffs = any(result[k] for k in ("added", "removed", "changed"))
    return 1 if has_diffs else 0


def _print_text(result: dict, env_path: str, pinned_at: str) -> None:
    print(f"Pin diff for: {env_path}  (pinned at {pinned_at})")
    if not any(result[k] for k in ("added", "removed", "changed")):
        print("  No changes since pin.")
        return
    for key in sorted(result["added"]):
        print(f"  + {key} (added)")
    for key in sorted(result["removed"]):
        print(f"  - {key} (removed)")
    for key, vals in sorted(result["changed"].items()):
        print(f"  ~ {key}: '{vals['pinned']}' -> '{vals['current']}'")
