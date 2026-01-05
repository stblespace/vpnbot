"""Обработчики оформления подписки и открытия мини-приложения."""
import logging

from aiogram import Router, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo

from bot.config import settings
from bot.db.session import AsyncSessionLocal
from bot.services.subscription_service import SubscriptionService
from bot.services.user_service import UserService

router = Router()
logger = logging.getLogger(__name__)


def webapp_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Открыть личный кабинет", web_app=WebAppInfo(url=settings.webapp_url))]
        ]
    )


@router.message(lambda m: m.text == "Личный кабинет")
async def open_cabinet(message: types.Message) -> None:
    logger.info("Открытие личного кабинета", extra={"tg_id": message.from_user.id})
    await message.answer("Открываем личный кабинет:", reply_markup=webapp_kb())


@router.message(lambda m: m.text == "Оформить подписку")
async def create_subscription(message: types.Message) -> None:
    async with AsyncSessionLocal() as session:
        user_service = UserService(session)
        sub_service = SubscriptionService(session)

        user = await user_service.get_or_create_user(message.from_user.id)
        subscription = await sub_service.create_or_extend(user, days=30)
        link = sub_service.build_subscription_url(subscription.token)

    await message.answer(
        f"✅ Подписка активирована на 30 дней.\n"
        f"ID: {subscription.id}\n"
        f"Ссылка подписки: {link}\n\n"
        f"Добавь её в приложение или открой личный кабинет.",
        reply_markup=webapp_kb(),
    )

    # TODO: добавить платежную логику и выбор тарифов
