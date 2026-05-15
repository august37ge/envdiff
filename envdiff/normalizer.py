"""Normalize .env file values for consistent comparison.

Provides utilities to strip quotes, expand common escape sequences,
and optionally lowercase keys before comparison.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict


class NormalizeError(Exception):
    """Raised when normalization cannot be completed."""


@dataclass
class NormalizeOptions:
    lowercase_keys: bool = False
    strip_quotes: bool = True
    expand_escapes: bool = True


_ESCAPE_MAP: Dict[str, str] = {
    "\\n": "\n",
    "\\t": "\t",
    "\\r": "\r",
    "\\\\": "\\",
}


def _strip_quotes(value: str) -> str:
    """Remove surrounding single or double quotes from a value."""
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
        return value[1:-1]
    return value


def _expand_escapes(value: str) -> str:
    """Replace common escape sequences with their real characters."""
    for seq, char in _ESCAPE_MAP.items():
        value = value.replace(seq, char)
    return value


def normalize_value(value: str, options: NormalizeOptions | None = None) -> str:
    """Normalize a single env value according to *options*."""
    if options is None:
        options = NormalizeOptions()
    if options.strip_quotes:
        value = _strip_quotes(value)
    if options.expand_escapes:
        value = _expand_escapes(value)
    return value


def normalize_key(key: str, options: NormalizeOptions | None = None) -> str:
    """Normalize a single env key according to *options*."""
    if options is None:
        options = NormalizeOptions()
    if options.lowercase_keys:
        return key.lower()
    return key


def normalize_env(
    env: Dict[str, str],
    options: NormalizeOptions | None = None,
) -> Dict[str, str]:
    """Return a new dict with all keys and values normalized.

    Raises NormalizeError if duplicate keys result from key normalization.
    """
    if options is None:
        options = NormalizeOptions()
    result: Dict[str, str] = {}
    for raw_key, raw_value in env.items():
        nk = normalize_key(raw_key, options)
        if nk in result:
            raise NormalizeError(
                f"Duplicate key after normalization: {nk!r} "
                f"(original keys: {raw_key!r})"
            )
        result[nk] = normalize_value(raw_value, options)
    return result
