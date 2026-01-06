"""Маршруты для клиентского мини-приложения."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.auth import AuthContext, get_auth_context
from app.db import get_session
from app.services.subscription_service import SubscriptionService

router = APIRouter(prefix="/api/me", tags=["client"])


class SubscriptionInfo(BaseModel):
    status: str
    subscription_id: int | None = None
    expires_at: str | None = None
    expires_in_days: int | None = None
    sub_url: str | None = None
    servers_count: int = 0


@router.get("/subscription", response_model=SubscriptionInfo, summary="Статус подписки текущего пользователя")
async def my_subscription(
    auth: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> SubscriptionInfo:
    """Вернуть состояние подписки для текущего пользователя."""
    service = SubscriptionService(session)
    summary = await service.get_subscription_summary_by_tg_id(auth.tg_id if auth.is_active else -1)
    return SubscriptionInfo(**summary)
