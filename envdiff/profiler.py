"""envdiff.profiler — build a statistical profile of a .env file.

A profile captures key counts, value length statistics, and category
breakdowns (empty, numeric, boolean, secret-like, other) so users can
quickly understand the shape of an environment file.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict

from envdiff.parser import parse_env_file, EnvParseError


class ProfileError(Exception):
    """Raised when profiling fails."""


_BOOL_VALUES = {"true", "false", "yes", "no", "1", "0"}
_SECRET_FRAGMENTS = ("key", "secret", "token", "password", "passwd", "pwd", "auth")


@dataclass
class EnvProfile:
    path: str
    total_keys: int
    empty_values: int
    numeric_values: int
    boolean_values: int
    secret_like_keys: int
    other_values: int
    avg_value_length: float
    max_value_length: int
    min_value_length: int
    category_counts: Dict[str, int] = field(default_factory=dict)

    def __str__(self) -> str:  # pragma: no cover
        lines = [
            f"Profile: {self.path}",
            f"  Total keys       : {self.total_keys}",
            f"  Empty values     : {self.empty_values}",
            f"  Numeric values   : {self.numeric_values}",
            f"  Boolean values   : {self.boolean_values}",
            f"  Secret-like keys : {self.secret_like_keys}",
            f"  Other values     : {self.other_values}",
            f"  Avg value length : {self.avg_value_length:.1f}",
            f"  Max value length : {self.max_value_length}",
            f"  Min value length : {self.min_value_length}",
        ]
        return "\n".join(lines)


def _categorise(key: str, value: str) -> str:
    if value == "":
        return "empty"
    if value.lstrip("-").replace(".", "", 1).isdigit():
        return "numeric"
    if value.lower() in _BOOL_VALUES:
        return "boolean"
    if any(frag in key.lower() for frag in _SECRET_FRAGMENTS):
        return "secret_like"
    return "other"


def profile_file(path: str | Path) -> EnvProfile:
    """Parse *path* and return an :class:`EnvProfile`."""
    try:
        env = parse_env_file(str(path))
    except EnvParseError as exc:
        raise ProfileError(f"Cannot profile {path}: {exc}") from exc

    if not env:
        return EnvProfile(
            path=str(path),
            total_keys=0,
            empty_values=0,
            numeric_values=0,
            boolean_values=0,
            secret_like_keys=0,
            other_values=0,
            avg_value_length=0.0,
            max_value_length=0,
            min_value_length=0,
            category_counts={},
        )

    lengths = [len(v) for v in env.values()]
    categories = {k: _categorise(k, v) for k, v in env.items()}
    counts: Dict[str, int] = {}
    for cat in categories.values():
        counts[cat] = counts.get(cat, 0) + 1

    return EnvProfile(
        path=str(path),
        total_keys=len(env),
        empty_values=counts.get("empty", 0),
        numeric_values=counts.get("numeric", 0),
        boolean_values=counts.get("boolean", 0),
        secret_like_keys=counts.get("secret_like", 0),
        other_values=counts.get("other", 0),
        avg_value_length=sum(lengths) / len(lengths),
        max_value_length=max(lengths),
        min_value_length=min(lengths),
        category_counts=counts,
    )
