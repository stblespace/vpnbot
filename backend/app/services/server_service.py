"""Сервис управления серверами VPN."""
import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Server

logger = logging.getLogger(__name__)


class ServerNotFound(Exception):
    """Сервер не найден."""


class ServerService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_servers(self) -> list[Server]:
        result = await self.session.execute(select(Server))
        servers = list(result.scalars().all())
        logger.info("Получен список серверов", extra={"count": len(servers)})
        return servers

    async def create_server(self, data: dict[str, Any]) -> Server:
        server = Server(**data)
        self.session.add(server)
        await self.session.commit()
        await self.session.refresh(server)
        logger.info(
            "Создан сервер",
            extra={
                "server_id": server.id,
                "host": server.host,
                "network": server.network,
                "inbound_id": server.inbound_id,
            },
        )
        return server

    async def _get_server(self, server_id: int) -> Server:
        result = await self.session.execute(select(Server).where(Server.id == server_id))
        server = result.scalar_one_or_none()
        if not server:
            raise ServerNotFound(f"Сервер {server_id} не найден")
        return server

    async def update_server(self, server_id: int, data: dict[str, Any]) -> Server:
        server = await self._get_server(server_id)
        for field, value in data.items():
            setattr(server, field, value)
        await self.session.commit()
        await self.session.refresh(server)
        logger.info(
            "Обновлен сервер",
            extra={"server_id": server.id, "host": server.host, "inbound_id": server.inbound_id},
        )
        return server

    async def delete_server(self, server_id: int) -> None:
        server = await self._get_server(server_id)
        await self.session.delete(server)
        await self.session.commit()
        logger.info("Удален сервер", extra={"server_id": server_id})
