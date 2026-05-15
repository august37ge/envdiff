"""sorter.py – sort diff keys by various criteria."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import List

from envdiff.comparator import CompareResult, KeyDiff


class SortError(Exception):
    """Raised when sorting cannot be performed."""


class SortKey(str, Enum):
    NAME = "name"          # alphabetical by key name
    SEVERITY = "severity"  # missing first, then mismatch, then ok
    STATUS = "status"      # group by diff type


_STATUS_ORDER = {"missing_left": 0, "missing_right": 1, "mismatch": 2, "ok": 3}


@dataclass
class SortOptions:
    key: SortKey = SortKey.NAME
    reverse: bool = False


def _severity_rank(diff: KeyDiff) -> int:
    if diff.left_value is None:
        return _STATUS_ORDER["missing_left"]
    if diff.right_value is None:
        return _STATUS_ORDER["missing_right"]
    if diff.left_value != diff.right_value:
        return _STATUS_ORDER["mismatch"]
    return _STATUS_ORDER["ok"]


def sort_diffs(result: CompareResult, options: SortOptions | None = None) -> List[KeyDiff]:
    """Return a sorted list of KeyDiff entries from *result*.

    Args:
        result:  A ``CompareResult`` produced by the comparator.
        options: Sorting options; defaults to alphabetical ascending.

    Returns:
        A new list of ``KeyDiff`` objects in the requested order.

    Raises:
        SortError: If *result* is None.
    """
    if result is None:
        raise SortError("result must not be None")

    if options is None:
        options = SortOptions()

    diffs: List[KeyDiff] = list(result.diffs)

    if options.key == SortKey.NAME:
        diffs.sort(key=lambda d: d.key, reverse=options.reverse)
    elif options.key in (SortKey.SEVERITY, SortKey.STATUS):
        diffs.sort(
            key=lambda d: (_severity_rank(d), d.key),
            reverse=options.reverse,
        )
    else:
        raise SortError(f"Unknown sort key: {options.key!r}")

    return diffs
