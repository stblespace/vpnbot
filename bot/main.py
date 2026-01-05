"""Бот: оформление подписки и открытие Mini App."""
import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode

from bot.config import settings
from bot.handlers import start as start_handlers
from bot.handlers import subscription as subscription_handlers


async def main() -> None:
    logging.basicConfig(level=logging.INFO)

    bot = Bot(settings.bot_token, parse_mode=ParseMode.HTML)
    dp = Dispatcher()
    dp.include_router(start_handlers.router)
    dp.include_router(subscription_handlers.router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
