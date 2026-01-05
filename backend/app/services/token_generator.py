"""Генерация безопасных токенов для подписок."""
import secrets


def generate_subscription_token(length: int = 32) -> str:
    """Создать URL-safe токен достаточной длины."""
    entropy_bytes = max(16, length)
    return secrets.token_urlsafe(entropy_bytes)
