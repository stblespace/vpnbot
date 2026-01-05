"""Модель сервера, доступного для подключения."""
from sqlalchemy import Boolean, Column, Integer, String

from app.db import Base


class Server(Base):
    __tablename__ = "servers"

    id = Column(Integer, primary_key=True)
    country_code = Column(String(8), nullable=False, index=True)
    name = Column(String(255), nullable=True)
    host = Column(String(255), nullable=False)
    port = Column(Integer, nullable=False)
    protocol = Column(String(32), nullable=False, default="vless")
    network = Column(String(16), nullable=False)  # tcp | ws | xhttp
    public_key = Column(String(255), nullable=False)
    sni = Column(String(255), nullable=True)
    enabled = Column(Boolean, nullable=False, default=True, index=True)
