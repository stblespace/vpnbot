"""Настройки приложения, считываются из переменных окружения."""
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator


class Settings(BaseSettings):
    database_url: str
    base_sub_url: str
    bot_token: str
    admin_tg_ids: list[int] = []
    log_level: str = "INFO"
    xui_base_url: str = "http://localhost:54321"
    xui_username: str = "admin"
    xui_password: str = "admin"
    xui_request_timeout: int = 15
    xui_reality_public_key: str | None = None
    xui_reality_fingerprint: str = "chrome"
    xui_reality_short_id: str | None = None
    xui_reality_spider_x: str = "/"

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
