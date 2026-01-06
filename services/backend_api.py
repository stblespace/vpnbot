"""HTTP-клиент к backend для получения каноничного статуса подписки."""
import os
from typing import Any, Dict, Optional

import aiohttp

BACKEND_API_URL = os.getenv("BACKEND_API_URL", "http://backend:8000").rstrip("/")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")


async def fetch_subscription(tg_id: int) -> Dict[str, Any]:
    """Запросить у backend актуальное состояние подписки."""
    url = f"{BACKEND_API_URL}/api/bot/subscription"
    headers = {"X-Bot-Token": BOT_TOKEN}
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
        async with session.post(url, json={"tg_id": tg_id}, headers=headers) as resp:
            if resp.status != 200:
                detail = await resp.text()
                raise RuntimeError(f"Backend returned {resp.status}: {detail}")
            return await resp.json()


async def safe_fetch_subscription(tg_id: int) -> Optional[Dict[str, Any]]:
    """Безопасная обертка: вернёт None при ошибке сети/бэка."""
    try:
        return await fetch_subscription(tg_id)
    except Exception:
        return None
