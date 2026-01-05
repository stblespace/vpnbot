"""Клавиатуры: главное меню и кнопка открытия WebApp."""
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    WebAppInfo,
)

from bot.config import WEBAPP_URL


def main_menu_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Личный кабинет")],
            [KeyboardButton(text="Помощь")],
        ],
        resize_keyboard=True,
    )


def webapp_kb() -> InlineKeyboardMarkup:
    # Кнопка открывает Telegram Mini App (WebApp) по заданному URL
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Открыть кабинет", web_app=WebAppInfo(url=WEBAPP_URL))]
        ]
    )
