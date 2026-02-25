"""
LancasterLink Backend – Application Configuration.

Centralises all settings (DB connection, Redis, API keys, tunables) using
pydantic-settings so values are loaded from environment variables with
sensible defaults for local development.

Environment variables are set per-service in docker-compose.yml.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application-wide configuration.

    Values are read from environment variables (case-insensitive).
    Defaults match the docker-compose dev environment so the app can
    start without an .env file.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── Database (PostgreSQL + PostGIS) ──────────────────────────────────
    database_url: str = (
        "postgresql+psycopg2://lancasterlink:lancasterlink"
        "@localhost:5432/lancasterlink"
    )

    # ── Redis ────────────────────────────────────────────────────────────
    redis_url: str = "redis://localhost:6379/0"

    # ── External API keys ────────────────────────────────────────────────
    bods_api_key: str = ""              # Bus Open Data Service
    network_rail_user: str = ""         # Network Rail STOMP feed
    network_rail_pass: str = ""

    # ── Polling / TTLs ───────────────────────────────────────────────────
    polling_interval_seconds: int = 30          # DR-03
    stale_data_ttl_seconds: int = 300           # NFR-RA-02: 5 minutes

    # ── Application ──────────────────────────────────────────────────────
    log_level: str = "info"
    cors_origins: list[str] = ["*"]             # Tighten for production
    app_title: str = "LancasterLink API"
    app_version: str = "0.1.0"


@lru_cache
def get_settings() -> Settings:
    """Return a cached singleton of the application settings."""
    return Settings()
