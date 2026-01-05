"""Маршруты для клиентского мини-приложения."""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.dependencies.auth import AuthContext, get_auth_context
from app.db import get_session
from app.services.subscription_service import SubscriptionService

router = APIRouter(prefix="/api/me", tags=["client"])


class SubscriptionInfo(BaseModel):
    subscription_id: int | None = None
    status: str
    expires_in_days: int | None = None
    sub_url: str | None = None


@router.get("/subscription", response_model=SubscriptionInfo, summary="Статус подписки текущего пользователя")
async def my_subscription(
    auth: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> SubscriptionInfo:
    """Вернуть состояние подписки для текущего пользователя."""
    service = SubscriptionService(session)
    subscription = await service.get_latest_subscription_for_user(auth.user_id)

    if not subscription:
        return SubscriptionInfo(status="inactive")

    now = datetime.now(timezone.utc)
    is_expired = subscription.is_expired(now) or not subscription.is_active
    status = "expired" if is_expired else "active"

    expires_in_days = None
    if subscription.expires_at:
        delta = subscription.expires_at - now
        expires_in_days = max(0, int(delta.total_seconds() // 86400))

    sub_url = f"{settings.base_sub_url.rstrip('/')}/{subscription.token}"

    return SubscriptionInfo(
        subscription_id=subscription.id,
        status=status,
        expires_in_days=expires_in_days,
        sub_url=sub_url,
    )
