"""Клиент для работы с 3X-UI на основе локальной реализации (сессии и API панели)."""
from __future__ import annotations

import json
import logging
from copy import deepcopy
from typing import Any, Iterable

import aiohttp
from aiohttp import ClientSession, ClientTimeout

from app.config import settings

logger = logging.getLogger(__name__)


class XUIClient:
    """Адаптер к 3X-UI API (куки-сессия + /panel/api/*)."""

    def __init__(self) -> None:
        self.cookie_jar = aiohttp.CookieJar(unsafe=True)
        self.session: ClientSession | None = None
        self._logged_in = False
        self._base_url = settings.xui_base_url.rstrip("/")

    def _build_url(self, path: str) -> str:
        if not path.startswith("/"):
            path = "/" + path
        return f"{self._base_url}{path}"

    async def _ensure_session(self) -> None:
        if self.session is None or self.session.closed:
            timeout = ClientTimeout(total=settings.xui_request_timeout or None)
            self.session = aiohttp.ClientSession(
                cookie_jar=self.cookie_jar,
                trust_env=True,
                timeout=timeout,
            )
            self._logged_in = False

    async def close(self) -> None:
        if self.session:
            await self.session.close()

    async def _login(self) -> bool:
        await self._ensure_session()
        assert self.session is not None

        auth_data = {"username": settings.xui_username, "password": settings.xui_password}
        login_url = self._build_url("/login")
        async with self.session.post(login_url, data=auth_data) as resp:
            raw = await resp.text()
            success = False
            if resp.status == 200:
                try:
                    payload = json.loads(raw)
                    success = bool(payload.get("success"))
                except Exception:
                    success = "success" in raw.lower()
            if success:
                self._logged_in = True
                logger.info("Аутентификация в 3X-UI успешна")
                return True
            logger.error(
                "Не удалось войти в 3X-UI",
                extra={"status": resp.status, "body": raw[:200]},
            )
        return False

    async def _request_json(
        self,
        method: str,
        path: str,
        *,
        retry: bool = False,
        **kwargs: Any,
    ) -> tuple[int, dict[str, Any] | None, str]:
        await self._ensure_session()
        assert self.session is not None

        if not self._logged_in:
            if not await self._login():
                return 0, None, ""

        url = self._build_url(path)
        async with self.session.request(method, url, **kwargs) as resp:
            raw = await resp.text()
            try:
                data = json.loads(raw)
            except Exception:
                data = None

            if resp.status in {401, 403, 404} and not retry:
                # Панель возвращает 404 для неавторизованных API-запросов
                self._logged_in = False
                if await self._login():
                    return await self._request_json(method, path, retry=True, **kwargs)
            return resp.status, data, raw

    @staticmethod
    def _extract_clients(inbound: dict[str, Any]) -> list[dict[str, Any]]:
        try:
            inbound_settings = json.loads(inbound.get("settings") or "{}")
        except json.JSONDecodeError:
            return []
        clients = inbound_settings.get("clients") or []
        return clients if isinstance(clients, list) else []

    @staticmethod
    def _find_client(clients: list[dict[str, Any]], client_uuid: str) -> tuple[dict[str, Any] | None, str | None]:
        target = str(client_uuid)
        for client in clients:
            cid = str(client.get("id", ""))
            email = str(client.get("email", ""))
            if cid == target or email == target:
                return client, cid or email or None
        return None, None

    def _build_client_payload(self, template: dict[str, Any], client_id: str) -> dict[str, Any]:
        base = deepcopy(template) if template else {}
        base.update(
            {
                "id": client_id,
                "email": client_id,
                "enable": True,
            }
        )
        # Подстрахуемся, чтобы числовые поля не стали None
        base.setdefault("flow", "")
        base.setdefault("limitIp", 0)
        base.setdefault("totalGB", 0)
        base.setdefault("expiryTime", 0)
        base.setdefault("reset", 0)
        # отметки времени выставит сама панель, если их нет
        return base

    async def list_inbounds(self) -> list[dict[str, Any]]:
        status, data, text = await self._request_json("GET", "/panel/api/inbounds/list")
        if status != 200:
            logger.error("Не удалось получить список inbounds", extra={"status": status, "body": text[:200]})
            return []
        if data and data.get("success"):
            objs = data.get("obj") or []
            return objs if isinstance(objs, list) else []
        logger.error("Ответ 3X-UI неуспешен при list_inbounds", extra={"body": text[:200]})
        return []

    async def get_inbound(self, inbound_id: int) -> dict[str, Any] | None:
        status, data, text = await self._request_json("GET", f"/panel/api/inbounds/get/{inbound_id}")
        if status != 200:
            logger.error(
                "Не удалось получить inbound",
                extra={"status": status, "body": text[:200], "inbound_id": inbound_id},
            )
            return None
        if data and data.get("success"):
            return data.get("obj")
        logger.error("Ответ 3X-UI неуспешен при get_inbound", extra={"body": text[:200], "inbound_id": inbound_id})
        return None

    async def add_client(self, client_uuid: str, inbound_id: int) -> bool:
        """Добавить клиента через /panel/api/inbounds/addClient."""
        inbound = await self.get_inbound(inbound_id)
        if not inbound:
            return False

        clients = self._extract_clients(inbound)
        existing, _ = self._find_client(clients, client_uuid)
        if existing:
            logger.info(
                "Клиент уже существует в inbound, пропускаем добавление",
                extra={"inbound_id": inbound_id, "client_id": client_uuid},
            )
            return True

        template = clients[0] if clients else {}
        new_client = self._build_client_payload(template, str(client_uuid))
        payload = {
            "id": inbound_id,
            "settings": json.dumps({"clients": [new_client]}),
        }

        status, data, text = await self._request_json(
            "POST",
            "/panel/api/inbounds/addClient",
            json=payload,
        )
        if status != 200 or not data or not data.get("success"):
            logger.error(
                "Не удалось добавить клиента в inbound",
                extra={"status": status, "body": text[:200], "inbound_id": inbound_id, "client_id": client_uuid},
            )
            return False
        return True

    async def disable_client(self, client_uuid: str, inbound_id: int) -> bool:
        """Отключить клиента через /panel/api/inbounds/updateClient/{clientId}."""
        inbound = await self.get_inbound(inbound_id)
        if not inbound:
            return False

        clients = self._extract_clients(inbound)
        existing, client_id = self._find_client(clients, client_uuid)
        if not existing or not client_id:
            logger.warning(
                "Клиент не найден или уже выключен",
                extra={"inbound_id": inbound_id, "client_id": client_uuid},
            )
            return False

        payload = {
            "id": inbound_id,
            "settings": json.dumps({"clients": [dict(existing, enable=False)]}),
        }
        status, data, text = await self._request_json(
            "POST",
            f"/panel/api/inbounds/updateClient/{client_id}",
            json=payload,
        )
        if status != 200 or not data or not data.get("success"):
            logger.error(
                "Не удалось выключить клиента в 3X-UI",
                extra={"status": status, "body": text[:200], "inbound_id": inbound_id, "client_id": client_uuid},
            )
            return False
        return True

    async def remove_client(self, client_uuid: str, inbound_id: int) -> bool:
        """Удалить клиента через /panel/api/inbounds/:id/delClientByEmail/:email."""
        inbound = await self.get_inbound(inbound_id)
        if not inbound:
            return False

        clients = self._extract_clients(inbound)
        existing, _ = self._find_client(clients, client_uuid)
        email = str(existing.get("email")) if existing else str(client_uuid)

        status, data, text = await self._request_json(
            "POST",
            f"/panel/api/inbounds/{inbound_id}/delClientByEmail/{email}",
        )
        if status != 200 or not data or not data.get("success"):
            logger.error(
                "Не удалось удалить клиента в 3X-UI",
                extra={"status": status, "body": text[:200], "inbound_id": inbound_id, "client_id": client_uuid},
            )
            return False
        return True


async def add_clients_for_inbounds(client: XUIClient, client_uuid: str, inbound_ids: Iterable[int]) -> None:
    """Добавить клиента во все перечисленные inbound'ы, продолжая при ошибке."""
    for inbound_id in inbound_ids:
        try:
            success = await client.add_client(client_uuid, inbound_id)
            if not success:
                logger.error(
                    "Не удалось добавить клиента в inbound",
                    extra={"client_id": client_uuid, "inbound_id": inbound_id},
                )
        except Exception:
            logger.exception(
                "Ошибка добавления клиента в inbound",
                extra={"client_id": client_uuid, "inbound_id": inbound_id},
            )


async def disable_clients_for_inbounds(client: XUIClient, client_uuid: str, inbound_ids: Iterable[int]) -> None:
    """Выключить клиента во всех inbound'ах, ошибки логируются и не прерывают цикл."""
    for inbound_id in inbound_ids:
        try:
            success = await client.disable_client(client_uuid, inbound_id)
            if not success:
                logger.warning(
                    "Не удалось выключить клиента в inbound",
                    extra={"client_id": client_uuid, "inbound_id": inbound_id},
                )
        except Exception:
            logger.exception(
                "Ошибка выключения клиента в inbound",
                extra={"client_id": client_uuid, "inbound_id": inbound_id},
            )


async def remove_clients_for_inbounds(client: XUIClient, client_uuid: str, inbound_ids: Iterable[int]) -> None:
    """Удалить клиента во всех inbound'ах, ошибки логируются и не прерывают цикл."""
    for inbound_id in inbound_ids:
        try:
            success = await client.remove_client(client_uuid, inbound_id)
            if not success:
                logger.warning(
                    "Не удалось удалить клиента в inbound",
                    extra={"client_id": client_uuid, "inbound_id": inbound_id},
                )
        except Exception:
            logger.exception(
                "Ошибка удаления клиента в inbound",
                extra={"client_id": client_uuid, "inbound_id": inbound_id},
            )
