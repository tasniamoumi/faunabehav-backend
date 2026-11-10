"""Application settings, read from environment variables or a .env file."""
from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # "supabase" uses the hosted Postgres; "memory" keeps everything in-process
    # (used by the test suite and for running a demo without any credentials).
    storage: Literal["supabase", "memory"] = "supabase"

    supabase_url: str = ""
    supabase_key: str = ""

    # JWT for dashboard users
    jwt_secret: str = "change-me"
    jwt_algorithm: str = "HS256"
    jwt_expires_minutes: int = 60 * 12

    # Detections below this confidence are never escalated above Low risk.
    min_confidence: float = 0.50

    # Comma-separated origins allowed to call the API from a browser.
    cors_origins: str = "http://localhost:3000,http://localhost:5173"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
