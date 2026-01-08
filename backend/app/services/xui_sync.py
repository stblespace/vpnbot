"""Связка между базой и 3X-UI: выбираем inbound'ы и применяем операции к клиенту."""
from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Server
from app.services.xui_client import (
    XUIClient,
    add_clients_for_inbounds,
    disable_clients_for_inbounds,
    remove_clients_for_inbounds,
)

logger = logging.getLogger(__name__)


async def _collect_inbound_ids(session: AsyncSession, *, enabled_only: bool = True) -> list[int]:
    stmt = select(Server.inbound_id).where(Server.inbound_id.is_not(None))
    if enabled_only:
        stmt = stmt.where(Server.enabled.is_(True))

    try:
        result = await session.execute(stmt)
    except SQLAlchemyError as exc:
        logger.error("Не удалось получить inbound_id из БД", exc_info=exc)
        return []

    inbound_ids = [inbound_id for inbound_id in result.scalars().all() if inbound_id is not None]
    unique_ids = list(dict.fromkeys(inbound_ids))  # сохраняем порядок без дублей
    if not unique_ids:
        logger.warning("Нет inbound_id для синхронизации с 3X-UI")
    return unique_ids


def _with_client(provided: XUIClient | None) -> tuple[XUIClient, bool]:
    if provided:
        return provided, False
    return XUIClient(), True


async def ensure_user_enabled(
    session: AsyncSession,
    user_uuid: str,
    *,
    xui_client: XUIClient | None = None,
) -> None:
    """Добавить/включить клиента во все активные inbound'ы."""
    inbound_ids = await _collect_inbound_ids(session, enabled_only=True)
    if not inbound_ids:
        return

    client, should_close = _with_client(xui_client)
    try:
        await add_clients_for_inbounds(client, user_uuid, inbound_ids)
    finally:
        if should_close:
            await client.close()


async def ensure_user_disabled(
    session: AsyncSession,
    user_uuid: str,
    *,
    include_disabled_servers: bool = True,
    xui_client: XUIClient | None = None,
) -> None:
    """Отключить клиента во всех inbound'ах, по умолчанию независимо от enabled-флага сервера."""
    inbound_ids = await _collect_inbound_ids(session, enabled_only=not include_disabled_servers)
    if not inbound_ids:
        return

    client, should_close = _with_client(xui_client)
    try:
        await disable_clients_for_inbounds(client, user_uuid, inbound_ids)
    finally:
        if should_close:
            await client.close()


async def remove_user_from_inbounds(
    session: AsyncSession,
    user_uuid: str,
    *,
    include_disabled_servers: bool = True,
    xui_client: XUIClient | None = None,
) -> None:
    """Полностью удалить клиента из inbound'ов (используется только при ручном подчистке)."""
    inbound_ids = await _collect_inbound_ids(session, enabled_only=not include_disabled_servers)
    if not inbound_ids:
        return

    client, should_close = _with_client(xui_client)
    try:
        await remove_clients_for_inbounds(client, user_uuid, inbound_ids)
    finally:
        if should_close:
            await client.close()
