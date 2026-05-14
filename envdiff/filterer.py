"""Filter comparison results by key pattern or diff type."""

from __future__ import annotations

import fnmatch
import re
from dataclasses import dataclass, field
from typing import Optional

from envdiff.comparator import CompareResult, KeyDiff


class FilterError(Exception):
    """Raised when a filter pattern is invalid."""


@dataclass
class FilterOptions:
    """Options controlling how results are filtered."""

    pattern: Optional[str] = None          # glob or regex pattern for key names
    use_regex: bool = False                # treat pattern as regex instead of glob
    missing_only: bool = False             # include only keys missing in either side
    mismatch_only: bool = False            # include only value mismatches
    exclude_pattern: Optional[str] = None  # keys matching this pattern are excluded


def filter_result(result: CompareResult, options: FilterOptions) -> CompareResult:
    """Return a new CompareResult containing only diffs that satisfy *options*."""
    if options.missing_only and options.mismatch_only:
        raise FilterError(
            "'missing_only' and 'mismatch_only' are mutually exclusive."
        )

    _compile = _make_matcher(options.pattern, options.use_regex) if options.pattern else None
    _exclude = _make_matcher(options.exclude_pattern, options.use_regex) if options.exclude_pattern else None

    filtered: list[KeyDiff] = []
    for diff in result.diffs:
        key = diff.key

        if _compile and not _compile(key):
            continue
        if _exclude and _exclude(key):
            continue
        if options.missing_only and diff.left_value is not None and diff.right_value is not None:
            continue
        if options.mismatch_only and (diff.left_value is None or diff.right_value is None):
            continue

        filtered.append(diff)

    return CompareResult(
        left_path=result.left_path,
        right_path=result.right_path,
        diffs=filtered,
    )


def _make_matcher(pattern: str, use_regex: bool):
    """Return a callable that returns True when a key matches *pattern*."""
    if use_regex:
        try:
            compiled = re.compile(pattern)
        except re.error as exc:
            raise FilterError(f"Invalid regex pattern '{pattern}': {exc}") from exc
        return lambda key: bool(compiled.search(key))
    return lambda key: fnmatch.fnmatch(key, pattern)
