"""Фоновая деактивация истекших подписок.

Запускается раз в сутки и помечает истекшие подписки как неактивные.
Если деплой не предполагает фоновые таски, можно вынести в cron/management команду (TODO).
"""
import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy import select, update

from app.db import AsyncSessionLocal
from app.models import Subscription, User
from app.services.xui_client import XUIClient
from app.services.xui_sync import ensure_user_disabled

logger = logging.getLogger(__name__)


async def deactivate_expired_subscriptions() -> None:
    """Однократно деактивировать все истекшие подписки."""
    now = datetime.now(timezone.utc)
    async with AsyncSessionLocal() as session:
        select_stmt = (
            select(Subscription.id, Subscription.user_id, User.uuid)
            .join(User, User.id == Subscription.user_id)
            .where(Subscription.expires_at < now)
            .where(Subscription.is_active.is_(True))
        )
        expired = list((await session.execute(select_stmt)).all())
        expired_ids = [row.id for row in expired]

        if not expired_ids:
            logger.info("Истекших подписок не найдено")
            return

        update_stmt = update(Subscription).where(Subscription.id.in_(expired_ids)).values(is_active=False)
        await session.execute(update_stmt)
        await session.commit()
        logger.info("Деактивированы истекшие подписки", extra={"count": len(expired_ids)})

        client = XUIClient()
        try:
            for row in expired:
                user_uuid = getattr(row, "uuid", None)
                if not user_uuid:
                    continue
                try:
                    await ensure_user_disabled(
                        session,
                        str(user_uuid),
                        include_disabled_servers=True,
                        xui_client=client,
                    )
                except Exception as exc:
                    logger.exception(
                        "Не удалось отключить клиента в 3X-UI",
                        exc_info=exc,
                        extra={"subscription_id": row.id, "user_id": row.user_id},
                    )
        finally:
            await client.close()


async def expired_subscriptions_loop(interval_hours: int = 24) -> None:
    """Периодически запускает деактивацию. Останавливается при отмене таски."""
    while True:
        try:
            await deactivate_expired_subscriptions()
        except Exception as exc:  # не даем задаче упасть навсегда
            logger.exception("Ошибка деактивации подписок", exc_info=exc)
        await asyncio.sleep(interval_hours * 3600)
