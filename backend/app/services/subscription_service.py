"""Бизнес-логика подписки и выдачи конфигов."""
import logging
from datetime import datetime, timezone
from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Server, Subscription, User
from app.services.config_generator import ConfigGenerator

logger = logging.getLogger(__name__)


class SubscriptionUnavailable(Exception):
    """Подписка недоступна или неверный токен."""


class NoActiveServers(Exception):
    """Нет доступных серверов для генерации конфигов."""


class SubscriptionService:
    def __init__(self, session: AsyncSession, config_generator: ConfigGenerator | None = None) -> None:
        self.session = session
        self.config_generator = config_generator or ConfigGenerator()

    async def _get_active_subscription(self, token: str) -> Subscription:
        stmt = (
            select(Subscription)
            .options(selectinload(Subscription.user))
            .where(Subscription.token == token)
        )
        result = await self.session.execute(stmt)
        subscription: Subscription | None = result.scalar_one_or_none()
        now = datetime.now(timezone.utc)

        if (
            not subscription
            or not subscription.is_active
            or subscription.is_expired(now)
            or not subscription.user
            or not subscription.user.is_active
        ):
            logger.warning(
                "Подписка недоступна или истекла",
                extra={"token_prefix": token[:6], "subscription_id": getattr(subscription, "id", None)},
            )
            raise SubscriptionUnavailable("Подписка недоступна или устарела")
        return subscription

    async def _get_enabled_servers(self) -> List[Server]:
        stmt = select(Server).where(Server.enabled.is_(True))
        result = await self.session.execute(stmt)
        servers = list(result.scalars().all())
        if not servers:
            raise NoActiveServers("Нет активных серверов")
        return servers

    async def build_subscription_payload(self, token: str) -> str:
        """Вернуть готовый текст подписки (plain text)."""
        subscription = await self._get_active_subscription(token)
        servers = await self._get_enabled_servers()
        logger.info(
            "Генерация payload подписки",
            extra={
                "subscription_id": subscription.id,
                "user_id": subscription.user_id,
                "servers_count": len(servers),
            },
        )
        links = [
            self.config_generator.build_vless_uri(server, str(subscription.user.uuid))
            for server in servers
        ]
        return "\n".join(links)

    async def get_latest_subscription_for_user(self, user_id: int) -> Subscription | None:
        """Вернуть последнюю подписку пользователя (даже если истекла)."""
        stmt = (
            select(Subscription)
            .where(Subscription.user_id == user_id)
            .order_by(Subscription.expires_at.desc())
        )
        result = await self.session.execute(stmt)
        sub = result.scalars().first()
        logger.info(
            "Получена последняя подписка пользователя",
            extra={"user_id": user_id, "subscription_id": getattr(sub, 'id', None)},
        )
        return sub
