"""Pydantic models for Fetcharr TOML configuration."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, SecretStr, model_validator
from pydantic_settings import BaseSettings, PydanticBaseSettingsSource, TomlConfigSettingsSource

CONFIG_PATH = Path("/config/fetcharr.toml")


class ArrConfig(BaseModel):
    """Connection configuration for a single *arr application."""

    url: str = ""
    api_key: SecretStr = SecretStr("")
    enabled: bool = False

    # Search tuning (sensible defaults -- override in config to customize)
    search_interval: int = 30  # Minutes between search cycles
    search_missing_count: int = 5  # Missing items to search per cycle
    search_cutoff_count: int = 5  # Cutoff items to search per cycle


class GeneralConfig(BaseModel):
    """Global application settings."""

    log_level: str = "info"


class Settings(BaseSettings):
    """Application settings loaded from TOML config file.

    Sections: [general], [radarr], [sonarr].
    At least one app must be configured with a URL and enabled.
    """

    model_config = {
        "toml_file": CONFIG_PATH,
    }

    general: GeneralConfig = GeneralConfig()
    radarr: ArrConfig = ArrConfig()
    sonarr: ArrConfig = ArrConfig()

    @model_validator(mode="after")
    def at_least_one_app_configured(self) -> Settings:
        """Validate that at least one app is enabled with a non-empty URL."""
        radarr_ok = self.radarr.enabled and self.radarr.url.strip()
        sonarr_ok = self.sonarr.enabled and self.sonarr.url.strip()
        if not radarr_ok and not sonarr_ok:
            raise ValueError(
                "At least one app (radarr or sonarr) must be configured "
                "with a URL and enabled"
            )
        return self

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (
            init_settings,
            TomlConfigSettingsSource(settings_cls),
        )
