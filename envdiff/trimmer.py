"""trimmer.py – strip leading/trailing whitespace from .env values and report changes."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List

from envdiff.parser import parse_env_file, EnvParseError


class TrimError(Exception):
    """Raised when trimming cannot be completed."""


@dataclass
class TrimEntry:
    key: str
    original: str
    trimmed: str

    @property
    def changed(self) -> bool:
        return self.original != self.trimmed

    def __str__(self) -> str:
        return f"{self.key}: {self.original!r} -> {self.trimmed!r}"


@dataclass
class TrimResult:
    entries: List[TrimEntry] = field(default_factory=list)
    source: str = ""

    @property
    def changed_entries(self) -> List[TrimEntry]:
        return [e for e in self.entries if e.changed]

    @property
    def has_changes(self) -> bool:
        return any(e.changed for e in self.entries)

    def as_dict(self) -> Dict[str, str]:
        """Return the trimmed key-value mapping."""
        return {e.key: e.trimmed for e in self.entries}


def trim_file(path: str | Path) -> TrimResult:
    """Parse *path* and return a TrimResult with trimmed values."""
    p = Path(path)
    if not p.exists():
        raise TrimError(f"File not found: {p}")
    try:
        pairs = parse_env_file(p)
    except EnvParseError as exc:
        raise TrimError(str(exc)) from exc

    entries = [
        TrimEntry(key=k, original=v, trimmed=v.strip())
        for k, v in pairs.items()
    ]
    return TrimResult(entries=entries, source=str(p))


def write_trimmed(result: TrimResult, output: str | Path) -> None:
    """Write the trimmed key=value pairs to *output*."""
    out = Path(output)
    lines = [f"{e.key}={e.trimmed}\n" for e in result.entries]
    out.write_text("".join(lines), encoding="utf-8")
