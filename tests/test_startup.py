"""Tests for startup localhost URL detection."""

from __future__ import annotations

import io

from loguru import logger

from fetcharr.models.config import ArrConfig, Settings
from fetcharr.startup import check_localhost_urls, collect_secrets


def _make_settings(
    radarr_url: str = "http://radarr:7878",
    radarr_enabled: bool = True,
    sonarr_url: str = "http://sonarr:8989",
    sonarr_enabled: bool = True,
) -> Settings:
    """Build a Settings instance with the given app URLs and enabled flags."""
    return Settings(
        radarr=ArrConfig(
            url=radarr_url,
            api_key="test-key",
            enabled=radarr_enabled,
        ),
        sonarr=ArrConfig(
            url=sonarr_url,
            api_key="test-key",
            enabled=sonarr_enabled,
        ),
    )


def test_localhost_url_logs_warning() -> None:
    """Enabled app with localhost URL triggers a warning."""
    settings = _make_settings(radarr_url="http://localhost:7878")

    sink = io.StringIO()
    handler_id = logger.add(sink, format="{message}", level="WARNING")
    try:
        check_localhost_urls(settings)
    finally:
        logger.remove(handler_id)

    output = sink.getvalue()
    assert "Radarr" in output
    assert "localhost" in output
    assert "host.docker.internal" in output


def test_127_0_0_1_url_logs_warning() -> None:
    """Enabled app with 127.0.0.1 URL triggers a warning."""
    settings = _make_settings(sonarr_url="http://127.0.0.1:8989")

    sink = io.StringIO()
    handler_id = logger.add(sink, format="{message}", level="WARNING")
    try:
        check_localhost_urls(settings)
    finally:
        logger.remove(handler_id)

    output = sink.getvalue()
    assert "Sonarr" in output
    assert "127.0.0.1" in output


def test_ipv6_loopback_url_logs_warning() -> None:
    """Enabled app with ::1 (IPv6 loopback) URL triggers a warning."""
    settings = _make_settings(radarr_url="http://[::1]:7878")

    sink = io.StringIO()
    handler_id = logger.add(sink, format="{message}", level="WARNING")
    try:
        check_localhost_urls(settings)
    finally:
        logger.remove(handler_id)

    output = sink.getvalue()
    assert "Radarr" in output


def test_non_localhost_url_no_warning() -> None:
    """Normal service-name URLs produce no warning."""
    settings = _make_settings(
        radarr_url="http://radarr:7878",
        sonarr_url="http://sonarr:8989",
    )

    sink = io.StringIO()
    handler_id = logger.add(sink, format="{message}", level="WARNING")
    try:
        check_localhost_urls(settings)
    finally:
        logger.remove(handler_id)

    output = sink.getvalue()
    assert output == ""


def test_disabled_app_with_localhost_no_warning() -> None:
    """Disabled app with localhost URL produces no warning (skipped)."""
    # Radarr disabled with localhost -- should be skipped.
    # Sonarr enabled with non-localhost -- satisfies validator, no warning.
    settings = _make_settings(
        radarr_url="http://localhost:7878",
        radarr_enabled=False,
        sonarr_url="http://sonarr:8989",
        sonarr_enabled=True,
    )

    sink = io.StringIO()
    handler_id = logger.add(sink, format="{message}", level="WARNING")
    try:
        check_localhost_urls(settings)
    finally:
        logger.remove(handler_id)

    output = sink.getvalue()
    assert output == ""


# ---------------------------------------------------------------------------
# collect_secrets
# ---------------------------------------------------------------------------


def test_collect_secrets_extracts_all_api_keys() -> None:
    """collect_secrets returns non-empty API key values from all configured apps."""
    settings = Settings(
        radarr=ArrConfig(
            url="http://radarr:7878",
            api_key="radarr-secret",
            enabled=True,
        ),
        sonarr=ArrConfig(
            url="http://sonarr:8989",
            api_key="sonarr-secret",
            enabled=True,
        ),
    )
    result = collect_secrets(settings)
    assert "radarr-secret" in result
    assert "sonarr-secret" in result
    assert len(result) == 2
