"""Админские эндпоинты для CRUD по серверам."""
import logging
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.auth import AuthContext, require_admin
from app.db import get_session
from app.services.server_service import ServerNotFound, ServerService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin/servers", tags=["admin"])


class ServerBase(BaseModel):
    country_code: str = Field(..., max_length=8)
    name: str | None = Field(None, max_length=255)
    host: str
    port: int = Field(..., ge=1, le=65535)
    network: str
    public_key: str
    sni: str | None = None
    short_id: str = Field(..., min_length=1, max_length=32)
    protocol: str = "vless"
    enabled: bool = True


class ServerCreate(ServerBase):
    """Тело создания сервера."""


class ServerUpdate(BaseModel):
    country_code: str | None = Field(None, max_length=8)
    name: str | None = Field(None, max_length=255)
    host: str | None = None
    port: int | None = Field(None, ge=1, le=65535)
    network: str | None = None
    public_key: str | None = None
    sni: str | None = None
    protocol: str | None = None
    enabled: bool | None = None


class ServerResponse(ServerBase):
    id: int
    short_id: str | None = None
    created_at: datetime | None = None

    class Config:
        from_attributes = True


@router.get("", response_model=list[ServerResponse], summary="Список всех серверов")
async def list_servers(
    admin: AuthContext = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> list[ServerResponse]:
    service = ServerService(session)
    servers = await service.list_servers()
    logger.info("Админ запросил список серверов", extra={"tg_id": admin.tg_id})
    return [ServerResponse.model_validate(server) for server in servers]


@router.post("", response_model=ServerResponse, status_code=status.HTTP_201_CREATED, summary="Создать сервер")
async def create_server(
    payload: ServerCreate,
    admin: AuthContext = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> ServerResponse:
    service = ServerService(session)
    server = await service.create_server(payload.model_dump())
    logger.info("Админ создал сервер", extra={"tg_id": admin.tg_id, "server_id": server.id, "host": server.host})
    return ServerResponse.model_validate(server)


@router.put("/{server_id}", response_model=ServerResponse, summary="Обновить сервер (полная замена)")
@router.patch("/{server_id}", response_model=ServerResponse, summary="Обновить сервер (частично)")
async def update_server(
    server_id: int,
    payload: ServerUpdate,
    admin: AuthContext = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> ServerResponse:
    service = ServerService(session)
    try:
        server = await service.update_server(server_id, payload.model_dump(exclude_unset=True))
    except ServerNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    logger.info("Админ обновил сервер", extra={"tg_id": admin.tg_id, "server_id": server.id})
    return ServerResponse.model_validate(server)


@router.delete("/{server_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Удалить сервер")
async def delete_server(
    server_id: int,
    admin: AuthContext = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> None:
    service = ServerService(session)
    try:
        await service.delete_server(server_id)
    except ServerNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    logger.info("Админ удалил сервер", extra={"tg_id": admin.tg_id, "server_id": server_id})
