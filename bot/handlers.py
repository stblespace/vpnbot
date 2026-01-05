"""Обработчики команд и кнопок."""
from aiogram import Router, types
from aiogram.filters import CommandStart

from bot.keyboards import main_menu_kb, webapp_kb

router = Router()

WELCOME_TEXT = (
    "Привет! Это бот-запускатель VPN кабинета.\n"
    "Нажмите «Личный кабинет», чтобы открыть Mini App."
)

HELP_TEXT = "Если что-то не работает — попробуйте обновить приложение или написать в поддержку."


@router.message(CommandStart())
async def cmd_start(message: types.Message) -> None:
    await message.answer(WELCOME_TEXT, reply_markup=main_menu_kb())


@router.message(lambda m: m.text == "Личный кабинет")
async def open_webapp(message: types.Message) -> None:
    await message.answer("Открываем личный кабинет:", reply_markup=webapp_kb())


@router.message(lambda m: m.text == "Помощь")
async def help_message(message: types.Message) -> None:
    await message.answer(HELP_TEXT, reply_markup=main_menu_kb())
