import os, asyncio, logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.fsm.storage.memory import MemoryStorage
from redis.asyncio import Redis
from dotenv import load_dotenv

from handlers.main_menu import router as main_menu_router

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN", "None")
REDIS_HOST=os.getenv("REDIS_HOST", "localhost")
REDIS_PORT=int(os.getenv("REDIS_PORT", 6379))


async def main() -> None:
    logging.basicConfig(level=logging.INFO)

    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    redis = Redis(host=REDIS_HOST, port=REDIS_PORT)
    try:
        await redis.ping()
        storage = RedisStorage(redis=redis)
    except Exception:
        logging.warning("Redis unavailable, falling back to MemoryStorage")
        storage = MemoryStorage()

    dp = Dispatcher(storage=storage)
    dp.include_router(main_menu_router)
    
    
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
