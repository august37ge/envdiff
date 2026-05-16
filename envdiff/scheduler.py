"""scheduler.py – schedule periodic env-diff checks and record results."""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, List, Optional

from envdiff.comparator import CompareResult


class SchedulerError(Exception):
    """Raised when the scheduler encounters a configuration problem."""


@dataclass
class ScheduleEntry:
    """A single recorded run produced by the scheduler."""

    timestamp: float
    left: str
    right: str
    has_diffs: bool
    missing_in_left: int
    missing_in_right: int
    mismatches: int

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "left": self.left,
            "right": self.right,
            "has_diffs": self.has_diffs,
            "missing_in_left": self.missing_in_left,
            "missing_in_right": self.missing_in_right,
            "mismatches": self.mismatches,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ScheduleEntry":
        return cls(
            timestamp=float(data["timestamp"]),
            left=data["left"],
            right=data["right"],
            has_diffs=bool(data["has_diffs"]),
            missing_in_left=int(data["missing_in_left"]),
            missing_in_right=int(data["missing_in_right"]),
            mismatches=int(data["mismatches"]),
        )


@dataclass
class ScheduleLog:
    """Ordered list of schedule run entries."""

    entries: List[ScheduleEntry] = field(default_factory=list)

    def append(self, entry: ScheduleEntry) -> None:
        self.entries.append(entry)

    def to_dict(self) -> dict:
        return {"entries": [e.to_dict() for e in self.entries]}

    @classmethod
    def from_dict(cls, data: dict) -> "ScheduleLog":
        return cls(entries=[ScheduleEntry.from_dict(e) for e in data.get("entries", [])])


def record_run(
    left: str,
    right: str,
    result: CompareResult,
    *,
    clock: Callable[[], float] = time.time,
) -> ScheduleEntry:
    """Convert a CompareResult into a ScheduleEntry stamped with the current time."""
    return ScheduleEntry(
        timestamp=clock(),
        left=left,
        right=right,
        has_diffs=result.has_diffs(),
        missing_in_left=len(result.missing_in_left()),
        missing_in_right=len(result.missing_in_right()),
        mismatches=len(result.mismatches()),
    )


def save_log(log: ScheduleLog, path: Path) -> None:
    """Persist a ScheduleLog to *path* as JSON (appends to existing log)."""
    existing: ScheduleLog
    if path.exists():
        try:
            existing = ScheduleLog.from_dict(json.loads(path.read_text()))
        except Exception as exc:  # noqa: BLE001
            raise SchedulerError(f"Cannot read existing log {path}: {exc}") from exc
    else:
        existing = ScheduleLog()
    for entry in log.entries:
        existing.append(entry)
    path.write_text(json.dumps(existing.to_dict(), indent=2))


def load_log(path: Path) -> ScheduleLog:
    """Load a ScheduleLog from *path*."""
    if not path.exists():
        raise SchedulerError(f"Log file not found: {path}")
    try:
        return ScheduleLog.from_dict(json.loads(path.read_text()))
    except Exception as exc:  # noqa: BLE001
        raise SchedulerError(f"Cannot parse log {path}: {exc}") from exc
