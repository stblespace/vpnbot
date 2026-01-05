"""Зависимости FastAPI для аутентификации через Telegram Mini App."""
from dataclasses import dataclass

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db import get_session
from app.services.auth_service import AuthError, AuthResult, AuthService


@dataclass
class AuthContext:
    user_id: int
    tg_id: int
    role: str
    is_active: bool


async def get_auth_context(
    init_data: str | None = Header(None, alias="X-Telegram-Init-Data"),
    session: AsyncSession = Depends(get_session),
) -> AuthContext:
    """Проверить подпись Telegram и вернуть контекст пользователя."""
    if not init_data:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="initData отсутствует")
    service = AuthService(session=session, bot_token=settings.bot_token, admin_tg_ids=settings.admin_tg_ids)
    try:
        result: AuthResult = await service.authenticate(init_data)
    except AuthError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    return AuthContext(
        user_id=result.user.id,
        tg_id=result.user.tg_id,
        role=result.role,
        is_active=result.is_active,
    )


async def require_admin(context: AuthContext = Depends(get_auth_context)) -> AuthContext:
    """Убедиться, что пользователь — админ."""
    if context.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Требуется администратор")
    return context
