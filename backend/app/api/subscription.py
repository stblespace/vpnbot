"""HTTP endpoint для выдачи подписки."""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.services.subscription_service import (
    NoActiveServers,
    SubscriptionService,
    SubscriptionUnavailable,
)

router = APIRouter()


@router.get("/sub/{token}", response_class=PlainTextResponse, summary="Динамическая подписка VLESS")
async def get_subscription(
    token: str,
    session: AsyncSession = Depends(get_session),
) -> PlainTextResponse:
    """Дать клиенту актуальный список VLESS ссылок."""
    service = SubscriptionService(session)
    try:
        payload = await service.build_subscription_payload(token)
    except SubscriptionUnavailable:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Подписка недоступна или истекла",
        )
    except NoActiveServers:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Нет активных серверов для выдачи конфигурации",
        )
    return PlainTextResponse(payload, media_type="text/plain")
