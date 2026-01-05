"""Клавиатуры основного меню."""
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def main_menu_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Оформить подписку")],
            [KeyboardButton(text="Личный кабинет")],
        ],
        resize_keyboard=True,
    )
