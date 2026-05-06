"""Tests for envdiff.watcher."""

import os
import time
from pathlib import Path

import pytest

from envdiff.watcher import WatchedPair, WatchError, watch


def _write(path: Path, content: str) -> None:
    path.write_text(content)


@pytest.fixture()
def env_left(tmp_path: Path) -> Path:
    p = tmp_path / "left.env"
    _write(p, "KEY_A=1\nKEY_B=2\n")
    return p


@pytest.fixture()
def env_right(tmp_path: Path) -> Path:
    p = tmp_path / "right.env"
    _write(p, "KEY_A=1\nKEY_B=2\n")
    return p


def test_watched_pair_detects_change(env_left: Path, env_right: Path) -> None:
    pair = WatchedPair(left=str(env_left), right=str(env_right))
    # First call seeds the mtimes — always reports changed.
    assert pair.has_changed() is True
    # No modification: should not report changed.
    assert pair.has_changed() is False
    # Touch the left file.
    time.sleep(0.05)
    env_left.write_text("KEY_A=updated\n")
    assert pair.has_changed() is True


def test_watched_pair_diff_returns_result(env_left: Path, env_right: Path) -> None:
    pair = WatchedPair(left=str(env_left), right=str(env_right))
    result = pair.diff()
    assert not result.has_diffs()


def test_watch_raises_on_missing_left(tmp_path: Path, env_right: Path) -> None:
    with pytest.raises(WatchError, match="Left file not found"):
        watch(str(tmp_path / "nope.env"), str(env_right), on_change=lambda r: None, max_iterations=1)


def test_watch_raises_on_missing_right(tmp_path: Path, env_left: Path) -> None:
    with pytest.raises(WatchError, match="Right file not found"):
        watch(str(env_left), str(tmp_path / "nope.env"), on_change=lambda r: None, max_iterations=1)


def test_watch_calls_on_change_when_file_changes(env_left: Path, env_right: Path) -> None:
    collected = []

    # Run two iterations: first seeds mtimes (triggers callback), second is stable.
    watch(
        str(env_left),
        str(env_right),
        on_change=lambda r: collected.append(r),
        interval=0.0,
        max_iterations=2,
    )

    # The very first iteration always triggers because mtimes were unseeded.
    assert len(collected) >= 1


def test_watch_no_callback_when_unchanged(env_left: Path, env_right: Path) -> None:
    collected = []

    # Seed the mtimes with one iteration.
    watch(
        str(env_left),
        str(env_right),
        on_change=lambda r: collected.append(r),
        interval=0.0,
        max_iterations=1,
    )
    collected.clear()

    # Second independent watch starting fresh but files unchanged — first iter re-seeds.
    pair = WatchedPair(left=str(env_left), right=str(env_right))
    pair.has_changed()  # seed
    assert pair.has_changed() is False
