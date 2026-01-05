"""Сервис аутентификации через Telegram Mini App."""
import hashlib
import hmac
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from urllib.parse import parse_qsl

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User


class AuthError(Exception):
    """Ошибки аутентификации."""


@dataclass
class AuthResult:
    user: User
    role: str


class AuthService:
    def __init__(self, session: AsyncSession, bot_token: str, admin_tg_ids: list[int] | None = None) -> None:
        self.session = session
        self.bot_token = bot_token
        self.admin_tg_ids = admin_tg_ids or []

    async def authenticate(self, init_data: str) -> AuthResult:
        """Проверить подпись, найти/создать пользователя и определить роль."""
        data = self._validate_signature(init_data)
        user_payload = self._extract_user(data)
        tg_id = self._extract_tg_id(user_payload)

        user = await self._get_or_create_user(tg_id)
        if not user.is_active:
            raise AuthError("Пользователь деактивирован")

        role = await self._resolve_role(user)
        return AuthResult(user=user, role=role)

    def _validate_signature(self, init_data: str) -> dict[str, str]:
        """Подпись согласно https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app."""
        parsed = dict(parse_qsl(init_data, keep_blank_values=True))
        received_hash = parsed.pop("hash", None)
        if not received_hash:
            raise AuthError("hash отсутствует в initData")

        check_string = "\n".join(f"{k}={v}" for k, v in sorted(parsed.items()))
        secret_key = hmac.new("WebAppData".encode(), self.bot_token.encode(), hashlib.sha256).digest()
        computed_hash = hmac.new(secret_key, check_string.encode(), hashlib.sha256).hexdigest()

        if not hmac.compare_digest(computed_hash, received_hash):
            raise AuthError("Некорректная подпись Telegram")

        # TODO: проверять auth_date на актуальность
        return parsed

    @staticmethod
    def _extract_user(parsed: dict[str, str]) -> dict[str, Any]:
        user_raw = parsed.get("user")
        if not user_raw:
            raise AuthError("Отсутствует user в initData")
        try:
            return json.loads(user_raw)
        except json.JSONDecodeError as exc:
            raise AuthError("Невалидный JSON в user") from exc

    @staticmethod
    def _extract_tg_id(user_payload: dict[str, Any]) -> int:
        tg_id = user_payload.get("id")
        if tg_id is None:
            raise AuthError("Не удалось извлечь tg_id")
        return int(tg_id)

    async def _get_or_create_user(self, tg_id: int) -> User:
        stmt = select(User).where(User.tg_id == tg_id)
        result = await self.session.execute(stmt)
        user = result.scalar_one_or_none()
        if user:
            return user

        user = User(tg_id=tg_id)
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def _resolve_role(self, user: User) -> str:
        role = user.role or "user"
        if user.tg_id in self.admin_tg_ids or role == "admin":
            if role != "admin":
                user.role = "admin"
                await self.session.commit()
            return "admin"
        return "user"
