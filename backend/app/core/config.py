"""Application settings — loaded from environment variables / .env file.

Railway injects DATABASE_URL as postgresql://... (no driver prefix).
We auto-transform it to the correct driver prefixes for asyncpg and psycopg2.
"""

from __future__ import annotations

from functools import lru_cache
from typing import List

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Database — Railway provides postgresql://, we transform to the right driver
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/nyc_housing"
    SYNC_DATABASE_URL: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/nyc_housing"

    # Security
    SECRET_KEY: str = "dev-secret-key-change-in-production-minimum-32-chars"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # App
    ENVIRONMENT: str = "development"
    PROJECT_NAME: str = "NYC Housing Simulator"
    API_V1_STR: str = "/api/v1"
    PORT: int = 8000

    # CORS — comma-separated list; add your Vercel URL here in production
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:3001"

    @model_validator(mode="after")
    def transform_database_urls(self) -> "Settings":
        """
        Normalize DATABASE_URL from whatever Railway / Render / Heroku provides.
        These platforms use postgresql:// or postgres:// without driver specifiers.
        """
        raw = self.DATABASE_URL
        if raw.startswith("postgres://"):
            raw = raw.replace("postgres://", "postgresql://", 1)

        # Async URL (asyncpg driver for FastAPI)
        if not raw.startswith("postgresql+asyncpg://"):
            self.DATABASE_URL = raw.replace("postgresql://", "postgresql+asyncpg://", 1)

        # Sync URL (psycopg2 for Alembic migrations)
        base = self.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql+psycopg2://", 1)
        if not self.SYNC_DATABASE_URL or self.SYNC_DATABASE_URL == "postgresql+psycopg2://postgres:postgres@localhost:5432/nyc_housing":
            self.SYNC_DATABASE_URL = base

        return self

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",")]

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
