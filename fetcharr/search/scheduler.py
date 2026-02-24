"""APScheduler integration with FastAPI lifespan for automated search cycles.

Creates interval jobs for Radarr and Sonarr search cycles, managed through
FastAPI's lifespan context manager.  State is shared by reference (safe
because AsyncIOScheduler runs jobs on the same event loop) and persisted
to disk after every cycle.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import AsyncIterator

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from loguru import logger

from fetcharr.clients.radarr import RadarrClient
from fetcharr.clients.sonarr import SonarrClient
from fetcharr.models.config import Settings
from fetcharr.search.engine import run_radarr_cycle, run_sonarr_cycle
from fetcharr.state import FetcharrState, load_state, save_state


def create_lifespan(
    settings: Settings, state_path: Path
) -> callable:  # type: ignore[type-arg]
    """Build a FastAPI lifespan context manager wired to APScheduler.

    Creates long-lived API clients for enabled apps, schedules interval
    jobs for each, and ensures clean shutdown of both the scheduler and
    clients on application exit.

    Args:
        settings: Application settings with app configs and intervals.
        state_path: Path to the JSON state file for persistence.

    Returns:
        An async context manager suitable for ``FastAPI(lifespan=...)``.
    """

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        state: FetcharrState = load_state(state_path)
        scheduler = AsyncIOScheduler()

        radarr_client: RadarrClient | None = None
        sonarr_client: SonarrClient | None = None

        # --- Create long-lived clients for enabled apps ---
        if settings.radarr.enabled:
            radarr_client = RadarrClient(
                base_url=settings.radarr.url,
                api_key=settings.radarr.api_key.get_secret_value(),
            )

        if settings.sonarr.enabled:
            sonarr_client = SonarrClient(
                base_url=settings.sonarr.url,
                api_key=settings.sonarr.api_key.get_secret_value(),
            )

        # --- Define wrapper functions that capture state by reference ---
        async def radarr_job() -> None:
            nonlocal state
            try:
                state = await run_radarr_cycle(radarr_client, state, settings)  # type: ignore[arg-type]
                save_state(state, state_path)
            except Exception as exc:
                logger.error("Radarr: Unhandled error in search cycle -- {exc}", exc=exc)

        async def sonarr_job() -> None:
            nonlocal state
            try:
                state = await run_sonarr_cycle(sonarr_client, state, settings)  # type: ignore[arg-type]
                save_state(state, state_path)
            except Exception as exc:
                logger.error("Sonarr: Unhandled error in search cycle -- {exc}", exc=exc)

        # --- Schedule jobs only for enabled apps ---
        if settings.radarr.enabled:
            scheduler.add_job(
                radarr_job,
                "interval",
                minutes=settings.radarr.search_interval,
                id="radarr_search",
                next_run_time=datetime.now(timezone.utc),
            )
            logger.info(
                "Scheduled Radarr search every {interval}m (first run: now)",
                interval=settings.radarr.search_interval,
            )

        if settings.sonarr.enabled:
            scheduler.add_job(
                sonarr_job,
                "interval",
                minutes=settings.sonarr.search_interval,
                id="sonarr_search",
                next_run_time=datetime.now(timezone.utc),
            )
            logger.info(
                "Scheduled Sonarr search every {interval}m (first run: now)",
                interval=settings.sonarr.search_interval,
            )

        scheduler.start()

        try:
            yield
        finally:
            scheduler.shutdown(wait=False)

            if radarr_client is not None:
                await radarr_client.close()
            if sonarr_client is not None:
                await sonarr_client.close()

            logger.info("Search engine stopped")

    return lifespan
