"""Построение VLESS URI на лету."""
import logging
from urllib.parse import urlencode

from app.models.server import Server

logger = logging.getLogger(__name__)


class ConfigGenerator:
    """Генератор конфигураций без сохранения в базе."""

    def build_vless_uri(self, server: Server, user_uuid: str) -> str:
        """Собрать одну VLESS ссылку для конкретного сервера."""
        protocol = server.protocol
        label = (server.country_code or server.host).upper()

        if protocol != "vless":
            logger.error(
                "Неподдерживаемый протокол для генерации VLESS URI",
                extra={"server_id": getattr(server, "id", None), "protocol": protocol},
            )
            raise ValueError("Поддерживается только VLESS")

        missing = []
        for field_name in ("host", "port", "network", "public_key"):
            value = getattr(server, field_name)
            if value in (None, ""):
                missing.append(field_name)

        if not server.sni:
            missing.append("sni")
        if not server.short_id:
            missing.append("short_id")

        if missing:
            logger.error(
                "Отсутствуют обязательные поля сервера для Reality",
                extra={"server_id": getattr(server, "id", None), "missing_fields": missing},
            )
            raise ValueError(f"Отсутствуют обязательные поля: {', '.join(missing)}")

        allowed_networks = {"tcp", "ws", "xhttp"}
        if server.network not in allowed_networks:
            logger.error(
                "Неподдерживаемый тип сети для VLESS",
                extra={"server_id": getattr(server, "id", None), "network": server.network},
            )
            raise ValueError("Неподдерживаемый тип сети")

        query = urlencode(
            [
                ("encryption", "none"),
                ("security", "reality"),
                ("pbk", server.public_key),
                ("sid", server.short_id),
                ("sni", server.sni),
                ("fp", "chrome"),
                ("type", server.network),
            ]
        )
        return f"{protocol}://{user_uuid}@{server.host}:{server.port}?{query}#{label}"
