"""Entry point for ``python -m fetcharr``."""

from __future__ import annotations

import asyncio

from loguru import logger


def main() -> None:
    """Run the Fetcharr startup sequence.

    Calls the async startup orchestrator and then logs a placeholder
    message.  The search engine loop will be added in Phase 2.
    """
    from fetcharr.startup import startup

    try:
        asyncio.run(_run())
    except KeyboardInterrupt:
        logger.info("Fetcharr stopped by user")


async def _run() -> None:
    """Async entry point that runs startup and placeholder message."""
    from fetcharr.startup import startup

    await startup()
    logger.info("Fetcharr started. Search engine not yet implemented.")


if __name__ == "__main__":
    main()
