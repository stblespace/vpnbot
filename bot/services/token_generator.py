"""Генерация безопасных токенов подписки."""
import secrets


def generate_token(length: int = 32) -> str:
    """URL-safe токен достаточной длины."""
    return secrets.token_urlsafe(length)
