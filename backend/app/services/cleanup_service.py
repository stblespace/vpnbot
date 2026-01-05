"""Фоновая деактивация истекших подписок.

Запускается раз в сутки и помечает истекшие подписки как неактивные.
Если деплой не предполагает фоновые таски, можно вынести в cron/management команду (TODO).
"""
import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy import update

from app.db import AsyncSessionLocal
from app.models import Subscription

logger = logging.getLogger(__name__)


async def deactivate_expired_subscriptions() -> None:
    """Однократно деактивировать все истекшие подписки."""
    now = datetime.now(timezone.utc)
    async with AsyncSessionLocal() as session:
        stmt = (
            update(Subscription)
            .where(Subscription.expires_at < now)
            .where(Subscription.is_active.is_(True))
            .values(is_active=False)
        )
        result = await session.execute(stmt)
        await session.commit()
        affected = result.rowcount or 0
    if affected:
        logger.info("Деактивированы истекшие подписки", extra={"count": affected})
    else:
        logger.info("Истекших подписок не найдено")


async def expired_subscriptions_loop(interval_hours: int = 24) -> None:
    """Периодически запускает деактивацию. Останавливается при отмене таски."""
    while True:
        try:
            await deactivate_expired_subscriptions()
        except Exception as exc:  # не даем задаче упасть навсегда
            logger.exception("Ошибка деактивации подписок", exc_info=exc)
        await asyncio.sleep(interval_hours * 3600)
