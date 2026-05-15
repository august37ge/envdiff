"""streaker.py – track consecutive 'clean' diff runs (streaks) for a file pair.

A streak counts how many times in a row two env files have produced zero diffs.
Results are persisted to a simple JSON file so the streak survives across runs.
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


class StreakerError(Exception):  # noqa: N818
    """Raised when streak persistence fails."""


@dataclass
class StreakRecord:
    left: str
    right: str
    current_streak: int = 0
    best_streak: int = 0
    last_run_ts: Optional[float] = None
    last_run_clean: Optional[bool] = None

    def to_dict(self) -> dict:
        return {
            "left": self.left,
            "right": self.right,
            "current_streak": self.current_streak,
            "best_streak": self.best_streak,
            "last_run_ts": self.last_run_ts,
            "last_run_clean": self.last_run_clean,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "StreakRecord":
        return cls(
            left=data["left"],
            right=data["right"],
            current_streak=data.get("current_streak", 0),
            best_streak=data.get("best_streak", 0),
            last_run_ts=data.get("last_run_ts"),
            last_run_clean=data.get("last_run_clean"),
        )


def load_streak(path: Path) -> StreakRecord:
    """Load an existing StreakRecord from *path*."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return StreakRecord.from_dict(data)
    except (OSError, json.JSONDecodeError, KeyError) as exc:
        raise StreakerError(f"Cannot load streak file '{path}': {exc}") from exc


def save_streak(record: StreakRecord, path: Path) -> None:
    """Persist *record* to *path* as JSON."""
    try:
        path.write_text(json.dumps(record.to_dict(), indent=2), encoding="utf-8")
    except OSError as exc:
        raise StreakerError(f"Cannot save streak file '{path}': {exc}") from exc


def record_run(
    record: StreakRecord,
    is_clean: bool,
    *,
    ts: Optional[float] = None,
) -> StreakRecord:
    """Update *record* with the outcome of a new diff run.

    Returns the mutated record (mutated in-place for convenience).
    """
    record.last_run_ts = ts if ts is not None else time.time()
    record.last_run_clean = is_clean
    if is_clean:
        record.current_streak += 1
        if record.current_streak > record.best_streak:
            record.best_streak = record.current_streak
    else:
        record.current_streak = 0
    return record
