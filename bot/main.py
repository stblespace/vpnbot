"""Бот: оформление подписки и открытие Mini App."""
import asyncio
import logging
from urllib.parse import urlsplit

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode

from bot.config import settings
from bot.handlers import start as start_handlers
from bot.handlers import subscription as subscription_handlers

logger = logging.getLogger(__name__)


def _mask_dsn(dsn: str) -> str:
    parsed = urlsplit(dsn)
    if "@" not in dsn:
        return dsn
    netloc = parsed.netloc
    if "@" in netloc and ":" in netloc.split("@")[0]:
        user_part, host_part = netloc.split("@", 1)
        user = user_part.split(":")[0]
        netloc = f"{user}:***@{host_part}"
    return parsed._replace(netloc=netloc).geturl()


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    logger.info(
        "Старт Telegram бота",
        extra={"database_url": _mask_dsn(settings.database_url), "webapp_url": settings.webapp_url},
    )

    bot = Bot(settings.bot_token, parse_mode=ParseMode.HTML)
    dp = Dispatcher()
    dp.include_router(start_handlers.router)
    dp.include_router(subscription_handlers.router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
