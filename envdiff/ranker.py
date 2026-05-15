"""Rank keys across a CompareResult by severity of their diff status."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum
from typing import List

from envdiff.comparator import CompareResult


class RankError(Exception):
    """Raised when ranking cannot be performed."""


class Severity(IntEnum):
    MISSING = 3   # key absent from one side — highest priority
    MISMATCH = 2  # key present on both sides but values differ
    OK = 1        # key is identical on both sides


@dataclass
class RankedKey:
    key: str
    severity: Severity
    left_value: str | None = None
    right_value: str | None = None

    def __str__(self) -> str:
        return f"{self.severity.name:<10} {self.key}"


@dataclass
class RankResult:
    ranked: List[RankedKey] = field(default_factory=list)

    def by_severity(self) -> List[RankedKey]:
        """Return keys sorted highest severity first, then alphabetically."""
        return sorted(self.ranked, key=lambda r: (-r.severity.value, r.key))

    def top(self, n: int = 10) -> List[RankedKey]:
        """Return the top-n highest-severity keys."""
        if n < 1:
            raise RankError("n must be a positive integer")
        return self.by_severity()[:n]

    def __len__(self) -> int:
        return len(self.ranked)


def rank_result(result: CompareResult) -> RankResult:
    """Produce a RankResult from a CompareResult."""
    if result is None:
        raise RankError("result must not be None")

    ranked: List[RankedKey] = []

    for key in result.missing_in_right:
        ranked.append(RankedKey(key=key, severity=Severity.MISSING,
                                left_value=result.left.get(key),
                                right_value=None))

    for key in result.missing_in_left:
        ranked.append(RankedKey(key=key, severity=Severity.MISSING,
                                left_value=None,
                                right_value=result.right.get(key)))

    for diff in result.mismatches:
        ranked.append(RankedKey(key=diff.key, severity=Severity.MISMATCH,
                                left_value=diff.left_value,
                                right_value=diff.right_value))

    common_keys = set(result.left) & set(result.right)
    mismatch_keys = {d.key for d in result.mismatches}
    for key in sorted(common_keys - mismatch_keys):
        ranked.append(RankedKey(key=key, severity=Severity.OK,
                                left_value=result.left.get(key),
                                right_value=result.right.get(key)))

    return RankResult(ranked=ranked)
