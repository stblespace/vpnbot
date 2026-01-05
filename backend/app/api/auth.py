"""Маршруты для аутентификации через Telegram Mini App."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db import get_session
from app.services.auth_service import AuthResult, AuthService

router = APIRouter(prefix="/api/auth", tags=["auth"])


class TelegramAuthRequest(BaseModel):
    initData: str


class TelegramAuthResponse(BaseModel):
    tg_id: int
    role: str


@router.post("/telegram", response_model=TelegramAuthResponse, summary="Аутентификация Telegram WebApp")
async def auth_telegram(
    payload: TelegramAuthRequest,
    session: AsyncSession = Depends(get_session),
) -> TelegramAuthResponse:
    """Проверить initData, создать пользователя при необходимости и вернуть роль."""
    service = AuthService(session=session, bot_token=settings.bot_token, admin_tg_ids=settings.admin_tg_ids)
    result: AuthResult = await service.authenticate(payload.initData)
    return TelegramAuthResponse(tg_id=result.user.tg_id, role=result.role)
