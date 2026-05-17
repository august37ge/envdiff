"""Chain multiple .env files and compare each consecutive pair."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Sequence

from envdiff.comparator import CompareResult
from envdiff.differ import diff_files


class ChainError(Exception):
    """Raised when a chained diff cannot be performed."""


@dataclass
class ChainLink:
    """Result of comparing one consecutive pair in the chain."""

    left: Path
    right: Path
    result: CompareResult

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.left.name} -> {self.right.name}"


@dataclass
class ChainResult:
    """Aggregated results for all consecutive pairs."""

    links: List[ChainLink] = field(default_factory=list)

    def any_diffs(self) -> bool:
        return any(link.result.has_diffs() for link in self.links)

    def links_with_diffs(self) -> List[ChainLink]:
        return [link for link in self.links if link.result.has_diffs()]

    def __len__(self) -> int:
        return len(self.links)


def diff_chain(paths: Sequence[str | Path]) -> ChainResult:
    """Compare each consecutive pair of *paths* and return a ChainResult.

    Parameters
    ----------
    paths:
        At least two file paths to compare in order.

    Raises
    ------
    ChainError
        If fewer than two paths are provided or any path does not exist.
    """
    resolved = [Path(p) for p in paths]

    if len(resolved) < 2:
        raise ChainError("At least two files are required for a chain diff.")

    for p in resolved:
        if not p.exists():
            raise ChainError(f"File not found: {p}")

    chain = ChainResult()
    for left, right in zip(resolved, resolved[1:]):
        result = diff_files(left, right)
        chain.links.append(ChainLink(left=left, right=right, result=result))

    return chain
