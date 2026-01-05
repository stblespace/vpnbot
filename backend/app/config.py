"""Настройки приложения, считываются из переменных окружения."""
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator


class Settings(BaseSettings):
    database_url: str
    base_sub_url: str
    bot_token: str
    admin_tg_ids: list[int] = []
    log_level: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @field_validator("admin_tg_ids", mode="before")
    @classmethod
    def parse_admin_ids(cls, value):
        if value is None:
            return []
        if isinstance(value, list):
            return [int(v) for v in value]
        parts = [part.strip() for part in str(value).split(",") if part.strip()]
        return [int(part) for part in parts if part]


settings = Settings()
