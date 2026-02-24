"""SQLite-backed search history persistence.

Replaces the in-memory bounded search_log list with durable storage
on the /config volume.  Uses aiosqlite for async access with a
connection-per-operation pattern (lightweight for local file I/O).
"""

from __future__ import annotations

import contextlib
from datetime import UTC, datetime
from pathlib import Path

import aiosqlite
from loguru import logger

DB_PATH = Path("/config/fetcharr.db")


async def init_db(db_path: Path = DB_PATH) -> None:
    """Create the search_history table and index if they do not exist.

    Args:
        db_path: Path to the SQLite database file.
    """
    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS search_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                app TEXT NOT NULL,
                queue_type TEXT NOT NULL,
                item_name TEXT NOT NULL
            )
            """
        )
        await db.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_search_history_timestamp
            ON search_history(timestamp DESC)
            """
        )
        await db.commit()
    await _migrate_add_outcome_columns(db_path)
    logger.debug("Search history database initialized at {path}", path=db_path)


async def _migrate_add_outcome_columns(db_path: Path) -> None:
    """Add outcome and detail columns to search_history if they do not exist.

    Each ALTER is wrapped in try/except to handle the case where the
    column already exists (SQLite raises "duplicate column name").

    Args:
        db_path: Path to the SQLite database file.
    """
    async with aiosqlite.connect(db_path) as db:
        for col, default in (("outcome", "NULL"), ("detail", "NULL")):
            with contextlib.suppress(Exception):
                await db.execute(
                    f"ALTER TABLE search_history ADD COLUMN {col} TEXT DEFAULT {default}"
                )
        await db.commit()


async def insert_search_entry(
    db_path: Path,
    app: str,
    queue_type: str,
    item_name: str,
    *,
    outcome: str = "searched",
    detail: str = "",
) -> None:
    """Insert a search log entry and prune old rows beyond 500.

    Args:
        db_path: Path to the SQLite database file.
        app: Application name (e.g. "Radarr", "Sonarr").
        queue_type: Queue type (e.g. "missing", "cutoff").
        item_name: Human-readable name of the searched item.
        outcome: Search outcome (e.g. "searched", "failed").
        detail: Additional detail text (e.g. error message).
    """
    timestamp = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            "INSERT INTO search_history (timestamp, app, queue_type, item_name, outcome, detail) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (timestamp, app, queue_type, item_name, outcome, detail),
        )
        await db.execute(
            """
            DELETE FROM search_history
            WHERE id NOT IN (
                SELECT id FROM search_history ORDER BY id DESC LIMIT 500
            )
            """
        )
        await db.commit()


async def get_recent_searches(db_path: Path, limit: int = 50) -> list[dict]:
    """Return the most recent search history entries.

    Args:
        db_path: Path to the SQLite database file.
        limit: Maximum number of entries to return.

    Returns:
        List of dicts with keys: name, timestamp, app, queue_type, outcome, detail.
        Ordered newest-first (by id DESC).
    """
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT timestamp, app, queue_type, item_name, outcome, detail "
            "FROM search_history ORDER BY id DESC LIMIT ?",
            (limit,),
        )
        rows = await cursor.fetchall()
    return [
        {
            "name": row["item_name"],
            "timestamp": row["timestamp"],
            "app": row["app"],
            "queue_type": row["queue_type"],
            "outcome": row["outcome"] or "searched",
            "detail": row["detail"] or "",
        }
        for row in rows
    ]


async def migrate_from_state(db_path: Path, search_log: list[dict]) -> int:
    """Migrate search_log entries from state.json into SQLite.

    Args:
        db_path: Path to the SQLite database file.
        search_log: List of dicts with name, timestamp, app, queue_type keys.

    Returns:
        Number of entries migrated.
    """
    if not search_log:
        return 0

    async with aiosqlite.connect(db_path) as db:
        for entry in search_log:
            await db.execute(
                "INSERT INTO search_history (timestamp, app, queue_type, item_name) VALUES (?, ?, ?, ?)",
                (
                    entry.get("timestamp", ""),
                    entry.get("app", ""),
                    entry.get("queue_type", ""),
                    entry.get("name", ""),
                ),
            )
        await db.commit()

    count = len(search_log)
    logger.info(
        "Migrated {count} search log entries from state.json to SQLite",
        count=count,
    )
    return count
