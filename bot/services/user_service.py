"""Работа с пользователями."""
import logging
import uuid as uuid_pkg

from sqlalchemy import BigInteger, Boolean, select, String
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from bot.db.session import Base

logger = logging.getLogger(__name__)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    tg_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    uuid: Mapped[uuid_pkg.UUID] = mapped_column(default=uuid_pkg.uuid4, unique=True)
    role: Mapped[str] = mapped_column(String(16), default="user")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class UserService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_or_create_user(self, tg_id: int) -> User:
        stmt = select(User).where(User.tg_id == tg_id)
        result = await self.session.execute(stmt)
        user = result.scalar_one_or_none()
        if user:
            logger.info("Пользователь найден", extra={"tg_id": tg_id, "user_id": user.id})
            return user

        user = User(tg_id=tg_id)
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        logger.info("Пользователь создан", extra={"tg_id": tg_id, "user_id": user.id})
        return user
