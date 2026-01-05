"""Конфигурация бота и подключение к внешним сервисам."""
import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


@dataclass(slots=True)
class Settings:
    bot_token: str
    database_url: str
    base_sub_url: str
    webapp_url: str


def get_settings() -> Settings:
    bot_token = os.getenv("BOT_TOKEN", "")
    if not bot_token:
        raise RuntimeError("BOT_TOKEN не задан")

    database_url = os.getenv("DATABASE_URL", "")
    if not database_url:
        raise RuntimeError("DATABASE_URL не задан")

    base_sub_url = os.getenv("BASE_SUB_URL", "https://stabelspace.ru/sub")
    webapp_url = os.getenv("WEBAPP_URL", "https://stabelspace.ru/app")

    return Settings(
        bot_token=bot_token,
        database_url=database_url,
        base_sub_url=base_sub_url.rstrip("/"),
        webapp_url=webapp_url,
    )


settings = get_settings()
