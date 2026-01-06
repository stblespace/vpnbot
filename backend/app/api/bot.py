"""Эндпоинты для Telegram-бота: единый источник подписки."""
from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db import get_session
from app.services.subscription_service import SubscriptionService

router = APIRouter(prefix="/api/bot", tags=["bot"])


class BotSubscriptionRequest(BaseModel):
    tg_id: int


class BotSubscriptionResponse(BaseModel):
    status: str
    subscription_id: int | None = None
    expires_at: str | None = None
    expires_in_days: int | None = None
    sub_url: str | None = None
    servers_count: int = 0


@router.post("/subscription", response_model=BotSubscriptionResponse, summary="Состояние подписки для бота")
async def bot_subscription(
    payload: BotSubscriptionRequest,
    bot_token: str = Header(..., alias="X-Bot-Token"),
    session: AsyncSession = Depends(get_session),
) -> BotSubscriptionResponse:
    """Бот запрашивает фактическое состояние подписки по tg_id."""
    if bot_token != settings.bot_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Неверный X-Bot-Token")

    service = SubscriptionService(session)
    summary = await service.get_subscription_summary_by_tg_id(payload.tg_id)
    return BotSubscriptionResponse(**summary)
