"""renamer.py – suggest or apply key renames across two .env files.

A 'rename' is detected when a key exists only in one file but a
similar key (by edit-distance or common prefix stripping) exists in
the other, suggesting the key was renamed rather than added/removed.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envdiff.comparator import CompareResult, KeyDiff


class RenameError(Exception):
    """Raised when rename detection fails."""


@dataclass
class RenameCandidate:
    left_key: str
    right_key: str
    confidence: float  # 0.0 – 1.0

    def __str__(self) -> str:  # pragma: no cover
        pct = int(self.confidence * 100)
        return f"{self.left_key!r} -> {self.right_key!r} ({pct}% confidence)"


@dataclass
class RenameResult:
    candidates: List[RenameCandidate] = field(default_factory=list)
    unmatched_left: List[str] = field(default_factory=list)
    unmatched_right: List[str] = field(default_factory=list)

    @property
    def has_candidates(self) -> bool:
        return bool(self.candidates)


def _similarity(a: str, b: str) -> float:
    """Simple Jaccard similarity on character bigrams."""
    def bigrams(s: str):
        return {s[i:i+2] for i in range(len(s) - 1)}

    ba, bb = bigrams(a.lower()), bigrams(b.lower())
    if not ba and not bb:
        return 1.0
    if not ba or not bb:
        return 0.0
    return len(ba & bb) / len(ba | bb)


def detect_renames(
    result: CompareResult,
    threshold: float = 0.5,
) -> RenameResult:
    """Detect likely renames among missing keys in *result*.

    Keys that appear only in the left file (missing_in_right) are
    compared against keys that appear only in the right file
    (missing_in_left).  Pairs whose bigram similarity exceeds
    *threshold* are returned as :class:`RenameCandidate` objects,
    sorted by descending confidence.

    Args:
        result:    A :class:`CompareResult` from the comparator.
        threshold: Minimum similarity score to consider a rename.

    Returns:
        :class:`RenameResult` with matched candidates and leftovers.

    Raises:
        :class:`RenameError`: if *result* is ``None``.
    """
    if result is None:
        raise RenameError("result must not be None")

    left_only = list(result.missing_in_right)   # present in left, absent right
    right_only = list(result.missing_in_left)   # present in right, absent left

    candidates: List[RenameCandidate] = []
    matched_left: set = set()
    matched_right: set = set()

    scored = []
    for lk in left_only:
        for rk in right_only:
            sim = _similarity(lk, rk)
            if sim >= threshold:
                scored.append((sim, lk, rk))

    scored.sort(key=lambda t: t[0], reverse=True)

    for sim, lk, rk in scored:
        if lk in matched_left or rk in matched_right:
            continue
        candidates.append(RenameCandidate(left_key=lk, right_key=rk, confidence=sim))
        matched_left.add(lk)
        matched_right.add(rk)

    return RenameResult(
        candidates=candidates,
        unmatched_left=[k for k in left_only if k not in matched_left],
        unmatched_right=[k for k in right_only if k not in matched_right],
    )
