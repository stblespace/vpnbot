"""Точка входа FastAPI-приложения."""
import asyncio
import logging
from urllib.parse import urlsplit

from fastapi import FastAPI

from app.api.admin_servers import router as admin_servers_router
from app.api.auth import router as auth_router
from app.api.client import router as client_router
from app.api.subscription import router as subscription_router
from app.config import settings
from app.db import init_db
from app.services.cleanup_service import expired_subscriptions_loop

logger = logging.getLogger(__name__)


def _mask_dsn(dsn: str) -> str:
    parsed = urlsplit(dsn)
    if "@" not in dsn:
        return dsn
    netloc = parsed.netloc
    if "@" in netloc and ":" in netloc.split("@")[0]:
        user_part, host_part = netloc.split("@", 1)
        user = user_part.split(":")[0]
        netloc = f"{user}:***@{host_part}"
    return parsed._replace(netloc=netloc).geturl()


def configure_logging() -> None:
    level = getattr(logging, settings.log_level.upper(), logging.INFO)
    logging.basicConfig(level=level)
    logger.info("Логирование настроено", extra={"log_level": settings.log_level})


def create_app() -> FastAPI:
    app = FastAPI(title="VPN Subscription Backend", docs_url="/docs", openapi_url="/openapi.json")

    @app.on_event("startup")
    async def on_startup() -> None:  # noqa: D401
        """Создаем таблицы и включаем логирование при запуске."""
        configure_logging()
        logger.info("Старт backend", extra={"database_url": _mask_dsn(settings.database_url)})
        await init_db()
        logger.info("Инициализация БД завершена")
        # Фоновая задача: ежедневная деактивация истекших подписок
        asyncio.create_task(expired_subscriptions_loop())

    app.include_router(subscription_router)
    app.include_router(auth_router)
    app.include_router(client_router)
    app.include_router(admin_servers_router)
    return app


app = create_app()
