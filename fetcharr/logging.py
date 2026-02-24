"""Loguru logging setup with API key redaction filter."""

from __future__ import annotations

import sys
from collections.abc import Callable

from loguru import logger


def create_redaction_filter(secrets: list[str]) -> Callable:
    """Create a loguru filter that redacts secret values from log messages.

    Returns a filter function that replaces any occurrence of a secret
    string in ``record["message"]`` with ``[REDACTED]``. Empty strings
    in the secrets list are skipped.

    Args:
        secrets: List of secret values to redact from log output.

    Returns:
        A loguru-compatible filter function.
    """

    def redact(record: dict) -> bool:
        for secret in secrets:
            if secret and secret in record["message"]:
                record["message"] = record["message"].replace(
                    secret, "[REDACTED]"
                )
        return True

    return redact


def setup_logging(level: str, secrets: list[str]) -> None:
    """Configure loguru with human-readable format and secret redaction.

    Removes the default handler and adds a new stderr handler with:
    - Format: ``2026-02-23 14:30:00 INFO     Connected to Radarr``
    - Configurable log level
    - Automatic redaction of all secret values

    Args:
        level: Log level string (e.g. "info", "debug", "warning").
        secrets: List of secret values to redact from all log output.
    """
    logger.remove()
    logger.add(
        sys.stderr,
        format="{time:YYYY-MM-DD HH:mm:ss} {level:<8} {message}",
        level=level.upper(),
        filter=create_redaction_filter(secrets),
        colorize=True,
    )
