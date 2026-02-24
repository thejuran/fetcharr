"""Core search engine: utility functions and search cycle orchestrators.

Pure functions for filtering, batching, deduplication, and search logging,
plus async cycle functions that compose them with API client calls to
drive the automated search behaviour for Radarr and Sonarr.
"""

from __future__ import annotations

from datetime import datetime, timezone

import httpx
from loguru import logger

from fetcharr.clients.radarr import RadarrClient
from fetcharr.clients.sonarr import SonarrClient
from fetcharr.models.config import Settings
from fetcharr.state import FetcharrState

SEARCH_LOG_MAX = 50


def filter_monitored(items: list[dict]) -> list[dict]:
    """Filter out items where ``monitored`` is not True.

    Works for both Radarr movies and Sonarr episodes.

    Args:
        items: List of item dicts from the *arr API.

    Returns:
        Only items with ``monitored`` set to True.
    """
    return [item for item in items if item.get("monitored", False)]


def slice_batch(items: list, cursor: int, batch_size: int) -> tuple[list, int]:
    """Slice a batch starting at cursor position with wrap-around.

    If cursor is past the end of the list, wraps to 0 silently
    (no log entry for wrap events, per user decision).

    Args:
        items: Full list of items to batch from.
        cursor: Current position in the list.
        batch_size: Maximum number of items to return.

    Returns:
        Tuple of (batch, new_cursor). New cursor wraps to 0
        when it reaches or passes the end of the list.
    """
    if not items:
        return [], 0
    if cursor >= len(items):
        cursor = 0
    batch = items[cursor : cursor + batch_size]
    new_cursor = cursor + len(batch)
    if new_cursor >= len(items):
        new_cursor = 0
    return batch, new_cursor


def append_search_log(
    state: FetcharrState, app: str, queue_type: str, item_name: str
) -> None:
    """Append a search log entry to state, bounded at 50 entries.

    Evicts oldest entries when the log exceeds ``SEARCH_LOG_MAX``.

    Args:
        state: Mutable state dict (modified in place).
        app: Application name (e.g. "Radarr", "Sonarr").
        queue_type: Queue type (e.g. "missing", "cutoff").
        item_name: Human-readable name of the searched item.
    """
    entry = {
        "name": item_name,
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "app": app,
        "queue_type": queue_type,
    }
    state["search_log"].append(entry)
    state["search_log"] = state["search_log"][-SEARCH_LOG_MAX:]


def deduplicate_to_seasons(episodes: list[dict]) -> list[dict]:
    """Deduplicate Sonarr episode records to unique (seriesId, seasonNumber) pairs.

    Order is preserved (first occurrence wins). Returns dicts with
    ``seriesId``, ``seasonNumber``, and ``display_name`` keys.

    Args:
        episodes: List of episode dicts from Sonarr API.

    Returns:
        List of season-level dicts for search commands.
    """
    seen: set[tuple[int, int]] = set()
    seasons: list[dict] = []
    for ep in episodes:
        key = (ep["seriesId"], ep["seasonNumber"])
        if key not in seen:
            seen.add(key)
            title = ep.get("series", {}).get("title", f"Series {ep['seriesId']}")
            seasons.append(
                {
                    "seriesId": ep["seriesId"],
                    "seasonNumber": ep["seasonNumber"],
                    "display_name": f"{title} - Season {ep['seasonNumber']}",
                }
            )
    return seasons


def filter_sonarr_episodes(episodes: list[dict]) -> list[dict]:
    """Filter Sonarr episodes: must be monitored with a past air date.

    Combines monitored filtering AND future/TBA air date filtering.
    Episodes without an air date (TBA) are treated as future and skipped.
    Episodes with unparseable air dates are also skipped.

    Args:
        episodes: List of episode dicts from Sonarr API.

    Returns:
        Only monitored episodes with a past air date.
    """
    now = datetime.now(timezone.utc)
    result: list[dict] = []
    for ep in episodes:
        if not ep.get("monitored", False):
            continue
        air_date_str = ep.get("airDateUtc")
        if air_date_str is None:
            continue
        try:
            air_date = datetime.fromisoformat(air_date_str.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            continue
        if air_date > now:
            continue
        result.append(ep)
    return result


async def run_radarr_cycle(
    client: RadarrClient,
    state: FetcharrState,
    settings: Settings,
) -> FetcharrState:
    """Run one complete Radarr search cycle: missing batch then cutoff batch.

    Fetches the current wanted-missing and wanted-cutoff lists, filters
    to monitored items, slices a batch from each queue using independent
    cursors, triggers ``MoviesSearch`` for each movie, and logs the result.

    Individual search failures are logged and skipped (skip-and-continue).
    If the fetch calls themselves fail (network/HTTP errors), the entire
    cycle aborts and cursors remain unchanged.

    Args:
        client: Connected Radarr API client.
        state: Mutable application state (modified in place).
        settings: Application settings with batch size configuration.

    Returns:
        Updated state with new cursor positions and last_run timestamp.
    """
    try:
        missing = await client.get_wanted_missing()
        cutoff = await client.get_wanted_cutoff()
    except (httpx.HTTPStatusError, httpx.ConnectError, httpx.TimeoutException, httpx.HTTPError) as exc:
        logger.warning("Radarr: Cycle aborted -- {exc}", exc=exc)
        state["radarr"]["connected"] = False
        if not state["radarr"].get("unreachable_since"):
            state["radarr"]["unreachable_since"] = (
                datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            )
        return state

    # Track connection health (WEBU-06)
    state["radarr"]["connected"] = True
    state["radarr"]["unreachable_since"] = None

    # Cache raw item counts before filtering (WEBU-04)
    state["radarr"]["missing_count"] = len(missing)
    state["radarr"]["cutoff_count"] = len(cutoff)

    # --- Missing queue ---
    missing = filter_monitored(missing)
    cursor = state["radarr"]["missing_cursor"]
    batch, new_cursor = slice_batch(missing, cursor, settings.radarr.search_missing_count)
    for movie in batch:
        try:
            await client.search_movies([movie["id"]])
            append_search_log(state, "Radarr", "missing", movie["title"])
            logger.info("Radarr: Searched {title} (missing)", title=movie["title"])
        except Exception as exc:
            logger.warning(
                "Radarr: Failed to search {title}: {exc}",
                title=movie.get("title", "unknown"),
                exc=exc,
            )
    state["radarr"]["missing_cursor"] = new_cursor

    # --- Cutoff queue ---
    cutoff = filter_monitored(cutoff)
    cursor = state["radarr"]["cutoff_cursor"]
    batch, new_cursor = slice_batch(cutoff, cursor, settings.radarr.search_cutoff_count)
    for movie in batch:
        try:
            await client.search_movies([movie["id"]])
            append_search_log(state, "Radarr", "cutoff", movie["title"])
            logger.info("Radarr: Searched {title} (cutoff)", title=movie["title"])
        except Exception as exc:
            logger.warning(
                "Radarr: Failed to search {title}: {exc}",
                title=movie.get("title", "unknown"),
                exc=exc,
            )
    state["radarr"]["cutoff_cursor"] = new_cursor

    # --- Update last_run ---
    state["radarr"]["last_run"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    return state


async def run_sonarr_cycle(
    client: SonarrClient,
    state: FetcharrState,
    settings: Settings,
) -> FetcharrState:
    """Run one complete Sonarr search cycle: missing batch then cutoff batch.

    Fetches the current wanted-missing and wanted-cutoff episode lists,
    filters to monitored episodes with past air dates, deduplicates to
    unique seasons, slices a batch from each queue using independent
    cursors, triggers ``SeasonSearch`` for each season, and logs the result.

    Individual search failures are logged and skipped (skip-and-continue).
    If the fetch calls themselves fail (network/HTTP errors), the entire
    cycle aborts and cursors remain unchanged.

    Args:
        client: Connected Sonarr API client.
        state: Mutable application state (modified in place).
        settings: Application settings with batch size configuration.

    Returns:
        Updated state with new cursor positions and last_run timestamp.
    """
    try:
        missing_episodes = await client.get_wanted_missing()
        cutoff_episodes = await client.get_wanted_cutoff()
    except (httpx.HTTPStatusError, httpx.ConnectError, httpx.TimeoutException, httpx.HTTPError) as exc:
        logger.warning("Sonarr: Cycle aborted -- {exc}", exc=exc)
        state["sonarr"]["connected"] = False
        if not state["sonarr"].get("unreachable_since"):
            state["sonarr"]["unreachable_since"] = (
                datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            )
        return state

    # Track connection health (WEBU-06)
    state["sonarr"]["connected"] = True
    state["sonarr"]["unreachable_since"] = None

    # Cache raw item counts before filtering (WEBU-04)
    state["sonarr"]["missing_count"] = len(missing_episodes)
    state["sonarr"]["cutoff_count"] = len(cutoff_episodes)

    # --- Missing queue ---
    missing_episodes = filter_sonarr_episodes(missing_episodes)
    missing_seasons = deduplicate_to_seasons(missing_episodes)
    cursor = state["sonarr"]["missing_cursor"]
    batch, new_cursor = slice_batch(missing_seasons, cursor, settings.sonarr.search_missing_count)
    for season in batch:
        try:
            await client.search_season(season["seriesId"], season["seasonNumber"])
            append_search_log(state, "Sonarr", "missing", season["display_name"])
            logger.info("Sonarr: Searched {name} (missing)", name=season["display_name"])
        except Exception as exc:
            logger.warning(
                "Sonarr: Failed to search {name}: {exc}",
                name=season.get("display_name", "unknown"),
                exc=exc,
            )
    state["sonarr"]["missing_cursor"] = new_cursor

    # --- Cutoff queue ---
    cutoff_episodes = filter_sonarr_episodes(cutoff_episodes)
    cutoff_seasons = deduplicate_to_seasons(cutoff_episodes)
    cursor = state["sonarr"]["cutoff_cursor"]
    batch, new_cursor = slice_batch(cutoff_seasons, cursor, settings.sonarr.search_cutoff_count)
    for season in batch:
        try:
            await client.search_season(season["seriesId"], season["seasonNumber"])
            append_search_log(state, "Sonarr", "cutoff", season["display_name"])
            logger.info("Sonarr: Searched {name} (cutoff)", name=season["display_name"])
        except Exception as exc:
            logger.warning(
                "Sonarr: Failed to search {name}: {exc}",
                name=season.get("display_name", "unknown"),
                exc=exc,
            )
    state["sonarr"]["cutoff_cursor"] = new_cursor

    # --- Update last_run ---
    state["sonarr"]["last_run"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    return state
