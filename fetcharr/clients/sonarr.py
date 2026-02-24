"""Sonarr async API client."""

from __future__ import annotations

from typing import Any

from fetcharr.clients.base import ArrClient


class SonarrClient(ArrClient):
    """HTTP client for Sonarr API.

    Thin wrapper around ArrClient that defines Sonarr-specific
    endpoint paths for wanted/missing and wanted/cutoff episode lists.
    Always includes ``includeSeries=true`` for human-readable log
    messages and season-level deduplication in the search engine.
    """

    def __init__(self, base_url: str, api_key: str, timeout: float = 30.0) -> None:
        super().__init__(base_url, api_key, timeout)
        self._app_name = "Sonarr"

    async def get_wanted_missing(self) -> list[dict[str, Any]]:
        """Fetch all wanted/missing episodes from Sonarr.

        Includes series data (``includeSeries=true``) for human-readable
        log messages and season-level deduplication.
        """
        return await self.get_paginated(
            "/api/v3/wanted/missing",
            extra_params={"includeSeries": "true"},
        )

    async def get_wanted_cutoff(self) -> list[dict[str, Any]]:
        """Fetch all episodes that don't meet their quality cutoff.

        Includes series data (``includeSeries=true``) for human-readable
        log messages and season-level deduplication.
        """
        return await self.get_paginated(
            "/api/v3/wanted/cutoff",
            extra_params={"includeSeries": "true"},
        )
