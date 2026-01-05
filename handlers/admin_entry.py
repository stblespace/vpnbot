import os
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

ADMIN_IDS = {
    int(x.strip())
    for x in os.getenv("ADMIN_ID", "").split(",")
    if x.strip().isdigit()
}

ADMIN_WEBAPP_URL = os.getenv("ADMIN_WEBAPP_URL", "https://stabelspace.ru/app/admin.html")

router = Router()


def admin_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Открыть админ-панель", web_app=WebAppInfo(url=ADMIN_WEBAPP_URL))]
        ]
    )


@router.message(Command("admin"))
async def admin_entry(message: Message) -> None:
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("Доступ запрещён. Добавьте свой tg_id в ADMIN_ID.")
        return
    await message.answer("Админ-панель:", reply_markup=admin_kb())
