"""Команда /start и главное меню."""
from aiogram import Router, types
from aiogram.filters import CommandStart

from bot.keyboards import main_menu_kb


router = Router()

WELCOME_TEXT = (
    "Привет! Это бот управления VPN подпиской.\n"
    "Можешь оформить подписку или открыть личный кабинет."
)


@router.message(CommandStart())
async def cmd_start(message: types.Message) -> None:
    await message.answer(WELCOME_TEXT, reply_markup=main_menu_kb())
