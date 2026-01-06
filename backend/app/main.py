"""Точка входа FastAPI-приложения."""
import asyncio
import logging
from pathlib import Path
from urllib.parse import urlsplit

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.staticfiles import StaticFiles

from app.api.admin_servers import router as admin_servers_router
from app.api.auth import router as auth_router
from app.api.client import router as client_router
from app.api.bot import router as bot_router
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
    static_dir = Path(__file__).resolve().parent.parent / "webapp"

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        # Логируем 422 с телом запроса и списком ошибок для быстрого дебага админских форм
        body = await request.body()
        logger.warning(
            "Ошибка валидации запроса",
            extra={"path": request.url.path, "errors": exc.errors(), "body": body.decode(errors="ignore")},
        )
        return JSONResponse(status_code=422, content={"detail": exc.errors()})

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
    app.include_router(bot_router)
    app.include_router(client_router)
    app.include_router(admin_servers_router)
    if static_dir.exists():
        # Раздаем mini-app статику (index.html, admin.html и ассеты)
        app.mount("/", StaticFiles(directory=static_dir, html=True), name="webapp")
    return app


app = create_app()
