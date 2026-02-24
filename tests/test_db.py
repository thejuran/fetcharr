"""Tests for SQLite search history persistence module.

Covers: database init, insert/retrieve, limit, pruning,
migration from state.json, empty state, and empty database.
"""

from __future__ import annotations

import aiosqlite

from fetcharr.db import get_recent_searches, init_db, insert_search_entry, migrate_from_state


async def test_init_db_creates_table(tmp_path):
    """init_db creates the search_history table and index."""
    db_path = tmp_path / "test.db"
    await init_db(db_path)

    async with aiosqlite.connect(db_path) as db:
        cursor = await db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='search_history'"
        )
        row = await cursor.fetchone()
    assert row is not None
    assert row[0] == "search_history"


async def test_insert_and_retrieve(tmp_path):
    """Inserted entries are retrieved in newest-first order with correct keys."""
    db_path = tmp_path / "test.db"
    await init_db(db_path)

    await insert_search_entry(db_path, "Radarr", "missing", "Movie A")
    await insert_search_entry(db_path, "Sonarr", "cutoff", "Show B")
    await insert_search_entry(db_path, "Radarr", "missing", "Movie C")

    results = await get_recent_searches(db_path)
    assert len(results) == 3
    # Newest first (by id DESC)
    assert results[0]["name"] == "Movie C"
    assert results[1]["name"] == "Show B"
    assert results[2]["name"] == "Movie A"

    # Verify all expected keys present
    for entry in results:
        assert "name" in entry
        assert "timestamp" in entry
        assert "app" in entry
        assert "queue_type" in entry


async def test_get_recent_searches_limit(tmp_path):
    """get_recent_searches respects the limit parameter."""
    db_path = tmp_path / "test.db"
    await init_db(db_path)

    for i in range(10):
        await insert_search_entry(db_path, "Radarr", "missing", f"Movie {i}")

    results = await get_recent_searches(db_path, limit=3)
    assert len(results) == 3
    # Should be the 3 most recent
    assert results[0]["name"] == "Movie 9"
    assert results[1]["name"] == "Movie 8"
    assert results[2]["name"] == "Movie 7"


async def test_insert_prunes_old_entries(tmp_path):
    """Inserting beyond 500 entries prunes the oldest rows."""
    db_path = tmp_path / "test.db"
    await init_db(db_path)

    for i in range(510):
        await insert_search_entry(db_path, "Radarr", "missing", f"Movie {i}")

    async with aiosqlite.connect(db_path) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM search_history")
        row = await cursor.fetchone()
    assert row[0] == 500


async def test_migrate_from_state(tmp_path):
    """migrate_from_state inserts entries from state.json format into SQLite."""
    db_path = tmp_path / "test.db"
    await init_db(db_path)

    search_log = [
        {"name": "Movie A", "timestamp": "2026-01-15T10:30:00Z", "app": "Radarr", "queue_type": "missing"},
        {"name": "Show B", "timestamp": "2026-01-15T10:31:00Z", "app": "Sonarr", "queue_type": "cutoff"},
    ]

    count = await migrate_from_state(db_path, search_log)
    assert count == 2

    results = await get_recent_searches(db_path)
    assert len(results) == 2
    names = {r["name"] for r in results}
    assert names == {"Movie A", "Show B"}


async def test_migrate_empty_log(tmp_path):
    """migrate_from_state with empty list returns 0 and inserts nothing."""
    db_path = tmp_path / "test.db"
    await init_db(db_path)

    count = await migrate_from_state(db_path, [])
    assert count == 0

    results = await get_recent_searches(db_path)
    assert results == []


async def test_get_recent_searches_empty_db(tmp_path):
    """get_recent_searches on empty database returns empty list."""
    db_path = tmp_path / "test.db"
    await init_db(db_path)

    results = await get_recent_searches(db_path)
    assert results == []
