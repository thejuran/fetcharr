"""Test suite for web UI routes.

Covers dashboard rendering, settings form (masked API keys, TOML write,
key preservation, PRG redirect), htmx partials, and search-now validation.
"""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.testclient import TestClient

from fetcharr.db import init_db, insert_search_entry
from fetcharr.web.routes import STATIC_DIR, router


@pytest.fixture
async def test_app(tmp_path):
    """Build a minimal FastAPI app with mocked state for route testing."""
    app = FastAPI()
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
    app.include_router(router)

    # Initialize SQLite search history database for tests
    db_path = tmp_path / "test.db"
    await init_db(db_path)
    await insert_search_entry(db_path, "Radarr", "missing", "Test Movie")
    app.state.db_path = db_path

    # Mock fetcharr state
    app.state.fetcharr_state = {
        "radarr": {
            "missing_cursor": 3,
            "cutoff_cursor": 1,
            "last_run": "2026-01-15T10:30:00Z",
            "connected": True,
            "unreachable_since": None,
            "missing_count": 42,
            "cutoff_count": 7,
        },
        "sonarr": {
            "missing_cursor": 0,
            "cutoff_cursor": 0,
            "last_run": None,
            "connected": None,
            "unreachable_since": None,
            "missing_count": None,
            "cutoff_count": None,
        },
        "search_log": [],
    }

    # Mock settings with SecretStr-like api_key
    mock_settings = MagicMock()
    mock_settings.radarr.enabled = True
    mock_settings.radarr.url = "http://radarr:7878"
    mock_settings.radarr.api_key.get_secret_value.return_value = "test-radarr-key"
    mock_settings.radarr.search_interval = 30
    mock_settings.radarr.search_missing_count = 5
    mock_settings.radarr.search_cutoff_count = 5
    mock_settings.sonarr.enabled = True
    mock_settings.sonarr.url = "http://sonarr:8989"
    mock_settings.sonarr.api_key.get_secret_value.return_value = "test-sonarr-key"
    mock_settings.sonarr.search_interval = 30
    mock_settings.sonarr.search_missing_count = 5
    mock_settings.sonarr.search_cutoff_count = 5
    mock_settings.general.log_level = "info"
    app.state.settings = mock_settings

    # Mock scheduler
    mock_scheduler = MagicMock()
    mock_job = MagicMock()
    mock_job.next_run_time = None
    mock_scheduler.get_job.return_value = mock_job
    app.state.scheduler = mock_scheduler

    # Mock clients (close() is async, so needs AsyncMock)
    radarr_client = MagicMock()
    radarr_client.close = AsyncMock()
    app.state.radarr_client = radarr_client
    sonarr_client = MagicMock()
    sonarr_client.close = AsyncMock()
    app.state.sonarr_client = sonarr_client

    # Paths
    app.state.config_path = tmp_path / "fetcharr.toml"
    app.state.state_path = tmp_path / "state.json"

    # Search lock (needed by search_now endpoint)
    app.state.search_lock = asyncio.Lock()

    return app


@pytest.fixture
def client(test_app):
    """Create a TestClient for the test app."""
    return TestClient(test_app)


def test_dashboard_returns_200(client):
    """GET / returns 200 and contains app name."""
    response = client.get("/")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    assert "Radarr" in response.text, "Dashboard should display Radarr card"


def test_dashboard_shows_search_log(client):
    """GET / response contains search log entry."""
    response = client.get("/")
    assert response.status_code == 200
    assert "Test Movie" in response.text, "Dashboard should show search log entry"


def test_settings_page_returns_200(client):
    """GET /settings returns 200."""
    response = client.get("/settings")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"


def test_settings_page_does_not_leak_api_keys(client):
    """GET /settings response must NOT contain actual API key values."""
    response = client.get("/settings")
    assert "test-radarr-key" not in response.text, "Radarr API key leaked in settings page"
    assert "test-sonarr-key" not in response.text, "Sonarr API key leaked in settings page"


def test_settings_page_shows_masked_placeholder(client):
    """GET /settings shows ******** placeholder when API key exists."""
    response = client.get("/settings")
    assert "********" in response.text, "Settings should show masked placeholder for existing key"


def test_app_card_partial_returns_200(client):
    """GET /partials/app-card/radarr returns 200."""
    response = client.get("/partials/app-card/radarr")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"


def test_app_card_partial_has_htmx_attributes(client):
    """App card partial contains htmx polling attributes."""
    response = client.get("/partials/app-card/radarr")
    assert "hx-trigger" in response.text, "Card should have hx-trigger attribute"
    assert "every 5s" in response.text, "Card should poll every 5 seconds"


def test_search_log_partial_returns_200(client):
    """GET /partials/search-log returns 200."""
    response = client.get("/partials/search-log")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"


def test_save_settings_writes_toml(client, test_app, tmp_path):
    """POST /settings writes TOML to config_path and redirects (303)."""
    response = client.post(
        "/settings",
        data={
            "log_level": "debug",
            "radarr_url": "http://radarr:7878",
            "radarr_api_key": "new-key",
            "radarr_enabled": "on",
            "radarr_search_interval": "15",
            "radarr_search_missing_count": "10",
            "radarr_search_cutoff_count": "3",
            "sonarr_url": "",
            "sonarr_api_key": "",
            "sonarr_search_interval": "30",
            "sonarr_search_missing_count": "5",
            "sonarr_search_cutoff_count": "5",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303, f"Expected 303 redirect, got {response.status_code}"
    assert response.headers["location"] == "/settings"

    # Verify TOML was written
    config_path = test_app.state.config_path
    assert config_path.exists(), "Config file should have been written"
    content = config_path.read_text()
    assert "radarr" in content, "TOML should contain radarr section"
    assert "new-key" in content, "TOML should contain the new API key"


def test_save_settings_preserves_existing_api_key(client, test_app, tmp_path):
    """POST /settings with empty api_key field preserves the existing key."""
    response = client.post(
        "/settings",
        data={
            "log_level": "info",
            "radarr_url": "http://radarr:7878",
            "radarr_api_key": "",  # Empty = keep existing
            "radarr_enabled": "on",
            "radarr_search_interval": "30",
            "radarr_search_missing_count": "5",
            "radarr_search_cutoff_count": "5",
            "sonarr_url": "http://sonarr:8989",
            "sonarr_api_key": "",  # Empty = keep existing
            "sonarr_enabled": "on",
            "sonarr_search_interval": "30",
            "sonarr_search_missing_count": "5",
            "sonarr_search_cutoff_count": "5",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303

    # Verify the existing keys were preserved in TOML
    content = test_app.state.config_path.read_text()
    assert "test-radarr-key" in content, "Existing radarr key should be preserved"
    assert "test-sonarr-key" in content, "Existing sonarr key should be preserved"


def test_save_settings_replaces_api_key_when_provided(client, test_app, tmp_path):
    """POST /settings with new api_key value writes the new key to TOML."""
    response = client.post(
        "/settings",
        data={
            "log_level": "info",
            "radarr_url": "http://radarr:7878",
            "radarr_api_key": "brand-new-key",  # Explicit new key
            "radarr_enabled": "on",
            "radarr_search_interval": "30",
            "radarr_search_missing_count": "5",
            "radarr_search_cutoff_count": "5",
            "sonarr_url": "http://sonarr:8989",
            "sonarr_api_key": "",
            "sonarr_enabled": "on",
            "sonarr_search_interval": "30",
            "sonarr_search_missing_count": "5",
            "sonarr_search_cutoff_count": "5",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303

    content = test_app.state.config_path.read_text()
    assert "brand-new-key" in content, "New API key should be written to TOML"
    assert "test-radarr-key" not in content, "Old radarr key should be replaced"


def test_search_now_invalid_app(client):
    """POST /api/search-now/invalid returns 400."""
    response = client.post("/api/search-now/invalid")
    assert response.status_code == 400, f"Expected 400, got {response.status_code}"
    assert "Invalid app" in response.text


def test_search_now_happy_path(client, test_app):
    """POST /api/search-now/radarr triggers cycle and returns 200 with updated card."""
    with patch(
        "fetcharr.web.routes.run_radarr_cycle",
        new=AsyncMock(return_value=test_app.state.fetcharr_state),
    ), patch(
        "fetcharr.web.routes.save_state",
    ):
        response = client.post("/api/search-now/radarr")
        assert response.status_code == 200
        assert "Radarr" in response.text  # Card partial contains app name
