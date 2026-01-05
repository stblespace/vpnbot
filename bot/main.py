"""Минимальный aiogram 3.x бот — только вход в WebApp."""
import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode

from bot.config import BOT_TOKEN
from bot.handlers import router


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    bot = Bot(BOT_TOKEN, parse_mode=ParseMode.HTML)
    dp = Dispatcher()
    dp.include_router(router)

    # Запуск бота долгоживущим пуллингом
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
