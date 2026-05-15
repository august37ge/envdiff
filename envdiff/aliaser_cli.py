"""aliaser_cli.py – CLI sub-commands for the aliaser module."""
from __future__ import annotations

import argparse
import json
import sys
from typing import List

from envdiff.aliaser import AliasError, AliasRule, AliasMap, apply_aliases
from envdiff.parser import parse_env_file, EnvParseError


def add_aliaser_subcommands(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser(
        "alias",
        help="resolve key aliases in an env file and print the normalised result",
    )
    p.add_argument("file", help="path to the .env file")
    p.add_argument(
        "--rule",
        metavar="CANONICAL:ALIAS[,ALIAS…]",
        action="append",
        dest="rules",
        default=[],
        help="alias rule; may be repeated",
    )
    p.add_argument(
        "--rules-file",
        metavar="JSON",
        help="JSON file containing a list of rule objects",
    )
    p.add_argument(
        "--format",
        choices=["env", "json"],
        default="env",
        help="output format (default: env)",
    )
    p.set_defaults(func=_cmd_alias)


def _parse_inline_rules(raw: List[str]) -> List[dict]:
    result = []
    for token in raw:
        if ":" not in token:
            raise AliasError(f"rule must be CANONICAL:ALIAS[,…], got {token!r}")
        canonical, _, rest = token.partition(":")
        aliases = [a.strip() for a in rest.split(",") if a.strip()]
        result.append({"canonical": canonical.strip(), "aliases": aliases})
    return result


def _cmd_alias(args: argparse.Namespace) -> int:
    # collect rules
    rule_dicts: List[dict] = []
    if args.rules_file:
        try:
            with open(args.rules_file) as fh:
                rule_dicts.extend(json.load(fh))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"error: cannot load rules file: {exc}", file=sys.stderr)
            return 1
    try:
        rule_dicts.extend(_parse_inline_rules(args.rules))
    except AliasError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    alias_rules = [AliasRule(r["canonical"], r.get("aliases", [])) for r in rule_dicts]
    alias_map = AliasMap(rules=alias_rules)

    try:
        env = parse_env_file(args.file)
    except (EnvParseError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    resolved = apply_aliases(env, alias_map)

    if args.format == "json":
        print(json.dumps(resolved, indent=2))
    else:
        for key, value in sorted(resolved.items()):
            print(f"{key}={value}")
    return 0
