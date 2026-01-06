"""Работа с Postgres той же БД, что и backend."""
import logging
import os
import secrets
import uuid as uuid_module
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, String, select
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    pass


DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL не задан")

engine = create_async_engine(DATABASE_URL, future=True)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    tg_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True, nullable=False)
    uuid: Mapped[uuid_module.UUID] = mapped_column(
        PG_UUID(as_uuid=True), unique=True, nullable=False, default=uuid_module.uuid4
    )
    role: Mapped[str] = mapped_column(String(16), default="user", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    token: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


async def ensure_user(session: AsyncSession, tg_id: int) -> User:
    stmt = select(User).where(User.tg_id == tg_id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()
    if user:
        return user
    user = User(tg_id=tg_id, uuid=uuid_module.uuid4())
    session.add(user)
    await session.commit()
    await session.refresh(user)
    logger.info("Создан пользователь", extra={"tg_id": tg_id, "user_id": user.id})
    return user


def _subscription_to_dict(sub: Subscription) -> dict:
    return {
        "id": sub.id,
        "user_id": sub.user_id,
        "token": sub.token,
        "expires_at": sub.expires_at.isoformat(),
        "is_active": sub.is_active,
        "plan_code": "ind",  # базовый план для фронта
    }


async def get_latest_subscription(session: AsyncSession, tg_id: int) -> Optional[dict]:
    user = await ensure_user(session, tg_id)
    stmt = (
        select(Subscription)
        .where(Subscription.user_id == user.id)
        .order_by(Subscription.expires_at.desc())
    )
    result = await session.execute(stmt)
    sub = result.scalars().first()
    if sub:
        logger.info("Последняя подписка найдена", extra={"tg_id": tg_id, "subscription_id": sub.id})
        return _subscription_to_dict(sub)
    logger.info("Подписок не найдено", extra={"tg_id": tg_id})
    return None


async def get_subscription_by_id(session: AsyncSession, subscription_id: int) -> Optional[dict]:
    stmt = select(Subscription).where(Subscription.id == subscription_id)
    result = await session.execute(stmt)
    sub = result.scalar_one_or_none()
    return _subscription_to_dict(sub) if sub else None


async def create_or_extend_subscription(session: AsyncSession, tg_id: int, expires_at: datetime) -> dict:
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    else:
        expires_at = expires_at.astimezone(timezone.utc)

    user = await ensure_user(session, tg_id)
    stmt = (
        select(Subscription)
        .where(Subscription.user_id == user.id)
        .order_by(Subscription.expires_at.desc())
    )
    result = await session.execute(stmt)
    sub = result.scalars().first()

    if sub:
        sub.expires_at = expires_at
        sub.is_active = True
        action = "extend"
    else:
        token = secrets.token_urlsafe(32)
        sub = Subscription(
            user_id=user.id,
            token=token,
            expires_at=expires_at,
            is_active=True,
        )
        session.add(sub)
        action = "create"

    await session.commit()
    await session.refresh(sub)
    logger.info(
        "Подписка сохранена",
        extra={
            "action": action,
            "tg_id": tg_id,
            "user_id": user.id,
            "subscription_id": sub.id,
            "token_prefix": sub.token[:6],
            "expires_at": sub.expires_at.isoformat(),
        },
    )
    return _subscription_to_dict(sub)


def days_left(expires_at: str) -> Optional[int]:
    try:
        expires = datetime.fromisoformat(expires_at)
    except ValueError:
        return None
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    delta = expires - _now_utc()
    if delta.total_seconds() < 0:
        return 0
    return delta.days + (1 if delta.seconds > 0 else 0)
