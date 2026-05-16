"""Inspector: produce a detailed per-key inspection report for a single .env file."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from envdiff.parser import parse_env_file, EnvParseError


class InspectError(Exception):
    """Raised when inspection cannot be completed."""


@dataclass
class KeyInspection:
    key: str
    value: str
    is_empty: bool
    is_numeric: bool
    is_boolean: bool
    is_url: bool
    char_count: int
    has_whitespace: bool

    def __str__(self) -> str:  # pragma: no cover
        flags = []
        if self.is_empty:
            flags.append("empty")
        if self.is_numeric:
            flags.append("numeric")
        if self.is_boolean:
            flags.append("boolean")
        if self.is_url:
            flags.append("url")
        if self.has_whitespace:
            flags.append("has-whitespace")
        tag = ", ".join(flags) if flags else "plain"
        return f"{self.key}={self.value!r} [{tag}] ({self.char_count} chars)"


@dataclass
class InspectResult:
    path: str
    keys: List[KeyInspection] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.keys)

    def find(self, key: str) -> Optional[KeyInspection]:
        for k in self.keys:
            if k.key == key:
                return k
        return None


_BOOLEAN_VALUES = {"true", "false", "yes", "no", "1", "0", "on", "off"}


def _inspect_key(key: str, value: str) -> KeyInspection:
    stripped = value.strip()
    is_empty = stripped == ""
    is_numeric = False
    if not is_empty:
        try:
            float(stripped)
            is_numeric = True
        except ValueError:
            pass
    is_boolean = stripped.lower() in _BOOLEAN_VALUES
    is_url = stripped.startswith(("http://", "https://", "ftp://"))
    has_whitespace = value != stripped
    return KeyInspection(
        key=key,
        value=value,
        is_empty=is_empty,
        is_numeric=is_numeric,
        is_boolean=is_boolean,
        is_url=is_url,
        char_count=len(value),
        has_whitespace=has_whitespace,
    )


def inspect_file(path: str) -> InspectResult:
    """Parse *path* and return a detailed inspection of every key."""
    p = Path(path)
    if not p.exists():
        raise InspectError(f"File not found: {path}")
    try:
        env = parse_env_file(path)
    except EnvParseError as exc:
        raise InspectError(str(exc)) from exc
    result = InspectResult(path=path)
    for key, value in env.items():
        result.keys.append(_inspect_key(key, value))
    return result
