"""Построение VLESS URI на лету."""
from urllib.parse import urlencode

from app.models.server import Server


class ConfigGenerator:
    """Генератор конфигураций без сохранения в базе."""

    def build_vless_uri(self, server: Server, user_uuid: str) -> str:
        """Собрать одну VLESS ссылку для конкретного сервера."""
        protocol = server.protocol or "vless"
        label = (server.country_code or server.host).upper()
        if server.protocol != "vless":
            raise ValueError("Поддерживается только VLESS")

        params = {
            "encryption": "none",
            "security": "reality",
            "fp": "chrome",
            "pbk": server.public_key,
            "type": server.network,
        }

        # Для Reality обязательны sni и short_id
        if not server.sni:
            raise ValueError("SNI обязателен для Reality")
        if not server.short_id:
            raise ValueError("shortId обязателен для Reality")

        params["sni"] = server.sni
        params["sid"] = server.short_id

        if server.network == "ws":
            params["host"] = server.sni or server.host
            params["path"] = "/"
        elif server.network == "xhttp":
            params["host"] = server.sni or server.host
            params["path"] = "/"

        query = urlencode(params)
        return f"{protocol}://{user_uuid}@{server.host}:{server.port}?{query}#{label}"
