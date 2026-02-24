"""Tests for state load/save with atomic write."""

from __future__ import annotations

from pathlib import Path

from fetcharr.state import AppState, FetcharrState, load_state, save_state


def test_state_round_trip(tmp_path: Path) -> None:
    """State saved and loaded back retains all cursor values."""
    state_file = tmp_path / "state.json"
    state = FetcharrState(
        radarr=AppState(missing_cursor=42, cutoff_cursor=7, last_run="2026-01-15T10:00:00Z"),
        sonarr=AppState(missing_cursor=100, cutoff_cursor=25, last_run="2026-01-15T10:05:00Z"),
        search_log=[{"action": "search", "count": 5}],
    )

    save_state(state, state_file)
    loaded = load_state(state_file)

    assert loaded["radarr"]["missing_cursor"] == 42
    assert loaded["radarr"]["cutoff_cursor"] == 7
    assert loaded["radarr"]["last_run"] == "2026-01-15T10:00:00Z"
    assert loaded["sonarr"]["missing_cursor"] == 100
    assert loaded["sonarr"]["cutoff_cursor"] == 25
    assert loaded["search_log"] == [{"action": "search", "count": 5}]


def test_state_default_on_missing_file(tmp_path: Path) -> None:
    """Loading from nonexistent path returns default state at cursor 0."""
    state_file = tmp_path / "nonexistent" / "state.json"

    state = load_state(state_file)

    assert state["radarr"]["missing_cursor"] == 0
    assert state["radarr"]["cutoff_cursor"] == 0
    assert state["radarr"]["last_run"] is None
    assert state["sonarr"]["missing_cursor"] == 0
    assert state["sonarr"]["cutoff_cursor"] == 0
    assert state["sonarr"]["last_run"] is None
    assert state["search_log"] == []


def test_state_atomic_write(tmp_path: Path) -> None:
    """After save, state file exists and no .tmp files remain."""
    state_file = tmp_path / "state.json"
    state = FetcharrState(
        radarr=AppState(missing_cursor=1, cutoff_cursor=2, last_run=None),
        sonarr=AppState(missing_cursor=3, cutoff_cursor=4, last_run=None),
        search_log=[],
    )

    save_state(state, state_file)

    assert state_file.exists()
    # No .tmp files should remain in the directory
    tmp_files = list(tmp_path.glob("*.tmp"))
    assert len(tmp_files) == 0


def test_state_creates_parent_dirs(tmp_path: Path) -> None:
    """Saving to a path with non-existent parents creates them."""
    state_file = tmp_path / "deep" / "nested" / "state.json"
    state = FetcharrState(
        radarr=AppState(missing_cursor=0, cutoff_cursor=0, last_run=None),
        sonarr=AppState(missing_cursor=0, cutoff_cursor=0, last_run=None),
        search_log=[],
    )

    save_state(state, state_file)

    assert state_file.exists()
    loaded = load_state(state_file)
    assert loaded["radarr"]["missing_cursor"] == 0
