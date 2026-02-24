"""Atomic JSON state persistence for Fetcharr.

State tracks round-robin cursor positions and search history
across container restarts. All writes use atomic write-then-rename
to prevent corruption if the process crashes mid-write.
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import TypedDict

STATE_PATH = Path("/config/state.json")


class AppState(TypedDict, total=False):
    """Per-app cursor and timing state."""

    missing_cursor: int
    cutoff_cursor: int
    last_run: str | None  # ISO timestamp
    connected: bool | None  # True after successful fetch, False after failure
    unreachable_since: str | None  # ISO timestamp of first failure, None when healthy
    missing_count: int | None  # Total wanted-missing items (before filtering)
    cutoff_count: int | None  # Total cutoff-unmet items (before filtering)


class FetcharrState(TypedDict, total=False):
    """Top-level application state."""

    radarr: AppState
    sonarr: AppState
    search_log: list[dict]  # bounded log of recent searches


def _default_state() -> FetcharrState:
    """Return a fresh default state with both apps at cursor 0."""
    return FetcharrState(
        radarr=AppState(missing_cursor=0, cutoff_cursor=0, last_run=None),
        sonarr=AppState(missing_cursor=0, cutoff_cursor=0, last_run=None),
        search_log=[],
    )


def load_state(state_path: Path = STATE_PATH) -> FetcharrState:
    """Load state from a JSON file.

    If the file does not exist, returns a default empty state
    with both apps at cursor position 0.

    Args:
        state_path: Path to the state JSON file.

    Returns:
        Parsed state dictionary.
    """
    if not state_path.exists():
        return _default_state()

    with open(state_path) as f:
        return json.load(f)


def save_state(state: FetcharrState, state_path: Path = STATE_PATH) -> None:
    """Atomically write state to disk.

    Uses write-to-temp-file then ``os.replace()`` to ensure the state
    file is never left in a partially written state. This prevents
    corruption if the process crashes mid-write.

    Args:
        state: State dictionary to persist.
        state_path: Destination path for the state file.
    """
    parent = state_path.parent
    parent.mkdir(parents=True, exist_ok=True)

    with tempfile.NamedTemporaryFile(
        mode="w", dir=parent, suffix=".tmp", delete=False
    ) as tmp:
        json.dump(state, tmp, indent=2)
        tmp.flush()
        os.fsync(tmp.fileno())

    os.replace(tmp.name, state_path)
