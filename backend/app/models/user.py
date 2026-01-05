"""Модель пользователя Telegram."""
import uuid

from sqlalchemy import BigInteger, Boolean, Column, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    tg_id = Column(BigInteger, unique=True, nullable=False, index=True)
    uuid = Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4)
    is_active = Column(Boolean, nullable=False, default=True)
    role = Column(String(16), nullable=False, default="user")

    subscriptions = relationship("Subscription", back_populates="user", cascade="all, delete-orphan")
