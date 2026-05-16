"""Detect and report duplicate keys within a single .env file."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List


class DeduplicatorError(Exception):
    """Raised when deduplication cannot be performed."""


@dataclass
class DuplicateEntry:
    key: str
    occurrences: List[int]  # 1-based line numbers

    def __str__(self) -> str:
        lines = ", ".join(str(n) for n in self.occurrences)
        return f"{self.key} (lines {lines})"


@dataclass
class DeduplicateResult:
    path: Path
    duplicates: List[DuplicateEntry] = field(default_factory=list)

    @property
    def has_duplicates(self) -> bool:
        return bool(self.duplicates)

    def __str__(self) -> str:
        if not self.has_duplicates:
            return f"{self.path}: no duplicate keys"
        lines = [f"{self.path}: {len(self.duplicates)} duplicate key(s)"]
        for entry in self.duplicates:
            lines.append(f"  {entry}")
        return "\n".join(lines)


def find_duplicates(path: str | Path) -> DeduplicateResult:
    """Scan *path* for duplicate keys and return a DeduplicateResult.

    Only non-blank, non-comment lines that contain '=' are considered.
    The *last* value for a duplicated key is what parsers typically use,
    but this function reports all occurrences so the caller can decide.
    """
    resolved = Path(path)
    if not resolved.exists():
        raise DeduplicatorError(f"File not found: {resolved}")

    seen: Dict[str, List[int]] = {}
    try:
        text = resolved.read_text(encoding="utf-8")
    except OSError as exc:
        raise DeduplicatorError(f"Cannot read {resolved}: {exc}") from exc

    for lineno, raw in enumerate(text.splitlines(), start=1):
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" not in stripped:
            continue
        key = stripped.split("=", 1)[0].strip()
        if not key:
            continue
        seen.setdefault(key, []).append(lineno)

    duplicates = [
        DuplicateEntry(key=k, occurrences=v)
        for k, v in seen.items()
        if len(v) > 1
    ]
    duplicates.sort(key=lambda d: d.occurrences[0])
    return DeduplicateResult(path=resolved, duplicates=duplicates)
