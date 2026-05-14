"""CLI subcommands for the auditor feature."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envdiff.auditor import AuditError, audit_file


def add_auditor_subcommands(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "audit",
        help="Audit a .env file for sensitive or empty keys.",
    )
    p.add_argument("file", type=Path, help="Path to the .env file to audit.")
    p.add_argument(
        "--warn-only",
        action="store_true",
        help="Only show warnings, suppress info-level issues.",
    )
    p.add_argument(
        "--strict",
        action="store_true",
        help="Exit with code 1 if any issues are found.",
    )
    p.set_defaults(func=_cmd_audit)


def _cmd_audit(args: argparse.Namespace) -> None:
    try:
        result = audit_file(args.file)
    except AuditError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(2)

    issues = result.warnings if args.warn_only else result.issues

    if not issues:
        print(f"No issues found in {args.file}.")
        sys.exit(0)

    print(f"Audit results for {args.file}:")
    for issue in issues:
        print(f"  {issue}")

    if args.strict and result.has_issues:
        sys.exit(1)
