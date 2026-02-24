"""Core search engine utility functions.

Pure functions for filtering, batching, deduplication, and search logging
shared by both Radarr and Sonarr search cycles.
"""

from __future__ import annotations

from datetime import datetime, timezone

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
