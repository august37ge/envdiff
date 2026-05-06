"""Watch .env files for changes and report diffs automatically."""

import time
import os
from dataclasses import dataclass, field
from typing import Callable, Dict, Optional

from envdiff.differ import diff_files
from envdiff.comparator import CompareResult


class WatchError(Exception):
    """Raised when the watcher encounters an unrecoverable error."""


@dataclass
class WatchedPair:
    left: str
    right: str
    _mtimes: Dict[str, float] = field(default_factory=dict, init=False, repr=False)

    def _mtime(self, path: str) -> float:
        try:
            return os.path.getmtime(path)
        except OSError:
            return -1.0

    def has_changed(self) -> bool:
        """Return True if either file has been modified since last check."""
        new_left = self._mtime(self.left)
        new_right = self._mtime(self.right)
        changed = (
            self._mtimes.get(self.left) != new_left
            or self._mtimes.get(self.right) != new_right
        )
        self._mtimes[self.left] = new_left
        self._mtimes[self.right] = new_right
        return changed

    def diff(self) -> CompareResult:
        """Run a diff on the watched pair."""
        return diff_files(self.left, self.right)


def watch(
    left: str,
    right: str,
    on_change: Callable[[CompareResult], None],
    interval: float = 1.0,
    max_iterations: Optional[int] = None,
) -> None:
    """Poll *left* and *right* for changes and invoke *on_change* with the diff.

    Args:
        left: Path to the left .env file.
        right: Path to the right .env file.
        on_change: Callback invoked with a CompareResult whenever a change is detected.
        interval: Polling interval in seconds.
        max_iterations: Stop after this many iterations (useful for testing).
    """
    if not os.path.isfile(left):
        raise WatchError(f"Left file not found: {left}")
    if not os.path.isfile(right):
        raise WatchError(f"Right file not found: {right}")

    pair = WatchedPair(left=left, right=right)
    iterations = 0

    while True:
        if pair.has_changed():
            result = pair.diff()
            on_change(result)

        iterations += 1
        if max_iterations is not None and iterations >= max_iterations:
            break

        time.sleep(interval)
