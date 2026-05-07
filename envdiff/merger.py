"""Merge multiple .env files into a unified key set, with conflict detection."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from envdiff.parser import parse_env_file, EnvParseError


class MergeError(Exception):
    """Raised when merging fails due to invalid input."""


@dataclass
class MergeConflict:
    key: str
    values: Dict[str, str]  # source_label -> value

    def __str__(self) -> str:
        parts = ", ".join(f"{src}={val!r}" for src, val in self.values.items())
        return f"CONFLICT {self.key}: {parts}"


@dataclass
class MergeResult:
    merged: Dict[str, str] = field(default_factory=dict)
    conflicts: List[MergeConflict] = field(default_factory=list)
    sources: List[str] = field(default_factory=list)

    @property
    def has_conflicts(self) -> bool:
        return len(self.conflicts) > 0


def merge_env_files(
    paths: List[Path],
    labels: Optional[List[str]] = None,
    strategy: str = "first",
) -> MergeResult:
    """Merge multiple .env files.

    Args:
        paths: List of .env file paths to merge.
        labels: Optional display names for each file; defaults to file names.
        strategy: Conflict resolution strategy — 'first' keeps the first value,
                  'last' keeps the last value.

    Returns:
        MergeResult containing merged keys, conflicts, and source labels.

    Raises:
        MergeError: If fewer than two paths are provided or a file cannot be parsed.
    """
    if len(paths) < 2:
        raise MergeError("At least two files are required for merging.")

    if strategy not in ("first", "last"):
        raise MergeError(f"Unknown strategy {strategy!r}; use 'first' or 'last'.")

    if labels is None:
        labels = [p.name for p in paths]

    if len(labels) != len(paths):
        raise MergeError("Number of labels must match number of paths.")

    parsed: List[Dict[str, str]] = []
    for path in paths:
        try:
            parsed.append(parse_env_file(path))
        except EnvParseError as exc:
            raise MergeError(f"Failed to parse {path}: {exc}") from exc

    merged: Dict[str, str] = {}
    conflict_map: Dict[str, Dict[str, str]] = {}

    for env, label in zip(parsed, labels):
        for key, value in env.items():
            if key not in merged:
                merged[key] = value
            elif merged[key] != value:
                if key not in conflict_map:
                    # find which earlier label set this value
                    for prev_label, prev_env in zip(labels, parsed):
                        if prev_label == label:
                            break
                        if key in prev_env:
                            conflict_map[key] = {prev_label: merged[key]}
                            break
                conflict_map[key][label] = value
                if strategy == "last":
                    merged[key] = value

    conflicts = [
        MergeConflict(key=k, values=v) for k, v in conflict_map.items()
    ]

    return MergeResult(merged=merged, conflicts=conflicts, sources=labels)
