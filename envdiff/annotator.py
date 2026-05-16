"""annotator.py – attach human-readable annotations to diff keys.

An annotation is a short string comment associated with a specific key,
loaded from a TOML-like annotations file (KEY = "comment" lines).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional

from envdiff.comparator import CompareResult, KeyDiff


class AnnotatorError(Exception):
    """Raised when annotation loading or application fails."""


@dataclass
class AnnotatedKey:
    diff: KeyDiff
    annotation: Optional[str] = None

    def __str__(self) -> str:
        base = str(self.diff)
        if self.annotation:
            return f"{base}  # {self.annotation}"
        return base


@dataclass
class AnnotateResult:
    annotated: list[AnnotatedKey] = field(default_factory=list)
    unannotated_count: int = 0

    @property
    def total(self) -> int:
        return len(self.annotated)


def load_annotations(path: Path) -> Dict[str, str]:
    """Parse a simple KEY = "comment" annotations file."""
    if not path.exists():
        raise AnnotatorError(f"Annotations file not found: {path}")
    annotations: Dict[str, str] = {}
    for lineno, raw in enumerate(path.read_text().splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise AnnotatorError(f"Invalid annotation at line {lineno}: {raw!r}")
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if not key:
            raise AnnotatorError(f"Empty key at line {lineno}: {raw!r}")
        annotations[key] = value
    return annotations


def annotate_result(
    result: CompareResult,
    annotations: Dict[str, str],
) -> AnnotateResult:
    """Attach annotations to every KeyDiff in *result*."""
    if result is None:
        raise AnnotatorError("result must not be None")
    annotated: list[AnnotatedKey] = []
    unannotated = 0
    all_diffs = (
        list(result.missing_in_right)
        + list(result.missing_in_left)
        + list(result.mismatched)
    )
    for diff in all_diffs:
        note = annotations.get(diff.key)
        if note is None:
            unannotated += 1
        annotated.append(AnnotatedKey(diff=diff, annotation=note))
    return AnnotateResult(annotated=annotated, unannotated_count=unannotated)
