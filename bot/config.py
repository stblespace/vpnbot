"""Настройки бота."""
import os

from dotenv import load_dotenv


load_dotenv()


BOT_TOKEN = os.getenv("BOT_TOKEN", "")
WEBAPP_URL = "https://stabelspace.ru/app"

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN не задан в окружении")
