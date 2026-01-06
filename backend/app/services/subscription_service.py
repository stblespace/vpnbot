"""Бизнес-логика подписки и выдачи конфигов."""
import logging
from datetime import datetime, timezone
from typing import List

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Server, Subscription, User
from app.services.config_generator import ConfigGenerator
from app.config import settings

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

        if not self._is_active_subscription(subscription, now):
            logger.warning(
                "Подписка недоступна или истекла",
                extra={"token_prefix": token[:6], "subscription_id": getattr(subscription, "id", None)},
            )
            raise SubscriptionUnavailable("Подписка недоступна или устарела")
        return subscription

    @staticmethod
    def _is_active_subscription(subscription: Subscription | None, now: datetime) -> bool:
        """Единственный критерий допуска к выдаче конфигурации."""
        if not subscription or not subscription.user:
            return False
        if not subscription.user.is_active:
            return False
        if subscription.is_expired(now):
            return False
        if not subscription.is_active:
            return False
        return True

    async def _get_enabled_servers(self) -> List[Server]:
        stmt = select(Server).where(Server.enabled.is_(True))
        result = await self.session.execute(stmt)
        servers = list(result.scalars().all())
        if not servers:
            logger.error("Нет активных серверов для генерации конфигурации")
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

    async def _get_enabled_servers_count(self) -> int:
        stmt = select(func.count(Server.id)).where(Server.enabled.is_(True))
        result = await self.session.execute(stmt)
        return int(result.scalar_one() or 0)

    def _render_status(self, subscription: Subscription | None, now: datetime) -> str:
        if not subscription:
            return "none"
        if not subscription.user or not subscription.user.is_active:
            return "blocked"
        if not subscription.is_active:
            return "blocked"
        if subscription.is_expired(now):
            return "expired"
        return "active"

    async def get_subscription_summary_for_user(self, user: User | None) -> dict:
        """Каноничный ответ о подписке для Mini App/бота."""
        servers_count = await self._get_enabled_servers_count()
        now = datetime.now(timezone.utc)
        if not user:
            return {
                "status": "none",
                "subscription_id": None,
                "expires_at": None,
                "expires_in_days": None,
                "sub_url": None,
                "servers_count": servers_count,
            }

        subscription = await self.get_latest_subscription_for_user(user.id)
        status = self._render_status(subscription, now)

        expires_in_days = None
        expires_at_iso = None
        sub_url = None
        if subscription and subscription.expires_at:
            delta = subscription.expires_at - now
            expires_in_days = max(0, int(delta.total_seconds() // 86400))
            expires_at_iso = subscription.expires_at.isoformat()
            sub_url = f"{settings.base_sub_url.rstrip('/')}/{subscription.token}"

        return {
            "status": status,
            "subscription_id": getattr(subscription, "id", None),
            "expires_at": expires_at_iso,
            "expires_in_days": expires_in_days,
            "sub_url": sub_url if status != "none" else None,
            "servers_count": servers_count,
        }

    async def get_subscription_summary_by_tg_id(self, tg_id: int) -> dict:
        """Каноничный ответ по Telegram ID (для бота)."""
        stmt = (
            select(User)
            .where(User.tg_id == tg_id)
            .options(selectinload(User.subscriptions))
        )
        result = await self.session.execute(stmt)
        user = result.scalar_one_or_none()
        return await self.get_subscription_summary_for_user(user)
