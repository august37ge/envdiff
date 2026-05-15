"""aliaser.py – map canonical key names to user-defined aliases.

Allows users to define alias rules so that keys with different names across
environments are treated as equivalent during comparison.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional


class AliasError(Exception):
    """Raised when alias configuration is invalid."""


@dataclass
class AliasRule:
    """Maps one or more alternate names to a canonical key name."""

    canonical: str
    aliases: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.canonical:
            raise AliasError("canonical key name must not be empty")
        if not re.match(r"[A-Za-z_][A-Za-z0-9_]*", self.canonical):
            raise AliasError(f"invalid canonical key name: {self.canonical!r}")

    def matches(self, key: str) -> bool:
        """Return True if *key* is the canonical name or one of its aliases."""
        return key == self.canonical or key in self.aliases


@dataclass
class AliasMap:
    """Collection of alias rules with fast lookup."""

    rules: List[AliasRule] = field(default_factory=list)
    # internal: alias -> canonical
    _index: Dict[str, str] = field(default_factory=dict, init=False, repr=False)

    def __post_init__(self) -> None:
        self._rebuild_index()

    def _rebuild_index(self) -> None:
        self._index = {}
        for rule in self.rules:
            for alias in rule.aliases:
                if alias in self._index:
                    raise AliasError(
                        f"alias {alias!r} is already mapped to "
                        f"{self._index[alias]!r}"
                    )
                self._index[alias] = rule.canonical

    def resolve(self, key: str) -> str:
        """Return the canonical name for *key*, or *key* itself if unknown."""
        return self._index.get(key, key)

    def add_rule(self, rule: AliasRule) -> None:
        """Append a rule and update the index."""
        self.rules.append(rule)
        self._rebuild_index()


def build_alias_map(rules: Optional[List[Dict]] = None) -> AliasMap:
    """Build an :class:`AliasMap` from a list of plain-dict rule definitions.

    Each dict must have a ``canonical`` key and an optional ``aliases`` list::

        [{"canonical": "DATABASE_URL", "aliases": ["DB_URL", "POSTGRES_URL"]}]
    """
    if not rules:
        return AliasMap()
    parsed: List[AliasRule] = []
    for entry in rules:
        if "canonical" not in entry:
            raise AliasError(f"alias rule missing 'canonical' key: {entry!r}")
        parsed.append(
            AliasRule(
                canonical=entry["canonical"],
                aliases=list(entry.get("aliases", [])),
            )
        )
    return AliasMap(rules=parsed)


def apply_aliases(env: Dict[str, str], alias_map: AliasMap) -> Dict[str, str]:
    """Return a new env dict with aliased keys replaced by their canonical names."""
    result: Dict[str, str] = {}
    for key, value in env.items():
        result[alias_map.resolve(key)] = value
    return result
