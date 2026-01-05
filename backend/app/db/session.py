"""Инициализация подключения к базе данных и фабрика сессий."""
from typing import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings


class Base(DeclarativeBase):
    """Базовый класс для декларативных моделей."""


echo_sql = settings.log_level.upper() == "DEBUG"
engine = create_async_engine(settings.database_url, echo=echo_sql, future=True)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_session() -> AsyncIterator[AsyncSession]:
    """Зависимость FastAPI для выдачи сессии."""
    async with AsyncSessionLocal() as session:
        yield session


async def init_db() -> None:
    """Создать таблицы, если их еще нет."""
    from app.models import Server, Subscription, User  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
