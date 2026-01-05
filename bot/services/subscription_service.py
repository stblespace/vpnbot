"""Создание и продление подписок через бота."""
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import Boolean, DateTime, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from bot.config import settings
from bot.db.session import Base
from bot.services.token_generator import generate_token
from bot.services.user_service import User

logger = logging.getLogger(__name__)


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(index=True)
    token: Mapped[str] = mapped_column(unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class SubscriptionService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_latest_by_user(self, user_id: int) -> Optional[Subscription]:
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

    async def create_or_extend(self, user: User, days: int = 30) -> Subscription:
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(days=days)

        existing = await self.get_latest_by_user(user.id)
        if existing:
            existing.expires_at = expires_at
            existing.is_active = True
            subscription = existing
            logger.info(
                "Продление подписки",
                extra={"subscription_id": subscription.id, "user_id": user.id, "expires_at": expires_at.isoformat()},
            )
        else:
            subscription = Subscription(
                user_id=user.id,
                token=generate_token(32),
                expires_at=expires_at,
                is_active=True,
            )
            self.session.add(subscription)
            logger.info(
                "Создана подписка",
                extra={
                    "subscription_id": None,
                    "user_id": user.id,
                    "expires_at": expires_at.isoformat(),
                    "token_prefix": subscription.token[:6],
                },
            )

        await self.session.commit()
        await self.session.refresh(subscription)
        return subscription

    def build_subscription_url(self, token: str) -> str:
        return f"{settings.base_sub_url}/{token}"
