"""Comprehensive tests for search engine utility functions and cycle orchestrators.

Tests cover: filtering (monitored, air dates), batch slicing (normal,
wrap, empty, past-end cursor), search log (add, format, eviction),
deduplication (collapse, order, display name, fallback),
Sonarr-specific filtering (unmonitored, future, null, past, malformed),
and async cycle orchestration (happy path, network failure, per-item skip,
cursor advancement) for both run_radarr_cycle and run_sonarr_cycle.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock

import httpx

from fetcharr.search.engine import (
    SEARCH_LOG_MAX,
    append_search_log,
    deduplicate_to_seasons,
    filter_monitored,
    filter_sonarr_episodes,
    run_radarr_cycle,
    run_sonarr_cycle,
    slice_batch,
)
from fetcharr.state import _default_state
from tests.conftest import make_settings


# ---------------------------------------------------------------------------
# filter_monitored
# ---------------------------------------------------------------------------


def test_filter_monitored_keeps_only_monitored():
    items = [
        {"id": 1, "monitored": True},
        {"id": 2, "monitored": False},
        {"id": 3},  # missing key
        {"id": 4, "monitored": True},
    ]
    result = filter_monitored(items)
    assert len(result) == 2
    assert result[0]["id"] == 1
    assert result[1]["id"] == 4


def test_filter_monitored_empty_list():
    assert filter_monitored([]) == []


# ---------------------------------------------------------------------------
# slice_batch
# ---------------------------------------------------------------------------


def test_slice_batch_normal():
    items = list(range(10))
    batch, new_cursor = slice_batch(items, cursor=3, batch_size=2)
    assert batch == [3, 4]
    assert new_cursor == 5


def test_slice_batch_wraps_at_end():
    items = list(range(5))
    batch, new_cursor = slice_batch(items, cursor=3, batch_size=3)
    assert batch == [3, 4]
    assert new_cursor == 0


def test_slice_batch_cursor_past_end():
    items = list(range(5))
    batch, new_cursor = slice_batch(items, cursor=99, batch_size=2)
    assert batch == [0, 1]
    assert new_cursor == 2


def test_slice_batch_empty_list():
    batch, new_cursor = slice_batch([], cursor=0, batch_size=5)
    assert batch == []
    assert new_cursor == 0


def test_slice_batch_batch_larger_than_remaining():
    items = list(range(3))
    batch, new_cursor = slice_batch(items, cursor=1, batch_size=10)
    assert batch == [1, 2]
    assert new_cursor == 0


# ---------------------------------------------------------------------------
# append_search_log
# ---------------------------------------------------------------------------


def test_append_search_log_adds_entry():
    state = _default_state()
    append_search_log(state, "Radarr", "missing", "Test Movie")
    assert len(state["search_log"]) == 1
    entry = state["search_log"][0]
    assert entry["name"] == "Test Movie"
    assert entry["app"] == "Radarr"
    assert entry["queue_type"] == "missing"
    assert "timestamp" in entry


def test_append_search_log_timestamp_format():
    state = _default_state()
    append_search_log(state, "Sonarr", "cutoff", "Test Show")
    ts = state["search_log"][0]["timestamp"]
    assert ts.endswith("Z")
    # Verify it is valid ISO format
    parsed = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    assert parsed.tzinfo is not None


def test_append_search_log_bounded_at_50():
    state = _default_state()
    for i in range(55):
        append_search_log(state, "Radarr", "missing", f"Movie {i}")
    assert len(state["search_log"]) == SEARCH_LOG_MAX
    # Oldest entries (0-4) should have been evicted; first entry is Movie 5
    assert state["search_log"][0]["name"] == "Movie 5"


# ---------------------------------------------------------------------------
# deduplicate_to_seasons
# ---------------------------------------------------------------------------


def test_deduplicate_to_seasons_removes_duplicates():
    episodes = [
        {"seriesId": 1, "seasonNumber": 2, "series": {"title": "Show A"}},
        {"seriesId": 1, "seasonNumber": 2, "series": {"title": "Show A"}},
        {"seriesId": 1, "seasonNumber": 3, "series": {"title": "Show A"}},
    ]
    result = deduplicate_to_seasons(episodes)
    assert len(result) == 2
    assert result[0]["seasonNumber"] == 2
    assert result[1]["seasonNumber"] == 3


def test_deduplicate_to_seasons_preserves_order():
    episodes = [
        {"seriesId": 2, "seasonNumber": 1, "series": {"title": "Show B"}},
        {"seriesId": 1, "seasonNumber": 3, "series": {"title": "Show A"}},
        {"seriesId": 2, "seasonNumber": 1, "series": {"title": "Show B"}},
    ]
    result = deduplicate_to_seasons(episodes)
    assert len(result) == 2
    assert result[0]["seriesId"] == 2
    assert result[1]["seriesId"] == 1


def test_deduplicate_to_seasons_display_name_format():
    episodes = [
        {"seriesId": 5, "seasonNumber": 3, "series": {"title": "Breaking Bad"}},
    ]
    result = deduplicate_to_seasons(episodes)
    assert result[0]["display_name"] == "Breaking Bad - Season 3"


def test_deduplicate_to_seasons_missing_series_data():
    episodes = [
        {"seriesId": 42, "seasonNumber": 1},
    ]
    result = deduplicate_to_seasons(episodes)
    assert result[0]["display_name"] == "Series 42 - Season 1"


# ---------------------------------------------------------------------------
# filter_sonarr_episodes
# ---------------------------------------------------------------------------


def _make_episode(
    monitored: bool = True,
    air_date_utc: str | None = "2020-01-01T00:00:00Z",
) -> dict:
    """Helper to build a Sonarr episode dict."""
    ep: dict = {"monitored": monitored, "seriesId": 1, "seasonNumber": 1}
    if air_date_utc is not None:
        ep["airDateUtc"] = air_date_utc
    return ep


def test_filter_sonarr_episodes_excludes_unmonitored():
    episodes = [_make_episode(monitored=False)]
    assert filter_sonarr_episodes(episodes) == []


def test_filter_sonarr_episodes_excludes_future_air_date():
    future = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat().replace("+00:00", "Z")
    episodes = [_make_episode(air_date_utc=future)]
    assert filter_sonarr_episodes(episodes) == []


def test_filter_sonarr_episodes_excludes_null_air_date():
    ep = _make_episode()
    del ep["airDateUtc"]  # simulate missing / TBA
    assert filter_sonarr_episodes([ep]) == []


def test_filter_sonarr_episodes_keeps_past_monitored():
    episodes = [_make_episode(monitored=True, air_date_utc="2020-06-15T12:00:00Z")]
    result = filter_sonarr_episodes(episodes)
    assert len(result) == 1
    assert result[0]["airDateUtc"] == "2020-06-15T12:00:00Z"


def test_filter_sonarr_episodes_handles_unparseable_date():
    episodes = [_make_episode(air_date_utc="not-a-date")]
    result = filter_sonarr_episodes(episodes)
    assert result == []


# ---------------------------------------------------------------------------
# run_radarr_cycle (async orchestration)
# ---------------------------------------------------------------------------


def _cycle_settings(missing_count: int = 2, cutoff_count: int = 2):
    """Build Settings tuned for predictable batching in cycle tests."""
    return make_settings(
        search_missing_count=missing_count,
        search_cutoff_count=cutoff_count,
    )


async def test_run_radarr_cycle_happy_path():
    client = AsyncMock()
    client.get_wanted_missing = AsyncMock(
        return_value=[
            {"id": 1, "title": "Movie A", "monitored": True},
            {"id": 2, "title": "Movie B", "monitored": True},
        ]
    )
    client.get_wanted_cutoff = AsyncMock(return_value=[])
    client.search_movies = AsyncMock()

    state = _default_state()
    settings = _cycle_settings(missing_count=2, cutoff_count=2)

    result = await run_radarr_cycle(client, state, settings)

    # Both movies searched (batch_size=2 covers both)
    assert client.search_movies.call_count == 2
    client.search_movies.assert_any_call([1])
    client.search_movies.assert_any_call([2])

    assert result["radarr"]["last_run"] is not None
    assert result["radarr"]["connected"] is True
    # 2 items, batch 2, cursor wraps to 0
    assert result["radarr"]["missing_cursor"] == 0


async def test_run_radarr_cycle_network_failure():
    client = AsyncMock()
    client.get_wanted_missing = AsyncMock(
        side_effect=httpx.ConnectError("refused")
    )

    state = _default_state()
    state["radarr"]["missing_cursor"] = 5
    settings = _cycle_settings()

    result = await run_radarr_cycle(client, state, settings)

    assert result["radarr"]["connected"] is False
    assert result["radarr"]["unreachable_since"] is not None
    # Cursor unchanged on abort
    assert result["radarr"]["missing_cursor"] == 5


async def test_run_radarr_cycle_per_item_skip():
    client = AsyncMock()
    client.get_wanted_missing = AsyncMock(
        return_value=[
            {"id": 1, "title": "Movie A", "monitored": True},
            {"id": 2, "title": "Movie B", "monitored": True},
        ]
    )
    client.get_wanted_cutoff = AsyncMock(return_value=[])
    # First search raises, second succeeds
    client.search_movies = AsyncMock(
        side_effect=[Exception("boom"), None]
    )

    state = _default_state()
    settings = _cycle_settings(missing_count=2, cutoff_count=2)

    result = await run_radarr_cycle(client, state, settings)

    # Did not abort after first failure -- called twice
    assert client.search_movies.call_count == 2
    # Only the successful search was logged
    assert len(result["search_log"]) == 1
    assert result["search_log"][0]["name"] == "Movie B"


async def test_run_radarr_cycle_cursor_advancement():
    movies = [
        {"id": i, "title": f"Movie {i}", "monitored": True}
        for i in range(1, 6)
    ]

    settings = _cycle_settings(missing_count=2, cutoff_count=2)

    # --- Run 1: cursor 0 -> 2 ---
    client = AsyncMock()
    client.get_wanted_missing = AsyncMock(return_value=movies)
    client.get_wanted_cutoff = AsyncMock(return_value=[])
    client.search_movies = AsyncMock()

    state = _default_state()
    state["radarr"]["missing_cursor"] = 0

    result = await run_radarr_cycle(client, state, settings)
    assert result["radarr"]["missing_cursor"] == 2

    # --- Run 2: cursor 2 -> 4 ---
    client.get_wanted_missing = AsyncMock(return_value=movies)
    client.get_wanted_cutoff = AsyncMock(return_value=[])
    client.search_movies = AsyncMock()

    result = await run_radarr_cycle(client, result, settings)
    assert result["radarr"]["missing_cursor"] == 4

    # --- Run 3: cursor 4 -> wraps to 0 (only 1 item left, then wraps) ---
    client.get_wanted_missing = AsyncMock(return_value=movies)
    client.get_wanted_cutoff = AsyncMock(return_value=[])
    client.search_movies = AsyncMock()

    result = await run_radarr_cycle(client, result, settings)
    assert result["radarr"]["missing_cursor"] == 0


# ---------------------------------------------------------------------------
# run_sonarr_cycle (async orchestration)
# ---------------------------------------------------------------------------


def _make_sonarr_episode(
    series_id: int,
    season_number: int,
    series_title: str = "Show",
    episode_id: int = 1,
) -> dict:
    """Build a Sonarr episode dict suitable for cycle tests."""
    return {
        "id": episode_id,
        "seriesId": series_id,
        "seasonNumber": season_number,
        "monitored": True,
        "airDateUtc": "2020-01-01T00:00:00Z",
        "series": {"title": series_title},
    }


async def test_run_sonarr_cycle_happy_path():
    episodes = [
        _make_sonarr_episode(series_id=10, season_number=1, series_title="Show A", episode_id=100),
        _make_sonarr_episode(series_id=10, season_number=2, series_title="Show A", episode_id=101),
    ]

    client = AsyncMock()
    client.get_wanted_missing = AsyncMock(return_value=episodes)
    client.get_wanted_cutoff = AsyncMock(return_value=[])
    client.search_season = AsyncMock()

    state = _default_state()
    settings = _cycle_settings(missing_count=2, cutoff_count=2)

    result = await run_sonarr_cycle(client, state, settings)

    # Two unique seasons from same series searched
    assert client.search_season.call_count == 2
    client.search_season.assert_any_call(10, 1)
    client.search_season.assert_any_call(10, 2)
    assert result["sonarr"]["connected"] is True
    assert result["sonarr"]["last_run"] is not None


async def test_run_sonarr_cycle_network_failure():
    client = AsyncMock()
    client.get_wanted_missing = AsyncMock(
        side_effect=httpx.ConnectError("refused")
    )

    state = _default_state()
    state["sonarr"]["missing_cursor"] = 3
    settings = _cycle_settings()

    result = await run_sonarr_cycle(client, state, settings)

    assert result["sonarr"]["connected"] is False
    assert result["sonarr"]["unreachable_since"] is not None
    assert result["sonarr"]["missing_cursor"] == 3


async def test_run_sonarr_cycle_per_item_skip():
    # Two episodes from different series -> 2 unique seasons after dedup
    episodes = [
        _make_sonarr_episode(series_id=10, season_number=1, series_title="Show A", episode_id=100),
        _make_sonarr_episode(series_id=20, season_number=1, series_title="Show B", episode_id=200),
    ]

    client = AsyncMock()
    client.get_wanted_missing = AsyncMock(return_value=episodes)
    client.get_wanted_cutoff = AsyncMock(return_value=[])
    # First season search raises, second succeeds
    client.search_season = AsyncMock(
        side_effect=[Exception("boom"), None]
    )

    state = _default_state()
    settings = _cycle_settings(missing_count=2, cutoff_count=2)

    result = await run_sonarr_cycle(client, state, settings)

    assert client.search_season.call_count == 2
    # Only the successful search was logged
    assert len(result["search_log"]) == 1
    assert "Show B" in result["search_log"][0]["name"]


async def test_run_sonarr_cycle_cursor_advancement():
    # 4 episodes that deduplicate to 3 seasons
    episodes = [
        _make_sonarr_episode(series_id=10, season_number=1, series_title="Show A", episode_id=100),
        _make_sonarr_episode(series_id=10, season_number=2, series_title="Show A", episode_id=101),
        _make_sonarr_episode(series_id=20, season_number=1, series_title="Show B", episode_id=200),
        _make_sonarr_episode(series_id=10, season_number=1, series_title="Show A", episode_id=102),  # dup
    ]

    settings = _cycle_settings(missing_count=2, cutoff_count=2)

    # --- Run 1: cursor 0 -> 2 ---
    client = AsyncMock()
    client.get_wanted_missing = AsyncMock(return_value=episodes)
    client.get_wanted_cutoff = AsyncMock(return_value=[])
    client.search_season = AsyncMock()

    state = _default_state()
    state["sonarr"]["missing_cursor"] = 0

    result = await run_sonarr_cycle(client, state, settings)
    assert result["sonarr"]["missing_cursor"] == 2

    # --- Run 2: cursor 2 -> wraps to 0 (only 1 season left) ---
    client.get_wanted_missing = AsyncMock(return_value=episodes)
    client.get_wanted_cutoff = AsyncMock(return_value=[])
    client.search_season = AsyncMock()

    result = await run_sonarr_cycle(client, result, settings)
    assert result["sonarr"]["missing_cursor"] == 0
