"""Tests for client structure, header auth, timeout, and subclass hierarchy."""

from __future__ import annotations

from fetcharr.clients.base import ArrClient
from fetcharr.clients.radarr import RadarrClient
from fetcharr.clients.sonarr import SonarrClient


def test_arr_client_sets_api_key_header() -> None:
    """ArrClient sets X-Api-Key in httpx client headers."""
    client = ArrClient(base_url="http://localhost:7878", api_key="test-key-123")
    assert client._client.headers["X-Api-Key"] == "test-key-123"


def test_arr_client_sets_timeout() -> None:
    """ArrClient respects custom timeout parameter."""
    client = ArrClient(base_url="http://localhost:7878", api_key="key", timeout=30)
    # httpx.Timeout stores timeout as a Timeout object; check the connect/read values
    assert client._client.timeout.connect == 30
    assert client._client.timeout.read == 30


def test_arr_client_sets_content_type() -> None:
    """ArrClient sets Content-Type: application/json in default headers."""
    client = ArrClient(base_url="http://localhost:7878", api_key="key")
    assert client._client.headers["Content-Type"] == "application/json"


def test_radarr_client_is_arr_client_subclass() -> None:
    """RadarrClient is a subclass of ArrClient."""
    assert issubclass(RadarrClient, ArrClient)


def test_sonarr_client_is_arr_client_subclass() -> None:
    """SonarrClient is a subclass of ArrClient."""
    assert issubclass(SonarrClient, ArrClient)


def test_radarr_client_app_name() -> None:
    """RadarrClient sets _app_name to 'Radarr'."""
    client = RadarrClient(base_url="http://localhost:7878", api_key="key")
    assert client._app_name == "Radarr"


def test_sonarr_client_app_name() -> None:
    """SonarrClient sets _app_name to 'Sonarr'."""
    client = SonarrClient(base_url="http://localhost:8989", api_key="key")
    assert client._app_name == "Sonarr"


def test_api_key_not_in_url() -> None:
    """API key is in headers only, not in the base URL."""
    api_key = "super-secret-key"
    client = ArrClient(base_url="http://localhost:7878", api_key=api_key)
    assert api_key not in str(client._client.base_url)
    assert client._client.headers["X-Api-Key"] == api_key
