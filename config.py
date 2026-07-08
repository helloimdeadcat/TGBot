from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    telegram_bot_token: str
    telegram_chat_id: str
    search_keywords: list[str] = Field(default_factory=lambda: ["python", "developer"])
    search_location: str | None = None
    daily_digest_hour: int = 9
    daily_digest_minute: int = 0
    enabled_sources: list[str] = Field(
        default_factory=lambda: ["arbeitsagentur", "indeed", "stepstone"]
    )
    database_path: Path = Path("data/vacancies.db")
    timezone: str = "Europe/Berlin"
    request_delay_seconds: float = 1.5
    max_results_per_source: int = 50

    @field_validator("search_keywords", "enabled_sources", mode="before")
    @classmethod
    def parse_comma_separated(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
