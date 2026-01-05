"""Админские эндпоинты для CRUD по серверам."""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.auth import require_admin
from app.db import get_session
from app.services.server_service import ServerNotFound, ServerService

router = APIRouter(prefix="/api/admin/servers", tags=["admin"])


class ServerBase(BaseModel):
    country_code: str = Field(..., max_length=8)
    name: str | None = Field(None, max_length=255)
    host: str
    port: int = Field(..., ge=1, le=65535)
    network: str
    public_key: str
    sni: str | None = None
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

    class Config:
        from_attributes = True


@router.get("", response_model=list[ServerResponse], summary="Список всех серверов")
async def list_servers(
    _=Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> list[ServerResponse]:
    service = ServerService(session)
    servers = await service.list_servers()
    return [ServerResponse.model_validate(server) for server in servers]


@router.post("", response_model=ServerResponse, status_code=status.HTTP_201_CREATED, summary="Создать сервер")
async def create_server(
    payload: ServerCreate,
    _=Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> ServerResponse:
    service = ServerService(session)
    server = await service.create_server(payload.model_dump())
    return ServerResponse.model_validate(server)


@router.put("/{server_id}", response_model=ServerResponse, summary="Обновить сервер (полная замена)")
@router.patch("/{server_id}", response_model=ServerResponse, summary="Обновить сервер (частично)")
async def update_server(
    server_id: int,
    payload: ServerUpdate,
    _=Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> ServerResponse:
    service = ServerService(session)
    try:
        server = await service.update_server(server_id, payload.model_dump(exclude_unset=True))
    except ServerNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return ServerResponse.model_validate(server)


@router.delete("/{server_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Удалить сервер")
async def delete_server(
    server_id: int,
    _=Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> None:
    service = ServerService(session)
    try:
        await service.delete_server(server_id)
    except ServerNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
